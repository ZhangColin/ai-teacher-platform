# -*- coding: utf-8 -*-
"""API Key 加密服务

使用 Fernet 对称加密保护存储在数据库中的敏感信息（如 API Key）
"""
import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class EncryptionService:
    """加密服务（使用 Fernet 对称加密）"""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        初始化加密服务

        Args:
            encryption_key: 加密密钥（32字节base64编码）。如果为None，从环境变量读取
        """
        if encryption_key:
            self._key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        else:
            # 从环境变量读取
            env_key = os.getenv("API_KEY_ENCRYPTION_KEY")
            if not env_key:
                raise ValueError(
                    "未配置加密密钥。请设置环境变量 API_KEY_ENCRYPTION_KEY "
                    "(生成方法: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
                )
            self._key = env_key.encode()

        # 验证密钥格式
        try:
            self._fernet = Fernet(self._key)
        except Exception as e:
            raise ValueError(f"加密密钥格式错误: {e}")

        logger.info("加密服务初始化成功")

    def encrypt(self, plaintext: str) -> str:
        """
        加密明文字符串

        Args:
            plaintext: 明文

        Returns:
            加密后的字符串（Base64编码）

        Raises:
            ValueError: 明文为空
        """
        if not plaintext:
            raise ValueError("明文不能为空")

        try:
            # Fernet 要求输入为字节
            plaintext_bytes = plaintext.encode('utf-8')
            encrypted_bytes = self._fernet.encrypt(plaintext_bytes)
            # 转换为字符串存储
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        解密密文字符串

        Args:
            ciphertext: 密文（Base64编码）

        Returns:
            解密后的明文

        Raises:
            ValueError: 密文为空或解密失败
        """
        if not ciphertext:
            raise ValueError("密文不能为空")

        try:
            # Fernet 要求输入为字节
            ciphertext_bytes = ciphertext.encode('utf-8')
            decrypted_bytes = self._fernet.decrypt(ciphertext_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise ValueError(f"解密失败: {e}")

    def is_encrypted(self, value: str) -> bool:
        """
        判断字符串是否为加密格式

        Args:
            value: 待检测的字符串

        Returns:
            是否为加密格式
        """
        if not value:
            return False

        try:
            # 尝试解密，如果成功则认为是加密格式
            self.decrypt(value)
            return True
        except Exception:
            return False

    @staticmethod
    def generate_key() -> str:
        """
        生成新的加密密钥

        Returns:
            Base64编码的密钥（44字符）

        Example:
            >>> key = EncryptionService.generate_key()
            >>> print(key)
            'abcdefghijklmnopqrstuvwxyz123456='
        """
        return Fernet.generate_key().decode('utf-8')

    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
        """
        从密码派生加密密钥（用于密钥管理）

        Args:
            password: 用户密码
            salt: 盐值（如果为None则生成新盐值）

        Returns:
            (密钥, 盐值) 元组
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode('utf-8'), salt
