# -*- coding: utf-8 -*-
"""工行聚合支付客户端"""
import hashlib
import json
import logging
from typing import Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from base64 import b64encode, b64decode

logger = logging.getLogger(__name__)


class IcbcClient:
    """工行聚合支付客户端"""

    # API 端点
    API_CREATE_ORDER = "https://gw.open.icbc.com.cn/api/cardbusiness/aggregatepay/b2c/online/consumepurchase/V1"
    API_QUERY_ORDER = "https://gw.open.icbc.com.cn/api/cardbusiness/aggregatepay/b2c/online/orderqry/V1"

    def __init__(
        self,
        app_id: str,
        mer_id: str,
        mer_prtcl_no: str,
        private_key: str,
        public_key: str,
        device_info: str,
        notify_url: str,
    ):
        """
        初始化工行客户端

        Args:
            app_id: 应用编号
            mer_id: 商户编号
            mer_prtcl_no: 协议编号
            private_key: 商户私钥（PEM 格式）
            public_key: 工行公钥（PEM 格式）
            device_info: 设备号
            notify_url: 回调地址
        """
        self.app_id = app_id
        self.mer_id = mer_id
        self.mer_prtcl_no = mer_prtcl_no
        self.private_key = private_key
        self.public_key = public_key
        self.device_info = device_info
        self.notify_url = notify_url

    def _load_private_key(self):
        """加载私钥"""
        from cryptography.hazmat.primitives.asymmetric import rsa
        try:
            # 尝试 PEM 格式
            return serialization.load_pem_private_key(
                self.private_key.encode(),
                password=None,
                backend=default_backend()
            )
        except Exception:
            # 尝试 PKCS8 格式
            return serialization.load_der_private_key(
                b64decode(self.private_key),
                password=None,
                backend=default_backend()
            )

    def _load_public_key(self):
        """加载公钥"""
        try:
            return serialization.load_pem_public_key(
                self.public_key.encode(),
                backend=default_backend()
            )
        except Exception:
            return serialization.load_der_public_key(
                b64decode(self.public_key),
                backend=default_backend()
            )

    def _sign(self, data: str, sign_type: str = "RSA2") -> str:
        """
        RSA2 签名

        Args:
            data: 待签名字符串
            sign_type: 签名类型（RSA2/RSA）

        Returns:
            Base64 编码的签名
        """
        private_key = self._load_private_key()

        if sign_type == "RSA2":
            # RSA256 签名
            signature = private_key.sign(
                data.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        else:
            # RSA 签名（SHA1）
            signature = private_key.sign(
                data.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA1()
            )

        return b64encode(signature).decode('utf-8')

    def _verify(self, data: str, sign: str, sign_type: str = "RSA") -> bool:
        """
        RSA 验签

        Args:
            data: 待验签字符串
            sign: Base64 编码的签名
            sign_type: 签名类型（RSA2/RSA）

        Returns:
            验签结果
        """
        public_key = self._load_public_key()
        signature = b64decode(sign)

        try:
            if sign_type == "RSA2":
                public_key.verify(
                    signature,
                    data.encode('utf-8'),
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
            else:
                public_key.verify(
                    signature,
                    data.encode('utf-8'),
                    padding.PKCS1v15(),
                    hashes.SHA1()
                )
            return True
        except Exception as e:
            logger.error(f"验签失败: {e}")
            return False

    def _build_sign_str(self, params: dict, path: str = "") -> str:
        """
        构建签名字符串

        工行签名规则：参数按字典序排序，拼接成 key1=value1&key2=value2 格式
        """
        # 过滤空值和 sign 字段
        filtered = {k: v for k, v in params.items() if v is not None and v != "" and k != "sign"}
        # 按字典序排序
        sorted_params = sorted(filtered.items())
        # 拼接
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        return sign_str
