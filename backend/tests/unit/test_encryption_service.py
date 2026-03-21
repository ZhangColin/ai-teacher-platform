# -*- coding: utf-8 -*-
"""加密服务单元测试"""
import pytest
from src.services.encryption_service import EncryptionService


class TestEncryptionService:
    """加密服务测试类"""

    def test_generate_key(self):
        """测试密钥生成"""
        key = EncryptionService.generate_key()
        assert isinstance(key, str)
        assert len(key) == 44  # Fernet 密钥固定44字符
        # 再生成一个，确保不同
        key2 = EncryptionService.generate_key()
        assert key != key2

    def test_encrypt_and_decrypt(self):
        """测试加密和解密"""
        # 使用临时密钥初始化
        key = EncryptionService.generate_key()
        service = EncryptionService(encryption_key=key)

        # 测试各种字符串
        test_cases = [
            "hello world",
            "sk-1234567890abcdef",
            "这是一个中文测试",
            "!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "a" * 1000,  # 长字符串
            "",  # 空字符串应该失败
        ]

        for plaintext in test_cases[:-1]:  # 跳过空字符串
            # 加密
            ciphertext = service.encrypt(plaintext)
            assert isinstance(ciphertext, str)
            assert ciphertext != plaintext
            assert len(ciphertext) > len(plaintext)

            # 解密
            decrypted = service.decrypt(ciphertext)
            assert decrypted == plaintext

    def test_encrypt_empty_string(self):
        """测试加密空字符串（应该失败）"""
        key = EncryptionService.generate_key()
        service = EncryptionService(encryption_key=key)

        with pytest.raises(ValueError, match="明文不能为空"):
            service.encrypt("")

    def test_decrypt_empty_string(self):
        """测试解密空字符串（应该失败）"""
        key = EncryptionService.generate_key()
        service = EncryptionService(encryption_key=key)

        with pytest.raises(ValueError, match="密文不能为空"):
            service.decrypt("")

    def test_decrypt_invalid_ciphertext(self):
        """测试解密无效密文"""
        key = EncryptionService.generate_key()
        service = EncryptionService(encryption_key=key)

        with pytest.raises(ValueError, match="解密失败"):
            service.decrypt("invalid_ciphertext")

    def test_decrypt_wrong_key(self):
        """测试使用错误的密钥解密"""
        key1 = EncryptionService.generate_key()
        key2 = EncryptionService.generate_key()

        service1 = EncryptionService(encryption_key=key1)
        service2 = EncryptionService(encryption_key=key2)

        plaintext = "secret message"
        ciphertext = service1.encrypt(plaintext)

        # 使用不同的密钥解密应该失败
        with pytest.raises(ValueError, match="解密失败"):
            service2.decrypt(ciphertext)

    def test_is_encrypted(self):
        """测试判断是否为加密格式"""
        key = EncryptionService.generate_key()
        service = EncryptionService(encryption_key=key)

        plaintext = "hello"
        ciphertext = service.encrypt(plaintext)

        assert service.is_encrypted(ciphertext) is True
        assert service.is_encrypted(plaintext) is False
        assert service.is_encrypted("") is False
        assert service.is_encrypted("not_encrypted") is False

    def test_encrypt_api_key(self):
        """测试加密 API Key（实际使用场景）"""
        key = EncryptionService.generate_key()
        service = EncryptionService(encryption_key=key)

        # 各种 API Key 格式
        api_keys = [
            "sk-ant1234567890abcdef",
            "sk-proj-abc123def456",
            "gpt_1234567890abcdef",
        ]

        for api_key in api_keys:
            ciphertext = service.encrypt(api_key)
            decrypted = service.decrypt(ciphertext)
            assert decrypted == api_key
            # 确保密文不是原文
            assert api_key not in ciphertext

    def test_derive_key_from_password(self):
        """测试从密码派生密钥"""
        password = "my_secure_password"

        # 派生密钥
        key1, salt1 = EncryptionService.derive_key_from_password(password)
        assert isinstance(key1, str)
        assert isinstance(salt1, bytes)
        assert len(salt1) == 16

        # 使用相同的密码和盐值，应该得到相同的密钥
        key2, salt2 = EncryptionService.derive_key_from_password(password, salt1)
        assert key1 == key2
        assert salt1 == salt2

        # 使用不同的盐值，应该得到不同的密钥
        key3, salt3 = EncryptionService.derive_key_from_password(password)
        assert key1 != key3
        assert salt1 != salt3

    def test_invalid_key_format(self):
        """测试无效的密钥格式"""
        with pytest.raises(ValueError, match="加密密钥格式错误"):
            EncryptionService(encryption_key="invalid_key")

    def test_unicode_encryption(self):
        """测试 Unicode 字符加密"""
        key = EncryptionService.generate_key()
        service = EncryptionService(encryption_key=key)

        # 各种 Unicode 字符
        test_strings = [
            "Hello 世界",
            "Привет мир",
            "مرحبا بالعالم",
            "🔐🔑🚀",
            "测试🧪Test",
        ]

        for text in test_strings:
            ciphertext = service.encrypt(text)
            decrypted = service.decrypt(ciphertext)
            assert decrypted == text
