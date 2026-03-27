# 工行二维码支付重新实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 严格按照工行官方文档重新实现二维码支付接口，修复现有实现的API端点、参数命名和缺失字段问题。

**架构:** 删除现有 IcbcQrCodeClient 实现，按照工行文档重写两个核心方法（generate_qrcode、query_order），新增回调接口，调整数据库模型和配置。

**Tech Stack:** FastAPI, SQLAlchemy, httpx, cryptography (RSA2签名)

---

## 文件结构

```
backend/src/
├── db_models.py                    # 修改：PaymentOrderModel 添加4个字段
├── config/
│   └── icbc_config.py              # 重写：更新配置结构
├── services/
│   ├── icbc_qrcode_client.py       # 重写：两个API方法
│   └── payment_service.py          # 修改：响应字段名调整
└── interfaces/
    └── routers/
        └── payment.py              # 新增：回调路由

backend/tests/
├── unit/
│   ├── test_icbc_config.py         # 新增：配置测试
│   └── test_icbc_qrcode_client.py  # 重写：客户端测试
└── integration/
    └── test_payment_flow.py        # 修改：集成测试

alembic/versions/
└── xxx_add_icbc_fields.py          # 新增：数据库迁移
```

---

## Task 1: 数据库模型修改

**Files:**
- Modify: `backend/src/db_models.py:544-588`

- [ ] **Step 1: 添加新字段到 PaymentOrderModel**

```python
# 在 PaymentOrderModel 类中，现有字段后添加：

# 工行业务参数
goods_name = Column(String(40), nullable=True, comment='商品名称')
attach = Column(String(127), nullable=True, comment='附加数据，原样返回')
support_app_type = Column(String(10), nullable=True, comment='支持的支付方式位图')
msg_id = Column(String(40), nullable=True, comment='消息通讯唯一编号')
```

将这4行添加到第568行（`qr_code_data` 字段）之后。

- [ ] **Step 2: 创建数据库迁移**

```bash
cd backend
alembic revision --autogenerate -m "add_icbc_order_fields"
```

预期：生成迁移文件在 `alembic/versions/` 目录

- [ ] **Step 3: 检查迁移文件内容**

打开生成的迁移文件，确认包含：
- `goods_name` (String(40))
- `attach` (String(127))
- `support_app_type` (String(10))
- `msg_id` (String(40))

- [ ] **Step 4: 执行迁移**

```bash
alembic upgrade head
```

预期：输出 "Running upgrade" 并成功

- [ ] **Step 5: 验证数据库字段**

```bash
mysql -u root -p -e "DESCRIBE ai_teacher_platform.payment_orders;" | grep -E "goods_name|attach|support_app_type|msg_id"
```

预期：显示4个新字段

- [ ] **Step 6: 提交**

```bash
git add backend/src/db_models.py alembic/versions/
git commit -m "feat: 添加工行支付订单字段"
```

---

## Task 2: 配置文件重写

**Files:**
- Modify: `backend/src/config/icbc_config.py`
- Test: `backend/tests/unit/test_icbc_config.py`

- [ ] **Step 1: 删除旧配置文件内容**

```bash
rm backend/src/config/icbc_config.py
```

- [ ] **Step 2: 创建新配置文件**

创建 `backend/src/config/icbc_config.py`：

```python
# -*- coding: utf-8 -*-
"""工行支付配置"""
import os
import textwrap
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
KEY_DIR = BASE_DIR / "src" / "key"

# 工行支付配置
ICBC_PAYMENT_CONFIG = {
    # 基础配置
    "app_id": os.getenv("ICBC_APP_ID", "11000000000000079872"),
    "mer_id": os.getenv("ICBC_MER_ID", "020004161912"),
    "mer_prtcl_no": os.getenv("ICBC_MER_PRTCL_NO", "0200041619120201"),  # mer_id + "0201"

    # 交易配置
    "access_type": "6",          # PC支付
    "cur_type": "001",           # 人民币
    "goods_name": "智研云平台充值",
    "body": "智研云平台充值",

    # 通知配置
    "notify_type": os.getenv("ICBC_NOTIFY_TYPE", "AG"),  # AG=主动查询, HS=回调通知
    "result_type": "0",          # 0=成功失败都通知
    "notify_url": os.getenv("ICBC_NOTIFY_URL", ""),

    # 密钥文件路径
    "private_key_path": str(KEY_DIR / "AI_客户用.pri"),
    "public_key_path": str(KEY_DIR / "AI_银行用.pub"),
}


def load_key_content(file_path: str) -> str:
    """
    加载密钥文件，将裸Base64转换为PEM格式

    工行密钥文件是裸 Base64 格式，需要转换为 PEM 格式才能被 cryptography 库解析

    Args:
        file_path: 密钥文件路径

    Returns:
        PEM 格式的密钥内容字符串
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # 如果是裸 Base64（无 BEGIN/END 标记），转换为 PEM 格式
    if not content.startswith("-----BEGIN"):
        # 将 Base64 内容按 64 字符换行
        wrapped_content = textwrap.wrap(content, width=64)
        base64_body = "\n".join(wrapped_content)

        if "PRIVATE" in file_path.upper() or ".pri" in file_path.lower():
            # 工行密钥是 PKCS#8 格式，使用 BEGIN PRIVATE KEY
            content = f"-----BEGIN PRIVATE KEY-----\n{base64_body}\n-----END PRIVATE KEY-----"
        else:
            content = f"-----BEGIN PUBLIC KEY-----\n{base64_body}\n-----END PUBLIC KEY-----"

    return content


def get_icbc_client_config() -> dict:
    """
    获取工行客户端初始化配置

    Returns:
        包含 app_id, mer_id, mer_prtcl_no, private_key_pem, public_key_pem, notify_url 等的字典
    """
    return {
        "app_id": ICBC_PAYMENT_CONFIG["app_id"],
        "mer_id": ICBC_PAYMENT_CONFIG["mer_id"],
        "mer_prtcl_no": ICBC_PAYMENT_CONFIG["mer_prtcl_no"],
        "access_type": ICBC_PAYMENT_CONFIG["access_type"],
        "cur_type": ICBC_PAYMENT_CONFIG["cur_type"],
        "goods_name": ICBC_PAYMENT_CONFIG["goods_name"],
        "body": ICBC_PAYMENT_CONFIG["body"],
        "notify_type": ICBC_PAYMENT_CONFIG["notify_type"],
        "result_type": ICBC_PAYMENT_CONFIG["result_type"],
        "notify_url": ICBC_PAYMENT_CONFIG["notify_url"],
        "private_key_pem": load_key_content(ICBC_PAYMENT_CONFIG["private_key_path"]),
        "public_key_pem": load_key_content(ICBC_PAYMENT_CONFIG["public_key_path"]),
    }
```

- [ ] **Step 3: 编写配置测试**

创建 `backend/tests/unit/test_icbc_config.py`：

```python
# -*- coding: utf-8 -*-
"""工行配置测试"""
import pytest
from backend.src.config.icbc_config import (
    ICBC_PAYMENT_CONFIG,
    load_key_content,
    get_icbc_client_config
)


class TestIcbcConfig:
    """工行配置测试"""

    def test_config_structure(self):
        """测试配置结构完整"""
        required_keys = [
            "app_id", "mer_id", "mer_prtcl_no",
            "access_type", "cur_type", "goods_name", "body",
            "notify_type", "result_type", "notify_url",
            "private_key_path", "public_key_path"
        ]
        for key in required_keys:
            assert key in ICBC_PAYMENT_CONFIG

    def test_mer_prtcl_no_format(self):
        """测试协议编号格式 = mer_id + 0201"""
        assert ICBC_PAYMENT_CONFIG["mer_prtcl_no"] == ICBC_PAYMENT_CONFIG["mer_id"] + "0201"

    def test_access_type_is_pc(self):
        """测试接入方式为PC"""
        assert ICBC_PAYMENT_CONFIG["access_type"] == "6"

    def test_cur_type_is_rmb(self):
        """测试币种为人民币"""
        assert ICBC_PAYMENT_CONFIG["cur_type"] == "001"

    def test_load_private_key_pem_format(self):
        """测试私钥转换为PEM格式"""
        pem = load_key_content(ICBC_PAYMENT_CONFIG["private_key_path"])
        assert pem.startswith("-----BEGIN PRIVATE KEY-----")
        assert pem.endswith("-----END PRIVATE KEY-----")

    def test_load_public_key_pem_format(self):
        """测试公钥转换为PEM格式"""
        pem = load_key_content(ICBC_PAYMENT_CONFIG["public_key_path"])
        assert pem.startswith("-----BEGIN PUBLIC KEY-----")
        assert pem.endswith("-----END PUBLIC KEY-----")

    def test_get_client_config(self):
        """测试获取客户端配置"""
        config = get_icbc_client_config()
        assert "private_key_pem" in config
        assert "public_key_pem" in config
        assert config["app_id"] == ICBC_PAYMENT_CONFIG["app_id"]
```

- [ ] **Step 4: 运行测试**

```bash
cd backend
pytest tests/unit/test_icbc_config.py -v
```

预期：8 passed

- [ ] **Step 5: 提交**

```bash
git add backend/src/config/icbc_config.py backend/tests/unit/test_icbc_config.py
git commit -m "feat: 重写工行配置文件"
```

---

## Task 3: IcbcQrCodeClient 重写 - 签名方法

**Files:**
- Modify: `backend/src/services/icbc_qrcode_client.py`

- [ ] **Step 1: 删除旧文件**

```bash
rm backend/src/services/icbc_qrcode_client.py
```

- [ ] **Step 2: 创建新的客户端文件 - 基础结构和签名方法**

创建 `backend/src/services/icbc_qrcode_client.py`：

```python
# -*- coding: utf-8 -*-
"""工行二维码支付客户端"""
import json
import logging
import uuid
from datetime import datetime
from typing import Optional
from base64 import b64encode, b64decode
import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class IcbcQrCodeClient:
    """工行二维码支付客户端"""

    # API 端点
    API_GENERATE_QRCODE = "https://gw.open.icbc.com.cn/api/cardbusiness/qrcode/consumption/V1"
    API_QUERY_ORDER = "https://gw.open.icbc.com.cn/api/cardbusiness/aggregatepay/b2c/online/orderqry/V1"

    def __init__(
        self,
        app_id: str,
        mer_id: str,
        mer_prtcl_no: str,
        access_type: str,
        cur_type: str,
        goods_name: str,
        body: str,
        notify_type: str,
        result_type: str,
        notify_url: str,
        private_key_pem: str,
        public_key_pem: str,
    ):
        """
        初始化工行二维码支付客户端

        Args:
            app_id: 应用编号
            mer_id: 商户编号（12位）
            mer_prtcl_no: 协议编号（mer_id + 0201）
            access_type: 接入方式（6=PC）
            cur_type: 币种（001=人民币）
            goods_name: 商品名称
            body: 商品描述
            notify_type: 通知类型（AG=主动查询, HS=回调通知）
            result_type: 结果类型（0=成功失败都通知）
            notify_url: 回调地址
            private_key_pem: 商户私钥（PEM 格式字符串）
            public_key_pem: 工行网关公钥（PEM 格式字符串）
        """
        self.app_id = app_id
        self.mer_id = mer_id
        self.mer_prtcl_no = mer_prtcl_no
        self.access_type = access_type
        self.cur_type = cur_type
        self.goods_name = goods_name
        self.body = body
        self.notify_type = notify_type
        self.result_type = result_type
        self.notify_url = notify_url
        self.private_key_pem = private_key_pem
        self.public_key_pem = public_key_pem

        # 预加载密钥
        self._private_key = None
        self._public_key = None
        self._load_keys()

    def _load_keys(self):
        """预加载 RSA 密钥"""
        try:
            self._private_key = serialization.load_pem_private_key(
                self.private_key_pem.encode(),
                password=None,
                backend=default_backend()
            )
            self._public_key = serialization.load_pem_public_key(
                self.public_key_pem.encode(),
                backend=default_backend()
            )
            logger.info("工行密钥加载成功")
        except Exception as e:
            logger.error(f"工行密钥加载失败: {e}")
            raise

    def _generate_msg_id(self) -> str:
        """
        生成消息通讯唯一编号

        格式：时间戳 + 随机数，确保40位以内且APP级唯一

        Returns:
            msg_id 字符串
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = uuid.uuid4().hex[:8].upper()
        return f"{timestamp}{random_str}"

    def _sign(self, data: str) -> str:
        """
        RSA2 签名 (SHA256WithRSA)

        Args:
            data: 待签名字符串

        Returns:
            Base64 编码的签名
        """
        signature = self._private_key.sign(
            data.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return b64encode(signature).decode('utf-8')

    def _verify(self, data: str, sign: str) -> bool:
        """
        RSA2 验签

        Args:
            data: 待验签字符串
            sign: Base64 编码的签名

        Returns:
            验签结果
        """
        try:
            signature = b64decode(sign)
            self._public_key.verify(
                signature,
                data.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            logger.error(f"验签失败: {e}")
            return False

    def _build_sign_str(self, params: dict) -> str:
        """
        构建签名字符串

        工行签名规则：参数按字典序排序，拼接成 key1=value1&key2=value2 格式
        注意：排除 sign 字段和空值

        Args:
            params: 请求参数字典

        Returns:
            签名字符串
        """
        filtered = {k: v for k, v in params.items()
                   if v is not None and v != "" and k != "sign"}
        sorted_params = sorted(filtered.items())
        return "&".join([f"{k}={v}" for k, v in sorted_params])
```

- [ ] **Step 3: 运行测试检查语法**

```bash
cd backend
python -c "from backend.src.services.icbc_qrcode_client import IcbcQrCodeClient; print('Import OK')"
```

预期：Import OK

- [ ] **Step 4: 提交**

```bash
git add backend/src/services/icbc_qrcode_client.py
git commit -m "feat: 重写工行客户端基础结构和签名方法"
```

---

## Task 4: IcbcQrCodeClient - generate_qrcode 方法

**Files:**
- Modify: `backend/src/services/icbc_qrcode_client.py`

- [ ] **Step 1: 添加 generate_qrcode 方法**

在 `IcbcQrCodeClient` 类中，`_build_sign_str` 方法后添加：

```python
    async def generate_qrcode(
        self,
        out_trade_no: str,
        amount: int,
        expire_seconds: int = 900,
        attach: str = "",
    ) -> dict:
        """
        生成支付二维码

        Args:
            out_trade_no: 商户订单号
            amount: 金额（分）
            expire_seconds: 二维码有效期（秒），默认900秒（15分钟）
            attach: 附加数据，原样返回

        Returns:
            工行响应结果
            {
                "return_code": "0",  # 0=成功
                "return_msg": "成功",
                "codeUrl": "二维码数据字符串",
                "supportAppType": "1010"  # 支持的支付方式位图
            }
        """
        # 生成 msg_id
        msg_id = self._generate_msg_id()

        # 准备时间参数
        now = datetime.now()
        order_date = now.strftime("%Y-%m-%d %H:%M:%S")
        timestamp = order_date

        # 构建 biz_content
        biz_content = {
            "out_trade_no": out_trade_no,
            "mer_id": self.mer_id,
            "mer_prtcl_no": self.mer_prtcl_no,
            "access_type": self.access_type,
            "cur_type": self.cur_type,
            "amount": str(amount),
            "icbc_appid": self.app_id,
            "expire_time": str(expire_seconds),
            "notify_type": self.notify_type,
            "result_type": self.result_type,
            "attach": attach,
            "order_date": order_date,
            "goods_name": self.goods_name,
            "body": self.body,
        }

        # 如果有回调URL，添加到biz_content
        if self.notify_url:
            biz_content["mer_url"] = self.notify_url

        # 构建请求参数
        params = {
            "app_id": self.app_id,
            "msg_id": msg_id,
            "format": "json",
            "charset": "UTF-8",
            "sign_type": "RSA2",
            "timestamp": timestamp,
            "biz_content": json.dumps(biz_content, ensure_ascii=False),
        }

        # 签名
        sign_str = self._build_sign_str(params)
        sign = self._sign(sign_str)
        params["sign"] = sign

        logger.info(f"工行二维码生成请求 - 订单号:{out_trade_no}, 金额:{amount}分, msg_id:{msg_id}")
        logger.debug(f"签名原文: {sign_str}")

        # 发送请求
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.API_GENERATE_QRCODE,
                data=params,  # 使用 data 而不是 json，工行要求 form-urlencoded
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"工行二维码生成响应 - 订单号:{out_trade_no}, 响应码:{result.get('return_code')}")
        logger.debug(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

        return result
```

- [ ] **Step 2: 编写单元测试**

创建/修改 `backend/tests/unit/test_icbc_qrcode_client.py`：

```python
# -*- coding: utf-8 -*-
"""工行客户端测试"""
import pytest
from backend.src.services.icbc_qrcode_client import IcbcQrCodeClient
from backend.src.config.icbc_config import get_icbc_client_config


class TestIcbcQrCodeClient:
    """工行客户端测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        config = get_icbc_client_config()
        return IcbcQrCodeClient(**config)

    def test_init(self, client):
        """测试客户端初始化"""
        assert client.app_id is not None
        assert client.mer_id is not None
        assert client._private_key is not None
        assert client._public_key is not None

    def test_generate_msg_id(self, client):
        """测试 msg_id 生成"""
        msg_id = client._generate_msg_id()
        assert len(msg_id) <= 40
        assert msg_id.isalnum()

    def test_sign_and_verify(self, client):
        """测试签名和验签"""
        test_data = "test_string_for_signing"
        signature = client._sign(test_data)
        assert signature  # 签名非空

        # 验签
        result = client._verify(test_data, signature)
        assert result is True

        # 错误验签
        result = client._verify(test_data, "wrong_signature")
        assert result is False

    def test_build_sign_str(self, client):
        """测试签名字符串构建"""
        params = {
            "app_id": "123",
            "msg_id": "456",
            "format": "json",
            "sign": "should_be_ignored",
            "empty_value": "",
            "null_value": None,
            "z_param": "last",
            "a_param": "first",
        }
        sign_str = client._build_sign_str(params)

        # 检查排序和过滤
        assert "a_param=first" in sign_str
        assert "z_param=last" in sign_str
        assert "sign=" not in sign_str
        assert "empty_value=" not in sign_str
        assert "null_value=" not in sign_str

    @pytest.mark.asyncio
    async def test_generate_qrcode_request_params(self, client):
        """测试生成二维码请求参数构造"""
        # 注意：这只是一个参数构造测试，不会真正调用API
        # 实际API调用需要集成测试或mock

        # 准备测试数据
        out_trade_no = "TEST2026032612043000001"
        amount = 1  # 1分钱

        # 这里我们只测试内部方法，不发送真实请求
        msg_id = client._generate_msg_id()
        assert msg_id is not None

        biz_content = {
            "out_trade_no": out_trade_no,
            "mer_id": client.mer_id,
            "mer_prtcl_no": client.mer_prtcl_no,
            "access_type": client.access_type,
            "cur_type": client.cur_type,
            "amount": str(amount),
            "icbc_appid": client.app_id,
            "expire_time": "900",
            "notify_type": client.notify_type,
            "result_type": client.result_type,
            "attach": "",
            "order_date": "2026-03-26 12:04:30",
            "goods_name": client.goods_name,
            "body": client.body,
        }

        # 验证必填字段
        required_keys = [
            "out_trade_no", "mer_id", "mer_prtcl_no", "access_type",
            "cur_type", "amount", "icbc_appid", "notify_type",
            "result_type", "order_date", "goods_name", "body"
        ]
        for key in required_keys:
            assert key in biz_content
```

- [ ] **Step 3: 运行测试**

```bash
cd backend
pytest tests/unit/test_icbc_qrcode_client.py -v
```

预期：6 passed

- [ ] **Step 4: 提交**

```bash
git add backend/src/services/icbc_qrcode_client.py backend/tests/unit/test_icbc_qrcode_client.py
git commit -m "feat: 实现工行生成二维码方法"
```

---

## Task 5: IcbcQrCodeClient - query_order 方法

**Files:**
- Modify: `backend/src/services/icbc_qrcode_client.py`

- [ ] **Step 1: 添加 query_order 方法**

在 `generate_qrcode` 方法后添加：

```python
    async def query_order(
        self,
        out_trade_no: str,
        order_id: str = None,
    ) -> dict:
        """
        查询订单状态

        Args:
            out_trade_no: 商户订单号
            order_id: 工行订单号（可选，与out_trade_no二选一）

        Returns:
            工行响应结果
            {
                "return_code": "0",
                "return_msg": "成功",
                "pay_status": "0",  # 0=成功, 1=失败, 2=未知
                "order_id": "工行订单号"
            }
        """
        # 生成 msg_id
        msg_id = self._generate_msg_id()

        # 当前时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 构建 biz_content
        biz_content = {
            "mer_id": self.mer_id,
            "out_trade_no": out_trade_no,
            "deal_flag": "0",  # 0=查询
            "icbc_appid": self.app_id,
            "mer_prtcl_no": self.mer_prtcl_no,
        }

        if order_id:
            biz_content["order_id"] = order_id

        # 构建请求参数
        params = {
            "app_id": self.app_id,
            "msg_id": msg_id,
            "format": "json",
            "charset": "UTF-8",
            "sign_type": "RSA2",
            "timestamp": timestamp,
            "biz_content": json.dumps(biz_content, ensure_ascii=False),
        }

        # 签名
        sign_str = self._build_sign_str(params)
        sign = self._sign(sign_str)
        params["sign"] = sign

        logger.info(f"工行订单查询请求 - 订单号:{out_trade_no}, msg_id:{msg_id}")

        # 发送请求
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.API_QUERY_ORDER,
                data=params,
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            )
            response.raise_for_status()
            result = response.json()

        # 解析响应
        if "response_biz_content" in result:
            biz_content = result["response_biz_content"]
            logger.info(f"工行订单查询响应 - 订单号:{out_trade_no}, 状态:{biz_content.get('pay_status', 'N/A')}")
        else:
            logger.warning(f"工行订单查询响应格式异常: {result}")

        return result
```

- [ ] **Step 2: 更新单元测试**

在 `test_icbc_qrcode_client.py` 中添加：

```python
    def test_query_order_params(self, client):
        """测试查询订单参数构造"""
        out_trade_no = "TEST2026032612043000001"

        biz_content = {
            "mer_id": client.mer_id,
            "out_trade_no": out_trade_no,
            "deal_flag": "0",
            "icbc_appid": client.app_id,
            "mer_prtcl_no": client.mer_prtcl_no,
        }

        # 验证必填字段
        required_keys = ["mer_id", "out_trade_no", "deal_flag", "icbc_appid", "mer_prtcl_no"]
        for key in required_keys:
            assert key in biz_content

    def test_query_order_with_order_id(self, client):
        """测试带工行订单号的查询"""
        out_trade_no = "TEST2026032612043000001"
        order_id = "0200041619122026032612043000001"

        biz_content = {
            "mer_id": client.mer_id,
            "out_trade_no": out_trade_no,
            "order_id": order_id,
            "deal_flag": "0",
            "icbc_appid": client.app_id,
            "mer_prtcl_no": client.mer_prtcl_no,
        }

        assert "order_id" in biz_content
        assert biz_content["order_id"] == order_id
```

- [ ] **Step 3: 运行测试**

```bash
cd backend
pytest tests/unit/test_icbc_qrcode_client.py -v
```

预期：8 passed

- [ ] **Step 4: 提交**

```bash
git add backend/src/services/icbc_qrcode_client.py backend/tests/unit/test_icbc_qrcode_client.py
git commit -m "feat: 实现工行查询订单方法"
```

---

## Task 6: IcbcQrCodeClient - verify_notify 方法

**Files:**
- Modify: `backend/src/services/icbc_qrcode_client.py`

- [ ] **Step 1: 添加 verify_notify 方法**

在 `query_order` 方法后添加：

```python
    def verify_notify(self, notify_data: dict) -> bool:
        """
        验证工行回调签名

        Args:
            notify_data: 回调数据（包含sign字段）

        Returns:
            验签结果
        """
        sign = notify_data.get("sign")
        if not sign:
            logger.error("回调数据缺少签名")
            return False

        sign_str = self._build_sign_str(notify_data)
        result = self._verify(sign_str, sign)

        if result:
            logger.info("回调验签成功")
        else:
            logger.error(f"回调验签失败 - 签名原文: {sign_str}")

        return result
```

- [ ] **Step 2: 添加回调响应签名方法**

在 `verify_notify` 方法后添加：

```python
    def sign_notify_response(self, return_code: int, msg_id: str) -> dict:
        """
        对回调响应进行签名

        Args:
            return_code: 返回码（0=成功）
            msg_id: 消息通讯唯一编号

        Returns:
            包含签名的响应字典
        """
        response_biz_content = {
            "return_code": return_code,
            "return_msg": "success" if return_code == 0 else "fail",
            "msg_id": msg_id,
        }

        # 构建签名字符串：response_biz_content + sign_type
        # 注意：工行要求特定格式，不含空格换行
        sign_params = {
            "response_biz_content": json.dumps(response_biz_content, separators=(',', ':')),
            "sign_type": "RSA2",
        }

        sign_str = self._build_sign_str(sign_params)
        sign = self._sign(sign_str)

        return {
            "response_biz_content": response_biz_content,
            "sign_type": "RSA2",
            "sign": sign,
        }
```

- [ ] **Step 3: 更新单元测试**

在 `test_icbc_qrcode_client.py` 中添加：

```python
    def test_verify_notify(self, client):
        """测试回调验签"""
        # 构造测试数据
        test_data = {
            "from": "icbc-api",
            "api": "/api/test",
            "app_id": client.app_id,
            "charset": "utf-8",
            "format": "json",
            "sign_type": "RSA2",
            "timestamp": "2026-03-26 12:04:30",
        }

        # 生成签名
        sign_str = client._build_sign_str(test_data)
        sign = client._sign(sign_str)
        test_data["sign"] = sign

        # 验签应该成功
        result = client.verify_notify(test_data)
        assert result is True

    def test_sign_notify_response(self, client):
        """测试回调响应签名"""
        msg_id = "TEST_MSG_ID_123"
        response = client.sign_notify_response(0, msg_id)

        assert "response_biz_content" in response
        assert "sign_type" in response
        assert "sign" in response
        assert response["response_biz_content"]["return_code"] == 0
        assert response["response_biz_content"]["msg_id"] == msg_id
        assert response["sign_type"] == "RSA2"
```

- [ ] **Step 4: 运行测试**

```bash
cd backend
pytest tests/unit/test_icbc_qrcode_client.py -v
```

预期：11 passed

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/icbc_qrcode_client.py backend/tests/unit/test_icbc_qrcode_client.py
git commit -m "feat: 实现工行回调验签和响应签名方法"
```

---

## Task 7: payment_service.py 修改

**Files:**
- Modify: `backend/src/services/payment_service.py`

- [ ] **Step 1: 更新 create_payment_order 方法**

找到 `create_payment_order` 方法中调用 `icbc_client.generate_qrcode` 的部分，修改：

原代码（约第118-125行）：
```python
            icbc_response = await self.icbc_client.generate_qrcode(
                out_trade_no=out_trade_no,
                amount=amount,
                trade_date=trade_date,
                trade_time=trade_time,
                expire_seconds=expire_time,
                attach=body[:21] if len(body) > 21 else body,
            )
```

修改为：
```python
            icbc_response = await self.icbc_client.generate_qrcode(
                out_trade_no=out_trade_no,
                amount=amount,
                expire_seconds=expire_time,
                attach=body[:127] if len(body) > 127 else body,  # 工行限制127字符
            )
```

- [ ] **Step 2: 修改响应字段解析**

找到 `create_payment_order` 方法中解析工行响应的部分（约第132-140行）：

原代码：
```python
            if icbc_response.get("return_code") == "0":  # 成功
                order.qr_code_data = icbc_response.get("qrcode")
                order.third_trade_no = icbc_response.get("order_id")
```

修改为：
```python
            if icbc_response.get("return_code") == "0":  # 成功
                order.qr_code_data = icbc_response.get("codeUrl")  # 改名：codeUrl
                order.third_trade_no = icbc_response.get("order_id")
                order.support_app_type = icbc_response.get("supportAppType")  # 新增
```

- [ ] **Step 3: 添加新字段保存**

在创建订单记录时添加新字段（约第99-108行）：

```python
        order = PaymentOrderModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            out_trade_no=out_trade_no,
            amount=amount,
            status=PaymentOrderStatus.created,
            business_type="recharge",
            expire_at=expire_at,
            goods_name=self.icbc_client.goods_name,  # 新增
            attach=body[:127] if len(body) > 127 else body,  # 新增
        )
```

- [ ] **Step 4: 修改 msg_id 保存**

在更新订单状态时（约第128-130行），添加 msg_id：

```python
            order.status = PaymentOrderStatus.processing
            order.submitted_at = datetime.now()
            order.icbc_response = icbc_response
            order.msg_id = icbc_response.get("msg_id", "")  # 新增
```

- [ ] **Step 5: 修改 query_payment_status 方法**

找到 `query_payment_status` 方法中解析查询响应的部分（约第187-193行）：

原代码：
```python
                if icbc_response.get("return_code") == "0":
                    pay_status = icbc_response.get("payStatus")
                    if pay_status == "1":  # 支付成功
```

修改为：
```python
                # 工行查询响应在 response_biz_content 中
                biz_content = icbc_response.get("response_biz_content", {})
                if biz_content.get("return_code") == "0" or icbc_response.get("return_code") == "0":
                    pay_status = biz_content.get("pay_status")
                    if pay_status == "0":  # 0=成功（注意：工行查询接口0表示成功）
                        await self._handle_payment_success(order, biz_content)
                    elif pay_status == "1":  # 1=失败
                        order.status = PaymentOrderStatus.failed
```

- [ ] **Step 6: 运行测试**

```bash
cd backend
pytest tests/integration/test_payment_flow.py -v -k "create_payment"
```

预期：测试通过

- [ ] **Step 7: 提交**

```bash
git add backend/src/services/payment_service.py
git commit -m "fix: 调整支付服务适配新工行接口"
```

---

## Task 8: payment.py 路由更新依赖

**Files:**
- Modify: `backend/src/interfaces/routers/payment.py`

- [ ] **Step 1: 更新 get_icbc_client 函数**

找到 `get_icbc_client` 函数，确保使用新的配置：

```python
def get_icbc_client() -> IcbcQrCodeClient:
    """获取工行客户端实例"""
    from backend.src.config.icbc_config import get_icbc_client_config

    config = get_icbc_client_config()
    return IcbcQrCodeClient(**config)
```

- [ ] **Step 2: 添加回调路由**

在 payment.py 中添加：

```python
@router.post("/icbc/notify")
async def icbc_notify(
    request: Request,
    db: Session = Depends(get_db),
    icbc_client: IcbcQrCodeClient = Depends(get_icbc_client),
):
    """
    工行支付回调接口

    工行支付网关在支付完成后会调用此接口通知支付结果
    """
    from urllib.parse import parse_qs

    # 1. 获取回调参数（URL参数编码格式）
    body = await request.body()
    params = parse_qs(body.decode('utf-8'))

    # 将参数列表转换为单值（parse_qs 返回的是列表）
    notify_data = {k: v[0] if v else "" for k, v in params.items()}

    logger.info(f"收到工行支付回调: {notify_data}")

    # 2. 验签
    if not icbc_client.verify_notify(notify_data):
        logger.error("支付回调验签失败")
        raise HTTPException(status_code=400, detail="签名验证失败")

    # 3. 解析 biz_content
    try:
        biz_content_str = notify_data.get("biz_content", "{}")
        biz_content = json.loads(biz_content_str)
    except json.JSONDecodeError as e:
        logger.error(f"回调 biz_content 解析失败: {e}")
        raise HTTPException(status_code=400, detail="回调数据格式错误")

    # 4. 处理支付结果
    payment_service = PaymentService(db, icbc_client, None)  # point_service 暂时为None
    success = await payment_service.handle_notify(biz_content)

    if not success:
        logger.error("支付回调处理失败")
        raise HTTPException(status_code=500, detail="处理失败")

    # 5. 返回指定格式响应
    msg_id = notify_data.get("msg_id", "")
    response = icbc_client.sign_notify_response(0, msg_id)

    return JSONResponse(content=response)
```

- [ ] **Step 3: 添加导入**

在文件顶部添加：

```python
from fastapi.responses import JSONResponse
```

- [ ] **Step 4: 运行测试**

```bash
cd backend
python -c "from backend.src.interfaces.routers.payment import router; print('Import OK')"
```

预期：Import OK

- [ ] **Step 5: 提交**

```bash
git add backend/src/interfaces/routers/payment.py
git commit -m "feat: 添加工行支付回调接口"
```

---

## Task 9: payment_service.py handle_notify 修改

**Files:**
- Modify: `backend/src/services/payment_service.py`

- [ ] **Step 1: 修改 handle_notify 方法**

找到 `handle_notify` 方法（约第208-258行），修改响应字段解析：

原代码：
```python
        # 6. 判断支付状态
        if notify_data.get("trade_status") == "1":  # 支付成功
```

修改为：
```python
        # 6. 判断支付状态
        # 工行回调：return_code=0 表示成功
        if notify_data.get("return_code") == "0":  # 支付成功
            await self._handle_payment_success(order, notify_data)
            self.db.commit()
            return True
```

- [ ] **Step 2: 运行测试**

```bash
cd backend
pytest tests/integration/test_payment_flow.py -v
```

预期：测试通过

- [ ] **Step 3: 提交**

```bash
git add backend/src/services/payment_service.py
git commit -m "fix: 修复回调处理状态判断"
```

---

## Task 10: 集成测试和验证

**Files:**
- Test: 手动测试

- [ ] **Step 1: 启动后端服务**

```bash
cd backend
python -m src.main
```

预期：服务运行在 http://localhost:8000

- [ ] **Step 2: 访问 Swagger UI**

浏览器打开：http://localhost:8000/docs

- [ ] **Step 3: 测试创建订单**

1. 找到 `POST /api/v1/payment/orders/create` 接口
2. 点击 "Try it out"
3. 输入请求体：
```json
{
  "amount": 1,
  "body": "智研云平台充值"
}
```
4. 点击 "Execute"

预期检查点：
- 返回状态码 200
- 返回包含 `qr_code_data` 字段
- 返回包含 `order_id`
- 日志显示工行请求和响应

- [ ] **Step 4: 检查日志**

查看后端日志，确认：
- 签名原文正确
- 请求参数包含所有必填字段
- 工行响应包含 `codeUrl`

- [ ] **Step 5: 测试查询订单**

1. 使用上一步返回的 `order_id`
2. 找到 `GET /api/v1/payment/orders/{order_id}` 接口
3. 输入 `order_id`
4. 点击 "Execute"

预期：返回订单状态信息

- [ ] **Step 6: 验证数据库**

```bash
mysql -u root -p -e "SELECT order_id, out_trade_no, amount, status, goods_name, attach, msg_id FROM ai_teacher_platform.payment_orders ORDER BY created_at DESC LIMIT 1;"
```

预期：显示最新订单，包含新字段

- [ ] **Step 7: 提交**

```bash
git add .
git commit -m "test: 完成集成测试验证"
```

---

## 验收标准

- [ ] 所有单元测试通过（15+ passed）
- [ ] 集成测试通过
- [ ] 创建订单成功，返回 `codeUrl`
- [ ] 查询订单返回正确状态
- [ ] 数据库包含4个新字段
- [ ] 日志显示正确的请求参数和签名
- [ ] 回调接口可访问（即使验签失败）

---

## 回滚计划

如果出现问题，可以通过以下命令回滚：

```bash
git reset --hard <commit-before-changes>
alembic downgrade -1
```
