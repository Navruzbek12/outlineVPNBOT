# bot/mock_outline.py
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MockOutlineAPI:
    """Outline API ni mock qilish (test uchun)"""
    
    def __init__(self, server_url: str = "", api_secret: str = ""):
        self.server_url = server_url or "https://mock.outline.server"
        self.api_secret = api_secret or "mock_secret"
        logger.warning("⚠️ Mock Outline API ishlatilmoqda - bu faqat test rejimi!")
    
    def test_connection(self) -> bool:
        """Serverga ulanishni test qilish"""
        logger.info("✅ Mock Outline serverga muvaffaqiyatli ulanildi (test)")
        return True
    
    def create_key(self, name: str, limit_gb: int = 10) -> Dict[str, Any]:
        """Yangi kalit yaratish"""
        logger.info(f"📝 Mock Outline key yaratildi: {name}")
        
        return {
            "id": "mock_key_id",
            "name": name,
            "password": "mock_password",
            "port": 12345,
            "method": "chacha20-ietf-poly1305",
            "accessUrl": "https://mock.outline.server/mock_key_id",
            "dataLimit": {
                "bytes": limit_gb * 1024 * 1024 * 1024
            }
        }
    
    def get_keys(self) -> list:
        """Barcha kalitlarni olish"""
        return []
    
    def delete_key(self, key_id: str) -> bool:
        """Kalitni o'chirish"""
        logger.info(f"🗑️ Mock Outline key o'chirildi: {key_id}")
        return True
    
    def rename_key(self, key_id: str, new_name: str) -> bool:
        """Kalitni nomini o'zgartirish"""
        logger.info(f"✏️ Mock Outline key nomi o'zgartirildi: {key_id} -> {new_name}")
        return True
    
    def set_data_limit(self, key_id: str, limit_gb: int) -> bool:
        """Kalit uchun data limit o'rnatish"""
        logger.info(f"📊 Mock Outline data limit o'rnatildi: {key_id} -> {limit_gb}GB")
        return True
    
    def delete_data_limit(self, key_id: str) -> bool:
        """Data limitni o'chirish"""
        logger.info(f"♾️ Mock Outline data limit o'chirildi: {key_id}")
        return True
    
    def get_server_info(self) -> Dict[str, Any]:
        """Server haqida ma'lumot olish"""
        return {
            "name": "Mock Outline Server",
            "serverId": "mock_server_id",
            "metricsEnabled": True,
            "createdTimestampMs": 1640995200000,
            "version": "1.0.0",
            "accessKeyDataLimit": {
                "bytes": 10737418240  # 10GB
            },
            "portForNewAccessKeys": 12345,
            "hostnameForAccessKeys": "mock.outline.server"
        }
