# 工行二维码支付对接实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完整对接工行二维码支付接口，替换现有模拟支付代码

**Architecture:** 新建 IcbcQrCodeClient 封装工行 API 调用，修改 PaymentService 使用真实 API，配置通过 icbc_config.py 集中管理，删除旧的 icbc_client.py

**Tech Stack:** FastAPI, SQLAlchemy, httpx, cryptography (RSA2 签名)

---

## 文件结构

### 新建文件
| 文件 | 职责 |
|------|------|
| `backend/src/config/icbc_config.py` | 工行配置加载和密钥文件读取 |
| `backend/src/services/icbc_qrcode_client.py` | 工行二维码支付 API 客户端 |
| `backend/tests/unit/test_icbc_qrcode_client.py` | 客户端单元测试 |

### 修改文件
| 文件 | 修改内容 |
|------|----------|
| `backend/src/services/payment_service.py` | 替换导入，移除模拟代码 |
| `backend/src/interfaces/routers/payment.py` | 更新 get_icbc_client() 函数 |

### 删除文件
| 文件 | 原因 |
|------|------|
| `backend/src/services/icbc_client.py` | 旧实现，替换为新客户端 |

---

## Task 0: 配置 .gitignore 确保密钥安全

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: 检查 .gitignore 中是否已有密钥目录配置**

```bash
grep -n "src/key" .gitignore
```

Expected: 如果没有找到，继续下一步

- [ ] **Step 2: 添加密钥目录到 .gitignore**

```bash
# 在 .gitignore 文件末尾添加

# 工行支付密钥文件（敏感信息，禁止提交）
backend/src/key/
```

- [ ] **Step 3: 验证密钥目录已被忽略**

```bash
# 检查密钥文件是否被 git 跟踪
git ls-files backend/src/key/

# 如果有输出，说明文件已被跟踪，需要先移除
git rm --cached backend/src/key/AI_客户用.pri backend/src/key/AI_银行用.pub backend/src/key/AI_AESKey.txt 2>/dev/null || true
```

- [ ] **Step 4: 提交**

```bash
git add .gitignore
git commit -m "chore: 将工行密钥目录添加到 .gitignore"
```

---

## Task 1: 创建工行配置管理模块

**Files:**
- Create: `backend/src/config/icbc_config.py`
- Create: `backend/tests/unit/test_icbc_config.py`

- [ ] **Step 1: 编写配置模块的测试**

```python
# backend/tests/unit/test_icbc_config.py
import os
import pytest
from pathlib import Path

def test_load_icbc_config():
    """测试工行配置加载"""
    from src.config.icbc_config import ICBC_PAYMENT_CONFIG, get_icbc_client_config

    # 验证必需的配置项存在
    assert "app_id" in ICBC_PAYMENT_CONFIG
    assert "mer_id" in ICBC_PAYMENT_CONFIG
    assert "private_key_path" in ICBC_PAYMENT_CONFIG
    assert "public_key_path" in ICBC_PAYMENT_CONFIG
    assert "notify_url" in ICBC_PAYMENT_CONFIG

    # 验证默认值
    assert ICBC_PAYMENT_CONFIG["app_id"] == "11000000000000079872"
    assert ICBC_PAYMENT_CONFIG["mer_id"] == "020004161912"

    # 验证密钥文件路径存在
    assert Path(ICBC_PAYMENT_CONFIG["private_key_path"]).exists()
    assert Path(ICBC_PAYMENT_CONFIG["public_key_path"]).exists()

def test_get_icbc_client_config():
    """测试获取客户端配置"""
    from src.config.icbc_config import get_icbc_client_config

    config = get_icbc_client_config()

    # 验证返回的配置包含必需字段
    assert "app_id" in config
    assert "mer_id" in config
    assert "private_key_pem" in config
    assert "public_key_pem" in config
    assert "notify_url" in config

    # 验证密钥已加载（非空字符串）
    assert len(config["private_key_pem"]) > 0
    assert len(config["public_key_pem"]) > 0
    assert config["private_key_pem"].startswith("-----BEGIN")
    assert config["public_key_pem"].startswith("-----BEGIN")
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/unit/test_icbc_config.py -v
```

Expected: `ImportError: No module named 'src.config.icbc_config'`

- [ ] **Step 2.5: 确保 config 目录存在且有 __init__.py**

```bash
# 检查 config 目录
ls -la backend/src/config/ 2>/dev/null || mkdir -p backend/src/config

# 确保 __init__.py 存在
touch backend/src/config/__init__.py
```

- [ ] **Step 3: 实现配置模块**

```python
# backend/src/config/icbc_config.py
# -*- coding: utf-8 -*-
"""工行支付配置"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 密钥文件路径
KEY_DIR = BASE_DIR / "src" / "key"

# 工行支付配置
ICBC_PAYMENT_CONFIG = {
    "app_id": os.getenv("ICBC_APP_ID", "11000000000000079872"),
    "mer_id": os.getenv("ICBC_MER_ID", "020004161912"),
    "private_key_path": os.getenv("ICBC_PRIVATE_KEY_PATH", str(KEY_DIR / "AI_客户用.pri")),
    "public_key_path": os.getenv("ICBC_PUBLIC_KEY_PATH", str(KEY_DIR / "AI_银行用.pub")),
    "notify_url": os.getenv("ICBC_NOTIFY_URL", ""),
}


def load_key_content(file_path: str) -> str:
    """
    加载密钥文件内容（支持裸 Base64 和 PEM 格式）

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
        if "PRIVATE" in file_path.upper() or ".pri" in file_path.lower():
            content = f"-----BEGIN RSA PRIVATE KEY-----\n{content}\n-----END RSA PRIVATE KEY-----"
        else:
            content = f"-----BEGIN PUBLIC KEY-----\n{content}\n-----END PUBLIC KEY-----"

    return content


def get_icbc_client_config() -> dict:
    """
    获取工行客户端初始化配置

    Returns:
        包含 app_id, mer_id, private_key_pem, public_key_pem, notify_url 的字典
    """
    return {
        "app_id": ICBC_PAYMENT_CONFIG["app_id"],
        "mer_id": ICBC_PAYMENT_CONFIG["mer_id"],
        "private_key_pem": load_key_content(ICBC_PAYMENT_CONFIG["private_key_path"]),
        "public_key_pem": load_key_content(ICBC_PAYMENT_CONFIG["public_key_path"]),
        "notify_url": ICBC_PAYMENT_CONFIG["notify_url"],
    }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/unit/test_icbc_config.py -v
```

Expected: `PASSED`

- [ ] **Step 5: 提交**

```bash
git add backend/src/config/icbc_config.py backend/tests/unit/test_icbc_config.py
git commit -m "feat: 添加工行支付配置管理模块"
```

---

## Task 2: 创建工行二维码支付客户端 - 基础结构和签名验签

**Files:**
- Create: `backend/src/services/icbc_qrcode_client.py`
- Modify: `backend/tests/unit/test_icbc_qrcode_client.py`

- [ ] **Step 1: 编写签名验签的测试**

```python
# backend/tests/unit/test_icbc_qrcode_client.py
import pytest
from src.services.icbc_qrcode_client import IcbcQrCodeClient

@pytest.fixture
def icbc_client():
    """创建测试用的工行客户端"""
    # 使用真实密钥文件进行测试
    from src.config.icbc_config import get_icbc_client_config
    config = get_icbc_client_config()
    return IcbcQrCodeClient(
        app_id=config["app_id"],
        mer_id=config["mer_id"],
        private_key_pem=config["private_key_pem"],
        public_key_pem=config["public_key_pem"],
        notify_url="",
    )

def test_client_initialization(icbc_client):
    """测试客户端初始化"""
    assert icbc_client.app_id == "11000000000000079872"
    assert icbc_client.mer_id == "020004161912"
    assert icbc_client._private_key is not None
    assert icbc_client._public_key is not None

def test_sign(icbc_client):
    """测试 RSA2 签名"""
    data = "app_id=11000000000000079872&charset=UTF-8&format=json"
    signature = icbc_client._sign(data)

    # 验证签名是 Base64 编码的字符串
    assert isinstance(signature, str)
    assert len(signature) > 0
    # Base64 编码的签名只包含特定字符
    import base64
    try:
        base64.b64decode(signature)
        assert True
    except Exception:
        assert False, "签名不是有效的 Base64 编码"

def test_verify(icbc_client):
    """测试 RSA2 验签"""
    data = "app_id=11000000000000079872&charset=UTF-8&format=json"
    signature = icbc_client._sign(data)

    # 验证自己的签名应该成功
    assert icbc_client._verify(data, signature) is True

    # 错误的签名应该验证失败
    assert icbc_client._verify(data, "wrong_signature") is False

def test_build_sign_str(icbc_client):
    """测试构建签名字符串"""
    params = {
        "app_id": "11000000000000079872",
        "charset": "UTF-8",
        "format": "json",
        "sign": "should_be_ignored",
        "empty_value": "",
        "none_value": None,
    }

    sign_str = icbc_client._build_sign_str(params)

    # 验证参数按字典序排序
    assert sign_str == "app_id=11000000000000079872&charset=UTF-8&format=json"

    # 验证空值和 None 被排除
    assert "empty_value" not in sign_str
    assert "none_value" not in sign_str
    assert "sign" not in sign_str
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/unit/test_icbc_qrcode_client.py::test_client_initialization -v
```

Expected: `ImportError: No module named 'src.services.icbc_qrcode_client'`

- [ ] **Step 3: 实现客户端基础结构和签名验签**

```python
# backend/src/services/icbc_qrcode_client.py
# -*- coding: utf-8 -*-
"""工行二维码支付客户端"""
import json
import logging
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
    API_GENERATE_QRCODE = "https://gw.open.icbc.com.cn/api/qrcode/V2/generate"
    API_QUERY_ORDER = "https://gw.open.icbc.com.cn/api/qrcode/query/V5"

    def __init__(
        self,
        app_id: str,
        mer_id: str,
        private_key_pem: str,
        public_key_pem: str,
        notify_url: str,
    ):
        """
        初始化工行二维码支付客户端

        Args:
            app_id: 应用编号
            mer_id: 商户编号（12位）
            private_key_pem: 商户私钥（PEM 格式字符串）
            public_key_pem: 工行网关公钥（PEM 格式字符串）
            notify_url: 支付结果回调地址（可选）
        """
        self.app_id = app_id
        self.mer_id = mer_id
        self.private_key_pem = private_key_pem
        self.public_key_pem = public_key_pem
        self.notify_url = notify_url

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
        """
        filtered = {k: v for k, v in params.items()
                   if v is not None and v != "" and k != "sign"}
        sorted_params = sorted(filtered.items())
        return "&".join([f"{k}={v}" for k, v in sorted_params])
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/unit/test_icbc_qrcode_client.py -v
```

Expected: `PASSED` (4 tests)

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/icbc_qrcode_client.py backend/tests/unit/test_icbc_qrcode_client.py
git commit -m "feat: 添加工行二维码支付客户端基础结构和签名验签"
```

---

## Task 3: 实现二维码生成接口

**Files:**
- Modify: `backend/src/services/icbc_qrcode_client.py`
- Modify: `backend/tests/unit/test_icbc_qrcode_client.py`

- [ ] **Step 1: 编写二维码生成接口的测试（使用 mock）**

```python
# 在 backend/tests/unit/test_icbc_qrcode_client.py 中添加

from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.asyncio
async def test_generate_qrcode_success(icbc_client):
    """测试生成二维码成功（mock 工行接口）"""
    mock_response = {
        "return_code": "0",
        "return_msg": "成功",
        "qrcode": "TEST_QR_CODE_DATA_STRING",
        "order_id": "ICBC_TEST_ORDER_123",
    }

    with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = lambda: None

        result = await icbc_client.generate_qrcode(
            out_trade_no="TEST2026032612345678",
            amount=1,  # 1分钱
            trade_date="20260326",
            trade_time="123456",
            expire_seconds=900,
        )

        assert result["return_code"] == "0"
        assert result["qrcode"] == "TEST_QR_CODE_DATA_STRING"
        assert result["order_id"] == "ICBC_TEST_ORDER_123"

@pytest.mark.asyncio
async def test_generate_qrcode_builds_correct_request(icbc_client):
    """测试生成二维码时构建正确的请求"""
    with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = {"return_code": "0", "qrcode": "test"}
        mock_post.return_value.raise_for_status = lambda: None

        await icbc_client.generate_qrcode(
            out_trade_no="TEST2026032612345678",
            amount=1,
            trade_date="20260326",
            trade_time="123456",
        )

        # 验证调用了正确的端点
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert icbc_client.API_GENERATE_QRCODE in str(call_args)

        # 验证请求体包含必需参数
        import json
        request_json = call_args[1]["json"]
        assert request_json["app_id"] == "11000000000000079872"
        assert request_json["sign_type"] == "RSA2"
        assert "sign" in request_json

        # 验证 biz_content
        biz_content = json.loads(request_json["biz_content"])
        assert biz_content["merId"] == "020004161912"
        assert biz_content["outTradeNo"] == "TEST2026032612345678"
        assert biz_content["orderAmt"] == "1"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/unit/test_icbc_qrcode_client.py::test_generate_qrcode_success -v
```

Expected: `AttributeError: 'IcbcQrCodeClient' object has no attribute 'generate_qrcode'`

- [ ] **Step 3: 实现二维码生成接口**

```python
# 在 backend/src/services/icbc_qrcode_client.py 的 IcbcQrCodeClient 类中添加

    async def generate_qrcode(
        self,
        out_trade_no: str,
        amount: int,
        trade_date: str,
        trade_time: str,
        expire_seconds: int = 900,
        attach: str = "",
    ) -> dict:
        """
        生成支付二维码

        Args:
            out_trade_no: 商户订单号
            amount: 金额（分）
            trade_date: 交易日期 yyyyMMdd
            trade_time: 交易时间 HHmmss
            expire_seconds: 二维码有效期（秒），默认900秒（15分钟），必须小于24小时
            attach: 附加数据，原样返回

        Returns:
            工行响应结果
            {
                "return_code": "0",  # 0=成功
                "return_msg": "成功",
                "qrcode": "二维码数据字符串",
                "order_id": "工行订单号"
            }
        """
        # 构建业务参数
        biz_content = {
            "merId": self.mer_id,
            "outTradeNo": out_trade_no,
            "orderAmt": str(amount),
            "tradeDate": trade_date,
            "tradeTime": trade_time,
            "payExpire": str(expire_seconds),
            "attach": attach,
            "tporderCreateIp": "127.0.0.1",
            "spFlag": "0",  # 不跳转分行
            "notifyFlag": "1" if self.notify_url else "0",  # 是否开启通知
        }

        # 如果有回调URL，添加到bizContent
        if self.notify_url:
            biz_content["notifyUrl"] = self.notify_url

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 构建请求参数
        params = {
            "app_id": self.app_id,
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

        logger.info(f"工行二维码生成请求 - 订单号:{out_trade_no}, 金额:{amount}分")
        logger.debug(f"签名原文: {sign_str}")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.API_GENERATE_QRCODE,
                json=params,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"工行二维码生成响应 - 订单号:{out_trade_no}, 响应码:{result.get('return_code')}")

        return result
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/unit/test_icbc_qrcode_client.py::test_generate_qrcode_success -v
```

Expected: `PASSED`

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/icbc_qrcode_client.py backend/tests/unit/test_icbc_qrcode_client.py
git commit -m "feat: 实现工行二维码生成接口"
```

---

## Task 4: 实现订单查询接口

**Files:**
- Modify: `backend/src/services/icbc_qrcode_client.py`
- Modify: `backend/tests/unit/test_icbc_qrcode_client.py`

- [ ] **Step 1: 编写订单查询接口的测试**

```python
# 在 backend/tests/unit/test_icbc_qrcode_client.py 中添加

@pytest.mark.asyncio
async def test_query_order_success(icbc_client):
    """测试查询订单成功（mock 工行接口）"""
    mock_response = {
        "return_code": "0",
        "return_msg": "成功",
        "payStatus": "1",  # 1=支付成功
        "order_id": "ICBC_TEST_ORDER_123",
    }

    with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = lambda: None

        result = await icbc_client.query_order(
            out_trade_no="TEST2026032612345678",
        )

        assert result["return_code"] == "0"
        assert result["payStatus"] == "1"

@pytest.mark.asyncio
async def test_query_order_with_order_id(icbc_client):
    """测试使用工行订单号查询"""
    with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = {"return_code": "0"}
        mock_post.return_value.raise_for_status = lambda: None

        await icbc_client.query_order(
            out_trade_no="TEST2026032612345678",
            order_id="ICBC_ORDER_123",
        )

        # 验证请求中包含 order_id
        call_args = mock_post.call_args
        import json
        request_json = call_args[1]["json"]
        biz_content = json.loads(request_json["biz_content"])
        assert biz_content["orderId"] == "ICBC_ORDER_123"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/unit/test_icbc_qrcode_client.py::test_query_order_success -v
```

Expected: `AttributeError: 'IcbcQrCodeClient' object has no attribute 'query_order'`

- [ ] **Step 3: 实现订单查询接口**

```python
# 在 backend/src/services/icbc_qrcode_client.py 的 IcbcQrCodeClient 类中添加

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
                "payStatus": "1",  # 0=支付中, 1=支付成功, 2=支付失败
                "order_id": "工行订单号"
            }
        """
        biz_content = {
            "merId": self.mer_id,
            "outTradeNo": out_trade_no,
        }

        if order_id:
            biz_content["orderId"] = order_id

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        params = {
            "app_id": self.app_id,
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

        logger.info(f"工行订单查询请求 - 订单号:{out_trade_no}")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.API_QUERY_ORDER,
                json=params,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"工行订单查询响应 - 订单号:{out_trade_no}, 状态:{result.get('payStatus', 'N/A')}")

        return result
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/unit/test_icbc_qrcode_client.py::test_query_order_success -v
```

Expected: `PASSED`

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/icbc_qrcode_client.py backend/tests/unit/test_icbc_qrcode_client.py
git commit -m "feat: 实现工行订单查询接口"
```

---

## Task 5: 实现回调验签

**Files:**
- Modify: `backend/src/services/icbc_qrcode_client.py`
- Modify: `backend/tests/unit/test_icbc_qrcode_client.py`

- [ ] **Step 1: 编写回调验签的测试**

```python
# 在 backend/tests/unit/test_icbc_qrcode_client.py 中添加

def test_verify_notify_success(icbc_client):
    """测试回调验签成功"""
    # 构造测试数据
    test_data = {
        "app_id": "11000000000000079872",
        "return_code": "0",
        "out_trade_no": "TEST123",
    }

    # 生成签名
    sign_str = icbc_client._build_sign_str(test_data)
    signature = icbc_client._sign(sign_str)
    test_data["sign"] = signature

    # 验签应该成功
    assert icbc_client.verify_notify(test_data) is True

def test_verify_notify_missing_sign(icbc_client):
    """测试回调验签 - 缺少签名"""
    test_data = {
        "app_id": "11000000000000079872",
        "return_code": "0",
    }

    assert icbc_client.verify_notify(test_data) is False

def test_verify_notify_wrong_sign(icbc_client):
    """测试回调验签 - 错误签名"""
    test_data = {
        "app_id": "11000000000000079872",
        "return_code": "0",
        "sign": "wrong_signature",
    }

    assert icbc_client.verify_notify(test_data) is False
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/unit/test_icbc_qrcode_client.py::test_verify_notify_success -v
```

Expected: `AttributeError: 'IcbcQrCodeClient' object has no attribute 'verify_notify'`

- [ ] **Step 3: 实现回调验签**

```python
# 在 backend/src/services/icbc_qrcode_client.py 的 IcbcQrCodeClient 类中添加

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

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/unit/test_icbc_qrcode_client.py::test_verify_notify_success -v
```

Expected: `PASSED`

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/icbc_qrcode_client.py backend/tests/unit/test_icbc_qrcode_client.py
git commit -m "feat: 实现工行回调验签功能"
```

---

## Task 6: 修改 PaymentService 使用新客户端

**Files:**
- Modify: `backend/src/services/payment_service.py`
- Modify: `backend/tests/integration/test_payment_api.py`

- [ ] **Step 1: 查看现有代码，确认需要修改的位置**

```bash
# 查看 payment_service.py 中的模拟代码
grep -n "模拟" backend/src/services/payment_service.py
```

Expected: 找到第 113-130 行左右的模拟代码

- [ ] **Step 2: 修改导入语句**

```python
# 在 backend/src/services/payment_service.py 中，将
from .icbc_client import IcbcClient

# 改为
from .icbc_qrcode_client import IcbcQrCodeClient
```

- [ ] **Step 3: 修改构造函数类型注解**

```python
# 在 backend/src/services/payment_service.py 中，将
def __init__(self, db: Session, icbc_client: IcbcClient, point_service: PointService):

# 改为
def __init__(self, db: Session, icbc_client: IcbcQrCodeClient, point_service: PointService):
```

- [ ] **Step 4: 移除模拟代码，启用真实 API 调用**

```python
# 在 backend/src/services/payment_service.py 的 create_payment_order 方法中，
# 找到模拟代码（大约第 113-130 行），删除并替换为：

        # 5. 准备工行接口所需的时间参数
        now = datetime.now()
        trade_date = now.strftime("%Y%m%d")   # yyyyMMdd
        trade_time = now.strftime("%H%M%S")   # HHmmss

        # 6. 调用工行二维码生成接口（真实调用）
        icbc_response = await self.icbc_client.generate_qrcode(
            out_trade_no=out_trade_no,
            amount=amount,
            trade_date=trade_date,
            trade_time=trade_time,
            expire_seconds=expire_time,
            attach=body[:21] if len(body) > 21 else body,  # 最多21个汉字
        )

        # 7. 更新订单状态
        order.status = PaymentOrderStatus.processing
        order.submitted_at = datetime.now()
        order.icbc_response = icbc_response

        # 8. 解析工行响应
        if icbc_response.get("return_code") == "0":  # 成功
            order.qr_code_data = icbc_response.get("qrcode")
            order.third_trade_no = icbc_response.get("order_id")
        else:
            # 下单失败
            order.status = PaymentOrderStatus.failed
            error_msg = icbc_response.get("return_msg", "未知错误")
            raise ValueError(f"工行下单失败: {error_msg}")
```

- [ ] **Step 5: 同样修改 query_payment_status 方法中的模拟代码**

```python
# 在 backend/src/services/payment_service.py 的 query_payment_status 方法中，
# 找到模拟代码（大约第 189-200 行），删除并替换为：

        # 如果订单未完成，主动查询工行
        if order.status in [PaymentOrderStatus.created, PaymentOrderStatus.processing]:
            try:
                icbc_response = await self.icbc_client.query_order(order.out_trade_no)

                order.icbc_response = icbc_response

                # 解析支付状态
                if icbc_response.get("return_code") == "0":
                    pay_status = icbc_response.get("payStatus")
                    if pay_status == "1":  # 支付成功
                        await self._handle_payment_success(order, icbc_response)
                    elif pay_status == "2":  # 支付失败
                        order.status = PaymentOrderStatus.failed

                self.db.commit()

            except Exception as e:
                logger.error(f"查询支付状态失败 - 订单ID:{order_id}, 错误:{e}", exc_info=True)
```

- [ ] **Step 6: 修改 handle_notify 方法使用新的验签方法**

```python
# 在 backend/src/services/payment_service.py 的 handle_notify 方法中，
# 将验签部分改为：

    async def handle_notify(self, notify_data: dict) -> bool:
        """
        处理工行支付回调

        Args:
            notify_data: 回调数据

        Returns:
            处理是否成功
        """
        # 1. 验签
        if not self.icbc_client.verify_notify(notify_data):
            logger.error(f"支付回调验签失败: {notify_data}")
            return False

        # ... 其余逻辑保持不变 ...

- [ ] **Step 7: 修改 _handle_payment_success 方法适配新接口响应**

```python
# 在 backend/src/services/payment_service.py 的 _handle_payment_success 方法中，
# 修改工行订单号的获取方式（新接口直接在根节点，不在 biz_content 中）：

async def _handle_payment_success(self, order: PaymentOrderModel, icbc_response: dict) -> None:
    """
    处理支付成功

    Args:
        order: 订单对象
        icbc_response: 工行响应
    """
    # 1. 更新订单状态
    order.status = PaymentOrderStatus.paid
    order.paid_at = datetime.now()

    # 新接口：工行订单号直接在响应根节点（不是 biz_content）
    order.third_trade_no = icbc_response.get("order_id")

    # ... 其余代码保持不变 ...
```

- [ ] **Step 8: 运行现有测试验证**
```

- [ ] **Step 7: 运行现有测试验证**

```bash
cd backend && python -m pytest tests/integration/test_payment_api.py -v
```

注意：由于需要真实调用工行接口，此测试可能需要调整或使用 mock。

- [ ] **Step 9: 提交**

```bash
git add backend/src/services/payment_service.py
git commit -m "refactor: payment_service 使用新的 icbc_qrcode_client，移除模拟代码"
```

---

## Task 7: 修改路由依赖

**Files:**
- Modify: `backend/src/interfaces/routers/payment.py`

- [ ] **Step 1: 修改 get_icbc_client 函数**

```python
# 在 backend/src/interfaces/routers/payment.py 中，将 get_icbc_client() 函数改为：

def get_icbc_client():
    """获取工行二维码支付客户端实例"""
    from src.services.icbc_qrcode_client import IcbcQrCodeClient
    from src.config.icbc_config import get_icbc_client_config

    config = get_icbc_client_config()

    return IcbcQrCodeClient(
        app_id=config["app_id"],
        mer_id=config["mer_id"],
        private_key_pem=config["private_key_pem"],
        public_key_pem=config["public_key_pem"],
        notify_url=config["notify_url"],
    )
```

- [ ] **Step 2: 运行路由测试**

```bash
cd backend && python -m pytest tests/integration/test_payment_api.py -v
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/interfaces/routers/payment.py
git commit -m "refactor: 更新 payment 路由使用新的 icbc_qrcode_client"
```

---

## Task 8: 删除旧的工行客户端

**Files:**
- Delete: `backend/src/services/icbc_client.py`

- [ ] **Step 1: 确认没有其他文件引用旧的 icbc_client**

```bash
cd backend && grep -r "from.*icbc_client import" --include="*.py" | grep -v ".pyc"
```

Expected: 无结果（或只有 payment_service.py 已被修改）

- [ ] **Step 2: 删除旧文件**

```bash
rm backend/src/services/icbc_client.py
```

- [ ] **Step 3: 运行所有测试确认**

```bash
cd backend && python -m pytest tests/unit/test_icbc_qrcode_client.py tests/unit/test_icbc_config.py -v
```

- [ ] **Step 4: 提交**

```bash
git rm backend/src/services/icbc_client.py
git commit -m "refactor: 删除旧的 icbc_client.py，已被 icbc_qrcode_client.py 替代"
```

---

## Task 9: 更新 .env.example 文件

**Files:**
- Modify: `backend/.env.example`

- [ ] **Step 1: 添加工行配置示例**

```bash
# 在 backend/.env.example 文件末尾添加

# 工行支付配置
ICBC_APP_ID=11000000000000079872
ICBC_MER_ID=020004161912
ICBC_NOTIFY_URL=https://your-domain.com/api/v1/payment/icbc/notify
ICBC_PRIVATE_KEY_PATH=backend/src/key/AI_客户用.pri
ICBC_PUBLIC_KEY_PATH=backend/src/key/AI_银行用.pub
```

- [ ] **Step 2: 提交**

```bash
git add backend/.env.example
git commit -m "docs: 添加工行支付配置示例到 .env.example"
```

---

## Task 10: 端到端测试（可选，需要真实环境）

**Files:**
- Create: `backend/tests/e2e/test_icbc_payment_e2e.py`

- [ ] **Step 1: 编写端到端测试**

```python
# backend/tests/e2e/test_icbc_payment_e2e.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_payment_order_e2e(async_client: AsyncClient, auth_headers):
    """端到端测试：创建支付订单"""
    response = await async_client.post(
        "/api/v1/payment/create-order",
        json={"amount": 1},  # 1分钱
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 1
    assert data["qr_code_data"] is not None
    assert data["status"] in ["created", "processing"]

@pytest.mark.asyncio
async def test_query_payment_order_e2e(async_client: AsyncClient, auth_headers):
    """端到端测试：查询订单状态"""
    # 先创建订单
    create_response = await async_client.post(
        "/api/v1/payment/create-order",
        json={"amount": 1},
        headers=auth_headers,
    )
    order_id = create_response.json()["order_id"]

    # 查询订单
    query_response = await async_client.get(
        f"/api/v1/payment/order/{order_id}",
        headers=auth_headers,
    )

    assert query_response.status_code == 200
    data = query_response.json()
    assert data["order_id"] == order_id
```

- [ ] **Step 2: 提交**

```bash
git add backend/tests/e2e/test_icbc_payment_e2e.py
git commit -m "test: 添加工行支付端到端测试"
```

---

## 验收标准

完成后，以下功能应该正常工作：

1. ✅ 调用 `/api/v1/payment/create-order` 创建支付订单，返回二维码数据
2. ✅ 调用 `/api/v1/payment/order/{id}` 查询订单状态
3. ✅ 工行回调 `/api/v1/payment/icbc/notify` 正确验签并处理
4. ✅ 支付成功后企业积分正确增加
5. ✅ 所有单元测试通过
6. ✅ 旧的 `icbc_client.py` 已删除

---

## 注意事项

1. **密钥安全**：确保 `backend/src/key/` 目录已在 `.gitignore` 中
2. **金额固定**：测试期间所有订单金额固定为 1 分钱
3. **日志记录**：所有工行 API 调用都有详细日志
4. **错误处理**：所有异常都被捕获并记录，订单状态正确更新
