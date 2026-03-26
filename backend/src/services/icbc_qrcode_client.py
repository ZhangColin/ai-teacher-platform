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
