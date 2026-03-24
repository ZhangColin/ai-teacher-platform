# 支付功能设计文档

**日期**: 2025-03-24
**作者**: Claude
**状态**: 设计中

## 1. 概述

为 AI 智能备课平台集成工商银行聚合支付，实现用户充值购买积分功能。

### 1.1 目标

- 用户通过浏览器扫描二维码完成支付充值
- 支付成功后自动增加企业积分余额
- 管理员可查看所有支付订单和配置系统参数

### 1.2 约束

- 工行无测试环境，直接在生产地址测试
- 需要提供测试接口模拟工行回调
- 设计需考虑未来扩展性（其他支付场景）

## 2. 数据模型

### 2.1 payment_orders（支付订单表）

每次向工行请求支付创建一条记录，记录完整的支付交互过程。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | CHAR(36) | 主键 |
| user_id | CHAR(36) | 用户ID（外键）|
| out_trade_no | String(64) | 商户订单号（唯一索引）|
| third_trade_no | String(64) | 工行流水号 |
| amount | Integer | 金额（分）|
| status | Enum | 订单状态（索引）|
| pay_channel | String(20) | 支付渠道（默认 icbc_aggregate）|
| business_type | String(20) | 业务类型（默认 recharge）|
| business_id | String(36) | 业务ID（预留，当前为空）|
| pay_url | String(512) | 支付URL |
| qr_code_data | String(512) | 二维码数据 |
| icbc_response | JSON | 工行下单响应 |
| submitted_at | DateTime | 发起时间（提交工行）|
| paid_at | DateTime | 支付时间 |
| expire_at | DateTime | 超时时间（15分钟）|
| notified_at | DateTime | 回调到达时间 |
| notify_data | JSON | 回调原始数据 |
| notify_verify_result | Boolean | 回调验签结果 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**状态枚举**：
- `created` - 已创建
- `processing` - 支付中（已提交工行）
- `paid` - 已支付
- `failed` - 支付失败
- `cancelled` - 已取消
- `timeout` - 已超时

**索引**：
- `idx_payment_user_status`: (user_id, status)
- `idx_payment_created`: created_at
- `uk_out_trade_no`: out_trade_no (唯一)

### 2.2 system_configs（系统配置表）

存储系统级配置，如积分兑换比例。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键（自增）|
| key | String(50) | 配置键（唯一索引）|
| value | String(500) | 配置值 |
| description | String(200) | 配置描述 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**预置配置**：
- `points_per_yuan`: 1元对应的积分数量（默认100）

### 2.3 point_transactions（积分交易表）- 修改

**说明**：该表已存在于系统中，用于记录积分交易历史。本次修改新增两个字段：

新增字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| payment_id | CHAR(36) | 关联的支付订单ID（可为空，仅充值类型有值）|
| amount | Integer | 充值金额（分）（可为空，仅充值类型有值）|

## 3. API 接口

### 3.1 用户端接口

#### 创建支付订单

```
POST /api/v1/payment/create-order
```

**请求**：
```json
{
  "amount": 10000  // 金额，单位：分（100元）
}
```

**金额限制**：
- 最小金额：100分（1元）
- 最大金额：500000分（5000元）
- 金额必须为整数（分）

**错误响应**：
```json
{
  "error": "INVALID_AMOUNT",
  "message": "金额必须在100-500000分之间"
}
```

**响应**：
```json
{
  "id": "订单ID",
  "out_trade_no": "PO20250324001",
  "amount": 10000,
  "status": "processing",
  "qr_code_data": "https://...",
  "expire_at": "2025-03-24T15:30:00"
}
```

#### 查询订单状态

```
GET /api/v1/payment/order/{id}
```

**响应**：
```json
{
  "id": "订单ID",
  "status": "paid",
  "amount": 10000,
  "paid_at": "2025-03-24T15:25:00"
}
```

#### 我的充值记录

```
GET /api/v1/payment/my-recharges?page=1&page_size=20
```

**响应**：
```json
{
  "items": [
    {
      "id": "交易ID",
      "amount": 10000,
      "points": 1000,
      "created_at": "2025-03-24T15:25:00"
    }
  ],
  "total": 10
}
```

### 3.2 工行回调接口

#### 支付回调

```
POST /api/v1/payment/icbc/notify
```

工行异步通知支付结果，需要验签后处理。

### 3.3 管理员接口

#### 支付订单列表

```
GET /api/v1/admin/payment/orders?page=1&page_size=20&status=paid
```

#### 积分兑换比例配置

```
GET /api/v1/admin/payment/config
POST /api/v1/admin/payment/config
```

#### 测试回调

```
POST /api/v1/admin/payment/test-notify
```

模拟工行回调，用于测试。

## 4. 服务层设计

### 4.1 IcbcClient（工行客户端）

```python
class IcbcClient:
    """工行聚合支付客户端"""

    def __init__(
        self,
        app_id: str,
        mer_id: str,
        mer_prtcl_no: str,
        private_key: str,
        public_key: str,
        device_info: str,
        notify_url: str
    ):
        """初始化工行客户端"""

    async def create_order(
        self,
        out_trade_no: str,
        amount: int,
        expire_time: int = 900
    ) -> dict:
        """
        调用工行统一下单接口

        Args:
            out_trade_no: 商户订单号
            amount: 金额（分）
            expire_time: 超时时间（秒），默认900秒（15分钟）

        Returns:
            工行响应，包含 pay_url 等字段
        """

    async def query_order(
        self,
        out_trade_no: str
    ) -> dict:
        """调用工行订单查询接口"""

    def _sign(
        self,
        data: dict,
        sign_type: str = "RSA2",
        charset: str = "UTF-8"
    ) -> str:
        """
        RSA2 签名

        工行签名规则：
        1. 参数按字典序排序
        2. 拼接成 key1=value1&key2=value2 格式
        3. 使用商户私钥签名
        """

    def _verify(
        self,
        data: dict,
        sign: str,
        sign_type: str = "RSA",
        charset: str = "UTF-8"
    ) -> bool:
        """
        RSA 验签

        使用工行公钥验证签名
        """
```

### 4.2 PaymentService（支付服务）

```python
class PaymentService:
    """支付服务"""

    async def create_payment_order(
        self,
        user_id: str,
        amount: int
    ) -> PaymentOrderModel:
        """创建支付订单"""

    async def query_payment_status(
        self,
        order_id: str
    ) -> dict:
        """查询支付状态（前端轮询用）"""

    async def handle_notify(
        self,
        notify_data: dict
    ) -> bool:
        """处理工行回调"""

    async def mark_order_timeout(
        self,
        order_id: str
    ):
        """标记订单超时"""
```

### 4.3 复用现有服务

- `PointService.add_points()` - 支付成功后添加积分
- `EnterpriseService` - 获取用户企业信息

## 5. 支付流程

### 5.1 正常支付流程

```
用户发起充值（输入金额）
    ↓
创建 PaymentOrder(status=created)
    ↓
调用 IcbcClient.create_order()
    ↓
更新 PaymentOrder(status=processing, 保存工行响应)
    ↓
前端展示二维码（轮询查询状态）
    ↓
用户扫码支付
    ↓
工行回调 /icbc/notify
    ↓
PaymentService.handle_notify()
    ├─ 验签
    │   ├─ 成功 → 继续
    │   └─ 失败 → 记录日志，返回错误给工行（return_code=-1）
    ├─ 检查 return_code
    │   ├─ 0（成功）→ 继续
    │   └─ 其他 → 标记为 failed
    ├─ 更新 status=paid
    ├─ 调用 PointService.add_points()
    ├─ 创建 PointTransaction
    └─ 更新 PaymentOrder 关联信息
```

### 5.2 回调验签失败处理

验签失败时：
1. 记录错误日志（包含回调原始数据）
2. 返回工行错误响应：`{"return_code": -1, "return_msg": "签名验证失败"}`
3. 不处理业务逻辑，不更新订单状态

### 5.3 订单状态流转

```
created（已创建）
    ↓ 提交工行成功
processing（支付中）
    ↓
├─ 支付成功 → paid（已支付）
├─ 超时（15分钟）→ timeout（已超时）
├─ 支付失败 → failed（支付失败）
└─ 用户取消 → cancelled（已取消）
```

## 6. 配置

### 6.1 环境变量（.env）

工行无独立测试环境，开发时直接使用生产地址。通过控制测试金额（如0.01元）来降低风险。

```bash
# 工行聚合支付配置（生产环境）
ICBC_APP_ID=xxx                      # 应用编号
ICBC_MER_ID=xxx                      # 商户编号
ICBC_MER_PRTCL_NO=xxx                # 协议编号
ICBC_MY_PRIVATE_KEY=xxx              # 商户私钥（RSA2）
ICBC_APIGW_PUBLIC_KEY=xxx            # 工行公钥（RSA）
ICBC_DEVICE_INFO=xxx                 # 设备号（自定义）
ICBC_NOTIFY_URL=https://your-domain.com/api/v1/payment/icbc/notify  # 回调地址
ICBC_API_URL=https://gw.open.icbc.com.cn  # 工行API地址
```

### 6.2 系统配置（数据库）

| key | value | 说明 |
|-----|-------|------|
| points_per_yuan | 100 | 1元=100积分 |

## 7. 测试

### 7.1 测试回调接口

```
POST /api/v1/admin/payment/test-notify
```

**请求**：
```json
{
  "out_trade_no": "PO20250324001",
  "return_code": "0",
  "third_trade_no": "ICBC123456",
  "total_amt": "10000"
}
```

### 7.2 测试页面

路径：`/admin/payment/test`

功能：输入订单号，选择测试场景，点击按钮发起测试回调。

### 7.3 定时任务

每分钟检查一次超时订单，标记为 timeout 状态。

## 8. 前端集成

### 8.1 充值页面

- 常用金额选项
- 自定义金额输入
- 二维码展示（使用 qrcode.js）
- 轮询订单状态（每3秒）

**轮询策略**：
- 间隔：3秒
- 最大轮询次数：300次（15分钟）
- 超时后停止轮询，显示"订单超时"提示
- 支付成功后停止轮询，显示成功页面

### 8.2 状态展示

| 状态 | 展示 |
|------|------|
| processing | 二维码 + "等待支付" |
| paid | "支付成功" |
| timeout | "订单超时，请重新支付" |
| failed | "支付失败，请重试" |

## 9. 扩展性设计

未来支持其他支付场景时：

1. 新增业务表（如 `course_purchases`）关联 `payment_orders`
2. 在 `PaymentOrder` 表增加 `business_type` 和 `business_id` 字段
3. 支付成功后根据业务类型调用不同的处理逻辑

当前实现只支持充值场景，`business_type` 默认为 `recharge`。
