# 支付退款功能设计

> **创建日期：** 2026-03-27
> **设计者：** Claude
> **状态：** 待审查

---

## 一、背景

当前系统已实现工行聚合支付功能，用户可以通过扫码完成充值。现需添加退款功能，允许管理员在管理后台对已支付订单发起退款。

**核心需求：**
1. 支持部分退款（如订单100元，可退款30元）
2. 支持多次退款（一个订单可发起多次退款，直到退完）
3. 仅管理员可操作，用户端不提供退款入口
4. 退款不处理积分回退

---

## 二、工行退款接口规范

### 2.1 线上退货接口

**接口地址：**
```
POST https://gw.open.icbc.com.cn/api/cardbusiness/aggregatepay/b2c/online/merrefund/V1
```

**通用请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| app_id | str | 是 | 应用编号 |
| msg_id | str | 是 | 消息通讯唯一编号，40位 |
| format | str | 否 | 固定json |
| charset | str | 否 | 固定UTF-8 |
| sign_type | str | 否 | RSA2 |
| sign | str | 是 | RSA2签名 |
| timestamp | str | 是 | yyyy-MM-dd HH:mm:ss |
| biz_content | str | 是 | 业务参数JSON |

**biz_content 业务参数：**

| 参数 | 类型 | 必填 | 说明 | 示例值 |
|-----|------|------|------|-------|
| mer_id | str | 是 | 商户编号 | 020004161912 |
| out_trade_no | str | 否 | 商户订单号（与order_id二选一） | 20260326xxxxx |
| order_id | str | 否 | 工行订单号（与out_trade_no二选一） | 020004161912xxxxx |
| outtrx_serial_no | str | 是 | 退货流水号，每次退款不同 | REF20260327xxxxx |
| ret_total_amt | str | 是 | 退款金额（分） | 100 |
| trnsc_ccy | str | 是 | 交易币种，001=人民币 | 001 |
| icbc_appid | str | 是 | 工行APPID | 11000000000000079872 |
| mer_prtcl_no | str | 否 | 协议编号 | 0200041619120201 |
| order_apd_inf | str | 否 | 订单附加信息 | |

**响应参数：**

| 参数 | 类型 | 说明 |
|-----|------|------|
| return_code | str | 返回码，0=成功 |
| return_msg | str | 返回说明 |
| outtrx_serial_no | str | 商户退款流水号 |
| intrx_serial_no | str | 工行退款流水号 |
| reject_amt | str | 退款总金额（分） |
| real_reject_amt | str | 实际退款金额（分） |
| refund_time | str | 退款时间 |
| pay_type | str | 支付方式 |

### 2.2 退款查询接口

**接口地址：**
```
POST https://gw.open.icbc.com.cn/api/cardbusiness/aggregatepay/b2c/online/refundqry/V1
```

**biz_content 业务参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| mer_id | str | 是 | 商户编号 |
| out_trade_no | str | 否 | 商户消费订单号（与order_id二选一） |
| order_id | str | 否 | 工行消费订单号（与out_trade_no二选一） |
| outtrx_serial_no | str | 是 | 商户退款流水号 |
| mer_prtcl_no | str | 否 | 协议编号 |

**响应参数：**

| 参数 | 类型 | 说明 |
|-----|------|------|
| return_code | str | 返回码，0=成功 |
| pay_status | str | 0=成功，1=失败，2=未知 |
| outtrx_serial_no | str | 商户退款流水号 |
| intrx_serial_no | str | 工行退款流水号 |
| reject_amt | str | 退款总金额（分） |
| real_reject_amt | str | 实际退款金额（分） |
| refund_time | str | 退款时间 |

---

## 三、数据库模型设计

### 3.1 退款订单模型

**文件：** `backend/src/db_models.py`

```python
class RefundStatus(str, Enum):
    """退款状态枚举"""
    refund_created = "refund_created"      # 退款已创建
    refund_processing = "refund_processing" # 退款处理中
    refund_success = "refund_success"       # 退款成功
    refund_failed = "refund_failed"         # 退款失败
    refund_cancelled = "refund_cancelled"   # 退款取消


class PaymentRefundModel(Base):
    """退款订单数据库模型"""
    __tablename__ = "payment_refunds"

    # 基础字段
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    out_refund_no = Column(String(64), unique=True, nullable=False, index=True, comment='商户退款流水号')
    payment_order_id = Column(CHAR(36), ForeignKey("payment_orders.id"), nullable=False, index=True, comment='关联支付订单ID')

    # 金额
    refund_amount = Column(Integer, nullable=False, comment='退款金额（分）')
    real_refund_amount = Column(Integer, nullable=True, comment='实际退款金额（分）')

    # 状态
    status = Column(Enum(RefundStatus), nullable=False, default=RefundStatus.refund_created, index=True)

    # 工行返回数据
    third_refund_no = Column(String(64), nullable=True, comment='工行退款流水号')
    icbc_refund_response = Column(JSON, nullable=True, comment='工行退款完整响应')

    # 操作信息
    operator_id = Column(CHAR(36), nullable=False, comment='操作人ID')
    operator_name = Column(String(50), nullable=True, comment='操作人姓名')
    refund_reason = Column(String(200), nullable=True, comment='退款原因')

    # 时间记录
    submitted_at = Column(DateTime, nullable=True, comment='发起退款时间')
    success_at = Column(DateTime, nullable=True, comment='退款成功时间')
    failed_at = Column(DateTime, nullable=True, comment='退款失败时间')

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 联合索引
    __table_args__ = (
        Index("idx_refund_payment", "payment_order_id"),
        Index("idx_refund_status", "status"),
        Index("idx_refund_created", "created_at"),
    )
```

### 3.2 支付订单模型扩展

在 `PaymentOrderModel` 中添加退款统计字段：

```python
# 在 PaymentOrderModel 类中添加
refunded_amount = Column(Integer, nullable=False, default=0, comment='已退款金额（分）')
refund_count = Column(Integer, nullable=False, default=0, comment='退款次数')
```

### 3.3 迁移计划

创建 Alembic 迁移脚本：
1. 添加 `payment_refunds` 表
2. 在 `payment_orders` 表中添加 `refunded_amount` 和 `refund_count` 字段

---

## 四、后端服务设计

### 4.1 工行客户端扩展

**文件：** `backend/src/services/icbc_qrcode_client.py`

新增方法：

```python
class IcbcQrCodeClient:
    # ... 现有代码 ...

    # 新增API端点
    API_REFUND_ORDER = "https://gw.open.icbc.com.cn/api/cardbusiness/aggregatepay/b2c/online/merrefund/V1"
    API_QUERY_REFUND = "https://gw.open.icbc.com.cn/api/cardbusiness/aggregatepay/b2c/online/refundqry/V1"

    async def refund_order(
        self,
        out_trade_no: str,
        out_refund_no: str,
        refund_amount: int,
        order_id: str = None,
    ) -> dict:
        """
        发起退款

        Args:
            out_trade_no: 商户订单号
            out_refund_no: 商户退款流水号
            refund_amount: 退款金额（分）
            order_id: 工行订单号（可选）

        Returns:
            工行响应结果
        """

    async def query_refund(
        self,
        out_trade_no: str,
        out_refund_no: str,
        order_id: str = None,
    ) -> dict:
        """
        查询退款状态

        Args:
            out_trade_no: 商户订单号
            out_refund_no: 商户退款流水号
            order_id: 工行订单号（可选）

        Returns:
            工行响应结果
        """
```

### 4.2 退款服务

**文件：** `backend/src/services/refund_service.py`（新建）

```python
class RefundService:
    """退款服务"""

    def __init__(self, db: Session, icbc_client: IcbcQrCodeClient):
        self.db = db
        self.icbc_client = icbc_client

    async def create_refund(
        self,
        payment_order_id: str,
        refund_amount: int,
        operator_id: str,
        operator_name: str = "",
        refund_reason: str = "",
    ) -> PaymentRefundModel:
        """
        创建退款订单

        业务规则：
        1. 支付订单状态必须为已支付
        2. 退款金额不能超过可退金额（订单金额 - 已退款金额）
        3. 生成唯一退款流水号
        4. 调用工行退款接口
        """

    async def query_refund_status(self, refund_id: str) -> dict:
        """
        查询退款状态

        调用工行查询接口，更新本地退款状态
        """

    def _can_refund(self, payment_order: PaymentOrderModel, refund_amount: int) -> bool:
        """检查是否可以退款"""

    def _generate_refund_no(self) -> str:
        """生成退款流水号"""
```

### 4.3 管理员API路由

**文件：** `backend/src/interfaces/routers/admin/payment_admin.py`

新增接口：

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/admin/payment/refunds` | 获取退款订单列表 |
| GET | `/admin/payment/refunds/{id}` | 获取退款订单详情 |
| POST | `/admin/payment/refunds/create` | 发起退款 |
| POST | `/admin/payment/refunds/{id}/query` | 查询退款状态 |
| GET | `/admin/payment/orders/{id}/refunds` | 获取支付订单的退款记录 |

**请求/响应模型：**

```python
# models.py
class CreateRefundRequest(BaseModel):
    """创建退款请求"""
    payment_order_id: str
    refund_amount: int  # 单位：分
    refund_reason: str = ""


class RefundResponse(BaseModel):
    """退款订单响应"""
    id: str
    out_refund_no: str
    payment_order_id: str
    refund_amount: int
    real_refund_amount: int | None
    status: str
    third_refund_no: str | None
    operator_id: str
    operator_name: str | None
    refund_reason: str | None
    submitted_at: str | None
    success_at: str | None
    failed_at: str | None
    created_at: str
```

---

## 五、前端页面设计

### 5.1 退款管理页面

**文件：** `frontend/src/views/admin/RefundManagement.vue`（新建）

功能：
1. 退款订单列表展示
2. 筛选：状态、商户订单号、退款流水号
3. 发起退款对话框
4. 退款详情对话框
5. 查询退款状态按钮

**页面结构：**
```
┌─────────────────────────────────────────────────────┐
│  退款管理                                             │
├─────────────────────────────────────────────────────┤
│  [筛选] 状态[▼] 订单号[____] 退款流水号[____] [查询] │
├─────────────────────────────────────────────────────┤
│  退款流水号  | 商户订单号 | 退款金额 | 状态 | 操作    │
│  REF2026... | ORD2026... | ¥10.00  | 成功 | 详情    │
│  REF2026... | ORD2026... | ¥50.00  | 处理中| 详情|查询│
└─────────────────────────────────────────────────────┘
```

### 5.2 支付订单页面增强

**文件：** `frontend/src/views/admin/PaymentOrdersView.vue`（修改）

新增内容：
1. "已退款金额"列
2. "退款次数"列
3. 操作列新增"发起退款"按钮（已支付订单）
4. 操作列新增"查看退款"按钮

### 5.3 路由配置

**文件：** `frontend/src/router/index.ts`

```typescript
{
  path: '/admin',
  component: AdminLayout,
  children: [
    // ... 现有路由 ...
    {
      path: 'refunds',
      name: 'AdminRefunds',
      component: () => import('@/views/admin/RefundManagement.vue'),
      meta: { requiresAuth: true, requiresAdmin: true, title: '退款管理' }
    }
  ]
}
```

### 5.4 导航菜单

在管理后台侧边栏添加"退款管理"菜单项。

---

## 六、业务流程

### 6.1 发起退款流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  管理员     │───>│  后端API    │───>│   工行      │
│  选择订单   │    │  创建退款   │    │   退款接口  │
└─────────────┘    └─────────────┘    └─────────────┘
                         │
                         v
                  ┌─────────────┐
                  │  数据库     │
                  │  退款订单   │
                  └─────────────┘

步骤：
1. 管理员选择已支付订单，点击"发起退款"
2. 系统检查：
   - 订单状态为 paid
   - 退款金额 <= (订单金额 - 已退款金额)
3. 创建退款订单（状态：refund_created）
4. 调用工行退款接口
5. 根据工行响应更新状态：
   - return_code=0 → refund_processing（等待回调或查询确认）
   - 其他错误码 → refund_failed
6. 更新支付订单的 refunded_amount 和 refund_count
```

### 6.2 退款查询流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  管理员     │───>│  后端API    │───>│   工行      │
│  点击查询   │    │  查询退款   │    │  查询接口   │
└─────────────┘    └─────────────┘    └─────────────┘
                         │
                         v
                  ┌─────────────┐
                  │  更新退款   │
                  │  订单状态   │
                  └─────────────┘

工行 pay_status 映射：
- 0 → refund_success
- 1 → refund_failed
- 2 → refund_processing（继续查询）
```

### 6.3 状态流转图

```
          创建退款
             │
             v
    refund_created
             │
      调用工行接口
             │
    ┌────────┴────────┐
    │                 │
 成功提交          提交失败
    │                 │
    v                 v
refund_processing  refund_failed
    │
 查询/回调确认
    │
    v
refund_success
```

---

## 七、文件修改清单

### 7.1 后端文件

| 文件 | 操作 | 说明 |
|-----|------|------|
| `db_models.py` | 修改 | 添加 RefundStatus 枚举、PaymentRefundModel |
| `db_models.py` | 修改 | PaymentOrderModel 添加退款统计字段 |
| `alembic/versions/xxx.py` | 新增 | 数据库迁移脚本 |
| `services/icbc_qrcode_client.py` | 修改 | 添加 refund_order、query_refund 方法 |
| `services/refund_service.py` | 新增 | 退款服务 |
| `interfaces/routers/admin/payment_admin.py` | 修改 | 添加退款相关API |
| `models.py` | 修改 | 添加退款相关Pydantic模型 |

### 7.2 前端文件

| 文件 | 操作 | 说明 |
|-----|------|------|
| `views/admin/RefundManagement.vue` | 新增 | 退款管理页面 |
| `views/admin/PaymentOrdersView.vue` | 修改 | 添加退款相关按钮和列 |
| `router/index.ts` | 修改 | 添加退款管理路由 |
| `types/index.ts` | 修改 | 添加退款相关类型定义 |

---

## 八、测试计划

### 8.1 单元测试

- `test_refund_service.py` - 测试退款服务逻辑
- `test_icbc_refund.py` - 测试工行退款接口

### 8.2 集成测试

- 测试完整退款流程
- 测试部分退款
- 测试多次退款
- 测试退款查询

### 8.3 测试步骤

1. 创建支付订单并完成支付
2. 发起部分退款（如订单100元，退款30元）
3. 验证退款订单创建成功
4. 验证支付订单 refunded_amount = 30, refund_count = 1
5. 发起第二次退款（退款50元）
6. 验证 refunded_amount = 80, refund_count = 2
7. 尝试退款超过可退金额，验证失败
8. 查询退款状态，验证状态更新

---

## 九、工行状态映射表

### 9.1 退款接口返回码

| 返回码 | 说明 | 本系统状态 |
|-------|------|-----------|
| 0 | 成功 | refund_processing / refund_success |
| 400011 | 参数非法 | refund_failed |
| 400017 | 签名验证失败 | refund_failed |
| 00005031 | 已下单，不允许再次下单 | refund_failed |
| 其他 | 其他错误 | refund_failed |

### 9.2 退款查询状态

| pay_status | 说明 | 本系统状态 |
|-----------|------|-----------|
| 0 | 退款成功 | refund_success |
| 1 | 退款失败 | refund_failed |
| 2 | 退款状态未知 | refund_processing |

---

## 十、附录

### 10.1 退款流水号生成规则

格式：`REF + yyyyMMddHHmmss + 8位随机数`

示例：`REF20260327143045A3F12B9C`

### 10.2 退款金额限制

- 单笔退款金额：>= 1分
- 累计退款金额：<= 原订单金额
- 退款次数：无限制（直到退完）

### 10.3 操作记录

所有退款操作需记录：
- 操作人ID和姓名
- 操作时间
- 退款原因
- 工行响应完整数据
