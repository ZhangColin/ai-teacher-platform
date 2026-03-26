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
