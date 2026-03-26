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
    import textwrap

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
    else:
        # 如果已经是 PEM 格式，检查是否需要重新换行（兼容单行格式）
        lines = content.split("\n")
        if len(lines) == 3:  # HEADER + BODY + FOOTER (单行 body)
            body = lines[1]
            wrapped_body = "\n".join(textwrap.wrap(body, width=64))
            header = lines[0]
            footer = lines[2]
            content = f"{header}\n{wrapped_body}\n{footer}"

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
