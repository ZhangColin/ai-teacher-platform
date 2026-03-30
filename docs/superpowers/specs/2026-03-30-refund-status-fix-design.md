# 退款状态流转修复设计

**日期**: 2026-03-30
**问题**: 工行退款接口返回成功只表示请求已接收，需要调用查询接口确认最终状态

## 一、问题分析

### 当前实现的问题

`backend/src/services/refund_service.py` 第139-142行：

```python
if return_code == "0":
    # 退款成功（工行退款接口同步返回结果，返回成功即退款成功）
    refund.status = RefundStatus.refund_success  # ❌ 错误！
```

### 工行接口说明

根据工行支付文档：

| 接口 | 返回字段 | 含义 |
|------|----------|------|
| 退款接口 `/api/.../merrefund/V1` | `return_code="0"` | 工行**接收到了**退款请求 |
| 查询接口 `/api/.../refundqry/V1` | `pay_status="0"` | 退款**成功** |
| 查询接口 `/api/.../refundqry/V1` | `pay_status="1"` | 退款**失败** |
| 查询接口 `/api/.../refundqry/V1` | `pay_status="2"` | 退款**状态未知**（处理中） |

## 二、状态流转设计

### 状态流转图

```
创建退款
    ↓
refund_created (退款已创建)
    ↓
调用工行退款接口
    ↓
┌───────────────────────┴───────────────────────┐
│ return_code != "0"                           │ return_code = "0"
│                                               │
│ → refund_failed                              │ → 等待2秒
│   (原因: 发起失败)                             │    ↓
└───────────────────────────────────────────────┤ 调用查询接口
                                                 ↓
                                           pay_status
                                               ├── "0" → refund_success
                                               ├── "1" → refund_failed
                                               └── "2" → refund_processing
                                                         ↑
                                                         │ 用户点击"刷新"
                                                         └───────────────┘
```

### 状态说明

| 状态代码 | 状态名称 | 含义 | 触发条件 |
|----------|----------|------|----------|
| `refund_created` | 退款已创建 | 初始状态 | 创建退款记录时 |
| `refund_processing` | 退款处理中 | 等待工行处理 | 查询返回 `pay_status="2"` |
| `refund_success` | 退款成功 | 退款完成 | 查询返回 `pay_status="0"` |
| `refund_failed` | 退款失败 | 退款失败 | 发起失败 OR 查询返回 `pay_status="1"` |
| `refund_cancelled` | 退款取消 | 暂不使用 | - |

## 三、数据库修改

### 新增字段

在 `payment_refunds` 表新增 `icbc_query_response` 字段：

```sql
ALTER TABLE payment_refunds
ADD COLUMN icbc_query_response JSON COMMENT '工行退款查询接口响应';
```

### 字段用途

| 字段 | 用途 |
|------|------|
| `icbc_refund_response` | 保存退款接口（发起）的响应 |
| `icbc_query_response` | 保存查询接口（查询状态）的响应 |

## 四、代码修改

### 4.1 数据模型 (`db_models.py`)

```python
class PaymentRefundModel(Base):
    # ... 现有字段 ...

    icbc_refund_response = Column(JSON, nullable=True, comment='工行退款发起接口响应')
    icbc_query_response = Column(JSON, nullable=True, comment='工行退款查询接口响应')  # 新增
```

### 4.2 退款服务 (`refund_service.py`)

#### `create_refund` 方法修改

```python
async def create_refund(...) -> PaymentRefundModel:
    # 1. 创建退款记录 (refund_created)
    refund = PaymentRefundModel(status=RefundStatus.refund_created, ...)

    # 2. 调用工行退款接口
    icbc_response = await self.icbc_client.refund_order(...)
    refund.icbc_refund_response = icbc_response

    return_code = icbc_response.get("return_code")
    if return_code != "0":
        # 发起失败
        refund.status = RefundStatus.refund_failed
        refund.failed_at = datetime.now()
    else:
        # 发起成功，等待2秒后查询
        await asyncio.sleep(2)
        query_response = await self.icbc_client.query_refund(...)
        refund.icbc_query_response = query_response

        # 解析查询结果
        biz_content = query_response.get("response_biz_content", {})
        pay_status = biz_content.get("pay_status")

        if pay_status == "0":
            refund.status = RefundStatus.refund_success
            refund.success_at = datetime.now()
        elif pay_status == "1":
            refund.status = RefundStatus.refund_failed
            refund.failed_at = datetime.now()
        else:
            refund.status = RefundStatus.refund_processing

    self.db.commit()
    return refund
```

#### `query_refund_status` 方法修改

```python
async def query_refund_status(self, refund_id: str) -> PaymentRefundModel:
    refund = self.db.query(PaymentRefundModel).filter(...).first()

    # 调用工行查询接口
    icbc_response = await self.icbc_client.query_refund(...)
    refund.icbc_query_response = icbc_response  # 保存查询响应

    # 解析状态（逻辑与 create_refund 中相同）
    biz_content = icbc_response.get("response_biz_content", {})
    pay_status = biz_content.get("pay_status")

    if pay_status == "0":
        refund.status = RefundStatus.refund_success
        refund.success_at = datetime.now()
    elif pay_status == "1":
        refund.status = RefundStatus.refund_failed
        refund.failed_at = datetime.now()
    # pay_status == "2" 保持 processing 状态

    self.db.commit()
    return refund
```

### 4.3 API 路由

新增手动刷新接口：

```
POST /api/v1/admin/refunds/{id}/query
```

### 4.4 前端修改

`RefundManagement.vue`：

- 处理中状态的退款记录显示"刷新状态"按钮
- 点击按钮调用 `POST /api/v1/admin/refunds/{id}/query`
- 刷新成功后更新列表

## 五、工行接口响应示例

### 退款接口响应（发起）

```json
{
  "sign": "...",
  "response_biz_content": {
    "return_code": "0",
    "return_msg": "成功",
    "intrx_serial_no": "020004161912000762603300000046",
    "outtrx_serial_no": "REF20260330142822EA82DB71",
    ...
  }
}
```

### 查询接口响应

```json
{
  "response_biz_content": {
    "return_code": "0",
    "return_msg": "",
    "pay_status": "0",  // 0=成功, 1=失败, 2=未知
    "real_reject_amt": "100",
    ...
  }
}
```

## 六、验收标准

1. 发起退款后，如果工行接收成功，状态为 `refund_processing` 或最终状态
2. 发起退款后，如果工行接收失败，状态为 `refund_failed`
3. 查询接口响应正确保存到 `icbc_query_response` 字段
4. 前端"处理中"状态的退款有"刷新"按钮
5. 点击刷新后能正确更新退款状态
