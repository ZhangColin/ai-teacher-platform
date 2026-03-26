# 工行二维码支付对接设计

**日期**: 2026-03-26
**作者**: Claude
**状态**: 设计完成，待审查

---

## 1. 概述

### 1.1 目标
将工行二维码支付接口完整对接到 AI 智能备课平台，替换现有的模拟支付代码。

### 1.2 支付场景
- 用户扫二维码支付（生成固定金额的支付二维码）
- 支付结果通知：异步回调 + 轮询查询（双保险）
- 测试金额：固定 1 分钱

### 1.3 环境
- 直接接入生产环境
- 本地测试：仅轮询查询
- 生产部署：启用异步回调

---

## 2. 配置参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `app_id` | `11000000000000079872` | 应用编号 |
| `mer_id` | `020004161912` | 商户编号（12位） |
| `private_key_path` | `backend/src/key/AI_客户用.pri` | 客户私钥 |
| `public_key_path` | `backend/src/key/AI_银行用.pub` | 银行公钥 |
| `notify_url` | 环境变量 | 支付结果回调地址（可选） |

---

## 3. 文件变更

### 3.1 新建文件

| 文件 | 说明 |
|------|------|
| `backend/src/services/icbc_qrcode_client.py` | 工行二维码支付客户端 |
| `backend/src/config/icbc_config.py` | 工行配置管理 |

### 3.2 修改文件

| 文件 | 修改内容 |
|------|----------|
| `backend/src/services/payment_service.py` | 移除模拟代码，使用新客户端 |
| `backend/src/interfaces/routers/payment.py` | 更新导入和依赖 |

### 3.3 删除文件

| 文件 | 原因 |
|------|------|
| `backend/src/services/icbc_client.py` | 旧的工行客户端，替换为新实现 |

---

## 4. 核心组件设计

### 4.1 IcbcQrCodeClient

**职责**：封装工行二维码支付 API 调用

**方法**：
- `generate_qrcode()` - 调用工行二维码生成接口
- `query_order()` - 调用工行订单查询接口
- `verify_notify()` - 验证工行回调签名
- `_sign()` - RSA2 签名
- `_verify()` - RSA2 验签
- `_build_sign_str()` - 构建签名字符串

**API 端点**：
- 二维码生成：`https://gw.open.icbc.com.cn/api/qrcode/V2/generate`
- 订单查询：`https://gw.open.icbc.com.cn/api/qrcode/query/V5`

### 4.2 PaymentService 修改

**主要修改**：
1. 移除模拟代码（第 113-130 行）
2. 启用真实 API 调用
3. 调整订单创建逻辑，适配工行接口参数

**保持不变**：
- 数据库模型 `PaymentOrderModel`
- 积分计算逻辑
- 回调处理逻辑

### 4.3 配置管理

**`icbc_config.py`** 提供配置加载和密钥文件读取：

```python
ICBC_PAYMENT_CONFIG = {
    "app_id": "...",
    "mer_id": "...",
    "private_key_path": "...",
    "public_key_path": "...",
    "notify_url": "...",
}
```

---

## 5. 数据流

```
用户发起充值
  → 创建支付订单 (PaymentOrderModel, status=created)
  → 调用工行二维码生成接口
  → 更新订单 (status=processing, qr_code_data=...)
  → 返回二维码数据给前端
  → 前端显示二维码，用户扫码支付
  → 前端轮询查询订单状态
  → [可选] 工行异步回调通知
  → 支付成功后更新订单 (status=paid)
  → 增加企业积分
```

---

## 6. 数据库

**复用现有表结构**：`PaymentOrderModel`

无需修改，现有字段完全满足工行二维码支付需求。

---

## 7. 错误处理

| 工行响应码 | 说明 |
|-----------|------|
| `0` | 成功 |
| 其他 | 失败，记录 `return_msg` |

所有异常都会记录到日志，订单状态标记为 `failed`。

---

## 8. 测试策略

1. **单元测试**：签名验签逻辑
2. **集成测试**：真实调用工行接口（1分钱）
3. **回调测试**：模拟工行回调通知

---

## 9. 部署配置

**环境变量** (`.env`):

```bash
ICBC_APP_ID=11000000000000079872
ICBC_MER_ID=020004161912
ICBC_NOTIFY_URL=https://your-domain.com/api/v1/payment/icbc/notify
```

本地测试时 `ICBC_NOTIFY_URL` 可留空。

---

## 10. 安全考虑

1. 私钥文件不提交到版本控制
2. 回调验签必须通过
3. 订单金额固定 1 分钱（测试阶段）
4. 所有敏感操作记录日志

---

## 11. 参考资料

- 工行开放平台 SDK 介绍
- 获取订单二维码接口文档
- 线上消费查询接口文档
