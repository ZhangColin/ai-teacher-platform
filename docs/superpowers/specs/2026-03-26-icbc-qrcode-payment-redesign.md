# 工行二维码支付对接重新设计

> **创建日期：** 2026-03-26
> **设计者：** Claude
> **状态：** 待审查

---

## 一、背景

当前 `IcbcQrCodeClient` 的实现与工行官方文档存在严重不一致，导致下单失败。需要删除原有实现，严格按照工行文档重新实现。

**核心问题：**
1. API 端点错误
2. 请求参数命名错误（camelCase vs snake_case）
3. 缺少多个必填参数
4. 响应字段解析错误

---

## 二、工行接口规范（依据官方文档）

### 2.1 生成支付二维码

**接口地址：**
```
POST https://gw.open.icbc.com.cn/api/cardbusiness/qrcode/consumption/V1
```

**通用请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| app_id | str | 是 | 应用编号 |
| msg_id | str | 是 | 消息通讯唯一编号，40位，APP级唯一 |
| format | str | 否 | 固定json |
| charset | str | 否 | 固定UTF-8 |
| sign_type | str | 否 | RSA2 |
| sign | str | 是 | RSA2签名 |
| timestamp | str | 是 | yyyy-MM-dd HH:mm:ss |
| biz_content | str | 是 | 业务参数JSON |

**biz_content 业务参数：**

| 参数 | 类型 | 必填 | 说明 | 示例值 |
|-----|------|------|------|-------|
| out_trade_no | str | 是 | 商户订单号 | 20260326204438abcd1234 |
| mer_id | str | 是 | 商户编号 | 020004161912 |
| mer_prtcl_no | str | 是 | 协议编号 = mer_id + "0201" | 0200041619120201 |
| access_type | str | 是 | 接入方式，6=PC | 6 |
| cur_type | str | 是 | 币种，001=人民币 | 001 |
| amount | str | 是 | 金额（分） | 1 |
| icbc_appid | str | 是 | 工行APPID | 11000000000000079872 |
| mer_url | str | 否 | 回调地址（AG模式可为空） | |
| expire_time | str | 否 | 订单有效期（秒） | 900 |
| notify_type | str | 是 | 通知类型，AG=不通知 | AG |
| result_type | str | 是 | 结果类型，0=成功失败都通知 | 0 |
| attach | str | 否 | 附加数据，原样返回 | test123 |
| order_date | str | 是 | 交易日期 | 2026-03-26 20:44:38 |
| goods_name | str | 是 | 商品名称（最多20汉字） | 智研云平台充值 |
| body | str | 是 | 商品描述（最多128字符） | 智研云平台充值 |

**响应参数：**

| 参数 | 类型 | 说明 |
|-----|------|------|
| return_code | str | 返回码，0=成功 |
| return_msg | str | 返回说明 |
| returnCode | str | 接口码 |
| codeUrl | str | 二维码串 |
| supportAppType | str | 支持的支付方式位图 |

### 2.2 查询订单状态

**接口地址：**
```
POST https://gw.open.icbc.com.cn/api/cardbusiness/aggregatepay/b2c/online/orderqry/V1
```

**biz_content 业务参数：**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| mer_id | str | 是 | 商户编号 |
| out_trade_no | str | 否 | 商户订单号 |
| order_id | str | 否 | 工行订单号 |
| deal_flag | str | 是 | 操作标志，0=查询，1=关单 |
| icbc_appid | str | 是 | 工行APPID |
| mer_prtcl_no | str | 是 | 协议编号 |

**响应参数：**

| 参数 | 类型 | 说明 |
|-----|------|------|
| return_code | str | 返回码，0=成功 |
| pay_status | str | 0=成功，1=失败，2=未知 |
| order_id | str | 工行订单号 |
| pay_time | str | 支付时间，yyyyMMddHHmmss |

### 2.3 支付回调

**回调地址：** `POST /api/v1/payment/icbc/notify`

**回调参数格式：** URL参数编码

**关键字段：**
- `from`: icbc-api
- `api`: /api/cardbusiness/aggregatepay/b2c/online/consumepurchase/V1
- `biz_content`: JSON字符串，包含订单状态
- `sign`: 签名

---

## 三、数据库模型修改

### 3.1 PaymentOrderModel 新增字段

```python
class PaymentOrderModel(Base):
    # ... 现有字段 ...

    # 新增字段
    goods_name = Column(String(40), nullable=True, comment='商品名称')
    attach = Column(String(127), nullable=True, comment='附加数据，原样返回')
    support_app_type = Column(String(10), nullable=True, comment='支持的支付方式位图')
    msg_id = Column(String(40), nullable=True, comment='消息通讯唯一编号')
```

### 3.2 迁移计划

创建 Alembic 迁移脚本添加上述4个字段。

---

## 四、配置设计

### 4.1 配置文件结构

**文件：** `backend/src/config/icbc_config.py`

```python
ICBC_PAYMENT_CONFIG = {
    # 基础配置
    "app_id": "11000000000000079872",
    "mer_id": "020004161912",
    "mer_prtcl_no": "0200041619120201",  # 自动计算

    # 交易配置
    "access_type": "6",          # PC支付
    "cur_type": "001",           # 人民币
    "goods_name": "智研云平台充值",
    "body": "智研云平台充值",

    # 通知配置
    "notify_type": "AG",         # 开发环境：主动查询
    "result_type": "0",          # 生产环境：成功失败都通知
    "notify_url": "",            # 生产环境配置

    # 密钥文件路径
    "private_key_path": KEY_DIR / "AI_客户用.pri",
    "public_key_path": KEY_DIR / "AI_银行用.pub",
}
```

### 4.2 密钥格式处理

工行提供的密钥是**裸Base64格式**，需要转换为PEM格式：

```python
def load_key_content(file_path: str) -> str:
    """将裸Base64密钥转换为PEM格式"""
    with open(file_path, "r") as f:
        content = f.read().strip()

    # 裸Base64需要添加PEM头尾和换行
    if not content.startswith("-----BEGIN"):
        wrapped = "\n".join(textwrap.wrap(content, 64))
        if "PRIVATE" in file_path.upper() or ".pri" in file_path.lower():
            return f"-----BEGIN PRIVATE KEY-----\n{wrapped}\n-----END PRIVATE KEY-----"
        else:
            return f"-----BEGIN PUBLIC KEY-----\n{wrapped}\n-----END PUBLIC KEY-----"
    return content
```

---

## 五、IcbcQrCodeClient 重写

### 5.1 类结构

```python
class IcbcQrCodeClient:
    """工行二维码支付客户端"""

    # API 端点
    API_GENERATE_QRCODE = "https://gw.open.icbc.com.cn/api/cardbusiness/qrcode/consumption/V1"
    API_QUERY_ORDER = "https://gw.open.icbc.com.cn/api/cardbusiness/aggregatepay/b2c/online/orderqry/V1"

    def __init__(self, config: dict):
        self.app_id = config["app_id"]
        self.mer_id = config["mer_id"]
        self.mer_prtcl_no = config["mer_prtcl_no"]
        # ... 加载密钥

    async def generate_qrcode(...) -> dict:
        """生成支付二维码"""

    async def query_order(...) -> dict:
        """查询订单状态"""

    def verify_notify(self, notify_data: dict) -> bool:
        """验证回调签名"""
```

### 5.2 签名与验签

**签名规则：**
1. 参数按字典序排序
2. 拼接成 `key1=value1&key2=value2` 格式
3. 排除 sign 字段和空值
4. 使用 RSA2 (SHA256WithRSA) 签名
5. Base64 编码

---

## 六、回调接口设计

### 6.1 路由定义

**文件：** `backend/src/interfaces/routers/payment.py`

```python
@router.post("/icbc/notify")
async def icbc_notify(request: Request, db: Session = Depends(get_db)):
    """工行支付回调"""
    # 1. 获取请求参数
    # 2. 验证签名
    # 3. 解析 biz_content
    # 4. 更新订单状态
    # 5. 返回指定格式响应
```

### 6.2 回调响应格式

工行要求严格的响应格式：

```json
{
    "response_biz_content": {
        "return_code": 0,
        "return_msg": "success",
        "msg_id": "回调中的msg_id"
    },
    "sign_type": "RSA2",
    "sign": "商户签名"
}
```

---

## 七、文件修改清单

| 文件 | 操作 | 说明 |
|-----|------|------|
| `db_models.py` | 修改 | PaymentOrderModel 添加4个字段 |
| `alembic/versions/xxx.py` | 新增 | 数据库迁移脚本 |
| `config/icbc_config.py` | 重写 | 更新配置结构 |
| `services/icbc_qrcode_client.py` | 重写 | 两个API方法完全重写 |
| `services/payment_service.py` | 修改 | 响应字段名调整（qrcode→codeUrl） |
| `interfaces/routers/payment.py` | 新增 | 添加回调路由 |

---

## 八、测试计划

### 8.1 单元测试

- `test_icbc_qrcode_client.py` - 测试签名、请求构造
- `test_icbc_config.py` - 测试密钥加载

### 8.2 集成测试

- 测试创建订单流程
- 测试查询订单流程
- 测试回调处理流程

### 8.3 测试步骤

1. 启动后端：`cd backend && python -m src.main`
2. 访问 Swagger UI：`http://localhost:8000/docs`
3. 调用 `POST /payment/orders/create` 创建订单
4. 获取 `qr_code_data` 显示二维码
5. 调用 `GET /payment/orders/{id}` 查询状态
6. 模拟回调测试支付完成

---

## 九、部署注意事项

### 9.1 开发环境

- `notify_type = "AG"` - 主动查询模式
- `notify_url` 可为空

### 9.2 生产环境

- `notify_type = "HS"` - 回调通知模式
- `notify_url` 必须配置（443或80端口）
- 确保回调地址可从公网访问

---

## 十、附录

### 10.1 支持的支付方式位图

`supportAppType` 为4位字符串，每位表示：
- 第1位：工商银行
- 第2位：银联
- 第3位：微信
- 第4位：支付宝

示例：`1010` = 工行+微信

### 10.2 订单状态映射

| 工行 pay_status | 本系统状态 |
|----------------|-----------|
| 0 | paid |
| 1 | failed |
| 2 | processing（继续查询） |

### 10.3 工行返回码

| 返回码 | 说明 |
|-------|------|
| 0 | 成功 |
| 400011 | 参数非法 |
| 400017 | 签名验证失败 |
| 85502 | 参数需URLEncoder |
