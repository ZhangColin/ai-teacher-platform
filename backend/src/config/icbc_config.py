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
