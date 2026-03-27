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
    # 新增API端点
    API_REFUND_ORDER = "https://gw.open.icbc.com.cn/api/cardbusiness/aggregatepay/b2c/online/merrefund/V1"
    API_QUERY_REFUND = "https://gw.open.icbc.com.cn/api/cardbusiness/aggregatepay/b2c/online/refundqry/V1"

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

    def _build_sign_str(self, params: dict, path: str = "") -> str:
        """
        构建签名字符串

        工行签名规则：{path}?{key1}={value1}&{key2}={value2}...
        参数按字典序排序（TreeMap 自然排序）
        注意：排除 sign 字段和空值

        Args:
            params: 请求参数字典
            path: URL 路径（如 /api/cardbusiness/qrcode/consumption/V1）

        Returns:
            签名字符串
        """
        # 使用 TreeMap 方式排序（字典序）
        filtered = {k: v for k, v in params.items()
                   if v is not None and v != "" and k != "sign"}
        sorted_params = sorted(filtered.items())

        # 构建签名字符串：路径?参数1=值1&参数2=值2...
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        if path:
            return f"{path}?{param_str}"
        return param_str

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

        # 构建 biz_content（按工行文档示例的字段顺序）
        biz_content = {
            "out_trade_no": out_trade_no,
            "mer_id": self.mer_id,
            "mer_prtcl_no": self.mer_prtcl_no,
            "access_type": self.access_type,
            "cur_type": self.cur_type,
            "amount": str(amount),
            "icbc_appid": self.app_id,
            "mer_url": self.notify_url if self.notify_url else "",  # 工行文档中该字段存在
            "expire_time": str(expire_seconds),
            "notify_type": self.notify_type,
            "result_type": self.result_type,
            "attach": attach,
            "order_apd_inf": "",  # 订单附件信息（可选，传空字符串）
            "order_date": order_date,
            "goods_name": self.goods_name,
            "body": self.body,
            "pay_limit": "",  # 支付方式限定（可选）
            "installment_times": "1",  # 分期付款期数（默认1=全额付款）
            "credit_type": "2",  # E支付支付方式限定（默认2=All）
            "goods_tag": "",  # 订单优惠标记（可选）
            "wxpay_detail": "",  # 微信商品详细描述（可选）
            "alipay_detail": "",  # 支付宝商品详细描述（可选）
        }

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

        # 签名 - 需要传入 URL 路径
        # SDK 的 buildOrderedSignStr 方法会将路径包含在签名字符串中
        sign_str = self._build_sign_str(params, "/api/cardbusiness/qrcode/consumption/V1")
        sign = self._sign(sign_str)
        params["sign"] = sign

        logger.info(f"工行二维码生成请求 - 订单号:{out_trade_no}, 金额:{amount}分, msg_id:{msg_id}")
        logger.debug(f"签名原文: {sign_str}")

        # 按照工行文档格式：所有参数放在 body 中（form-urlencoded 格式）
        # biz_content 作为 JSON 字符串
        body_params = {
            "app_id": params["app_id"],
            "msg_id": params["msg_id"],
            "format": params["format"],
            "charset": params["charset"],
            "sign_type": params["sign_type"],
            "timestamp": params["timestamp"],
            "sign": params["sign"],
            "biz_content": params["biz_content"],  # JSON 字符串
        }

        logger.debug(f"请求Body参数: {body_params}")

        # 发送请求（使用 data 参数，httpx 会自动进行 form-urlencoded 编码）
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.API_GENERATE_QRCODE,
                data=body_params,  # form-urlencoded 格式
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"工行二维码生成响应 - 订单号:{out_trade_no}, 响应码:{result.get('return_code')}")
        logger.debug(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

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

        # 签名 - 需要传入 URL 路径
        sign_str = self._build_sign_str(params, "/api/cardbusiness/aggregatepay/b2c/online/orderqry/V1")
        sign = self._sign(sign_str)
        params["sign"] = sign

        logger.info(f"工行订单查询请求 - 订单号:{out_trade_no}, msg_id:{msg_id}")
        logger.debug(f"签名原文: {sign_str}")

        # 按照工行文档格式：所有参数放在 body 中（form-urlencoded 格式）
        body_params = {
            "app_id": params["app_id"],
            "msg_id": params["msg_id"],
            "format": params["format"],
            "charset": params["charset"],
            "sign_type": params["sign_type"],
            "timestamp": params["timestamp"],
            "sign": params["sign"],
            "biz_content": params["biz_content"],  # JSON 字符串
        }

        logger.debug(f"请求Body参数: {body_params}")

        # 发送请求
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.API_QUERY_ORDER,
                data=body_params,  # form-urlencoded 格式
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
            order_id: 工行订单号（可选，与out_trade_no二选一）

        Returns:
            工行响应结果
            {
                "return_code": "0",  # 0=成功
                "return_msg": "success",
                "outtrx_serial_no": "商户退款流水号",
                "intrx_serial_no": "工行退款流水号",
                "reject_amt": "退款金额（分）",
                "real_reject_amt": "实际退款金额（分）"
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
            "outtrx_serial_no": out_refund_no,
            "ret_total_amt": str(refund_amount),
            "trnsc_ccy": "001",  # 人民币
            "icbc_appid": self.app_id,
            "mer_prtcl_no": self.mer_prtcl_no,
            "order_apd_inf": "",  # 订单附加信息
        }

        # 如果有工行订单号，添加到biz_content
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

        # 签名 - 需要传入 URL 路径
        sign_str = self._build_sign_str(params, "/api/cardbusiness/aggregatepay/b2c/online/merrefund/V1")
        sign = self._sign(sign_str)
        params["sign"] = sign

        logger.info(f"工行退款请求 - 订单号:{out_trade_no}, 退款金额:{refund_amount}分, msg_id:{msg_id}")
        logger.debug(f"签名原文: {sign_str}")

        # 按照工行文档格式：所有参数放在 body 中（form-urlencoded 格式）
        body_params = {
            "app_id": params["app_id"],
            "msg_id": params["msg_id"],
            "format": params["format"],
            "charset": params["charset"],
            "sign_type": params["sign_type"],
            "timestamp": params["timestamp"],
            "sign": params["sign"],
            "biz_content": params["biz_content"],  # JSON 字符串
        }

        logger.debug(f"请求Body参数: {body_params}")

        # 发送请求
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.API_REFUND_ORDER,
                data=body_params,  # form-urlencoded 格式
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"工行退款响应 - 订单号:{out_trade_no}, 响应码:{result.get('return_code')}")
        logger.debug(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

        return result

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
            {
                "return_code": "0",
                "return_msg": "success",
                "pay_status": "0",  # 0=成功, 1=失败, 2=未知
                "outtrx_serial_no": "商户退款流水号",
                "intrx_serial_no": "工行退款流水号",
                "reject_amt": "退款总金额（分）",
                "real_reject_amt": "实际退款金额（分）"
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
            "outtrx_serial_no": out_refund_no,
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
        sign_str = self._build_sign_str(params, "/api/cardbusiness/aggregatepay/b2c/online/refundqry/V1")
        sign = self._sign(sign_str)
        params["sign"] = sign

        logger.info(f"工行退款查询请求 - 退款流水号:{out_refund_no}, msg_id:{msg_id}")

        # 按照工行文档格式：所有参数放在 body 中（form-urlencoded 格式）
        body_params = {
            "app_id": params["app_id"],
            "msg_id": params["msg_id"],
            "format": params["format"],
            "charset": params["charset"],
            "sign_type": params["sign_type"],
            "timestamp": params["timestamp"],
            "sign": params["sign"],
            "biz_content": params["biz_content"],  # JSON 字符串
        }

        # 发送请求
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.API_QUERY_REFUND,
                data=body_params,
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"工行退款查询响应 - 退款流水号:{out_refund_no}, pay_status:{result.get('pay_status', 'N/A')}")

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
