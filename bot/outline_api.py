# bot/outline_api.py - TO'G'RI VERSIYA
import requests
import logging
from typing import Dict, Any
from urllib3.exceptions import InsecureRequestWarning
import warnings

# SSL ogohlantirishlarini o'chirish
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

logger = logging.getLogger(__name__)

class OutlineAPI:
    def __init__(self):
        """
        Outline API inicializatsiyasi
        """
        from bot.config import Config
        
        # Config dan ma'lumotlarni olish
        api_url = Config.OUTLINE_SERVER_URL
        api_secret = Config.OUTLINE_API_SECRET
        
        logger.info(f"Outline API initialization:")
        logger.info(f"  Server URL: {api_url}")
        logger.info(f"  API Secret: {api_secret[:10]}...")
        
        # URL manzilini tekshirish va tozalash
        if not api_url:
            raise ValueError("OUTLINE_SERVER_URL not configured")
        
        # Agar port allaqachon URLda bo'lsa, portni olib tashlash
        if ':' in api_url.split('//')[-1]:
            # URLda port bor, faqat shu URLni ishlatamiz
            base_url = api_url
            if not base_url.endswith('/'):
                base_url += '/'
            self.base_url = f"{base_url}{api_secret}"
            logger.info(f"  Base URL (with port in URL): {self.base_url[:60]}...")
        else:
            # URLda port yo'q, standart port qo'shamiz
            api_port = Config.OUTLINE_API_PORT
            if not api_url.endswith('/'):
                api_url += '/'
            self.base_url = f"{api_url}:{api_port}/{api_secret}"
            logger.info(f"  Base URL (added port): {self.base_url[:60]}...")
    
    def test_connection(self) -> bool:
        """Serverga ulanishni test qilish"""
        try:
            logger.info(f"Testing Outline connection...")
            
            url = f"{self.base_url}/server"
            logger.info(f"Request URL: {url}")
            
            response = requests.get(
                url,
                headers={'Content-Type': 'application/json'},
                timeout=10,
                verify=False
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Outline serverga muvaffaqiyatli ulanildi")
                return True
            else:
                logger.warning(f"⚠️ Outline connection test failed: {response.status_code}")
                logger.debug(f"Response: {response.text[:200]}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Outline test error: {type(e).__name__}: {e}")
            return False
    
    def create_key(self, name: str = None, limit_gb: int = 10) -> Dict[str, Any]:
        """Yangi kalit yaratish"""
        try:
            url = f"{self.base_url}/access-keys"
            data = {}
            
            if name:
                data['name'] = name
            
            if limit_gb > 0:
                data['limit'] = {'bytes': limit_gb * 1024 * 1024 * 1024}
            
            logger.info(f"Creating Outline key: {name}")
            logger.debug(f"Request URL: {url}")
            logger.debug(f"Request data: {data}")
            
            response = requests.post(
                url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30,
                verify=False
            )
            
            logger.info(f"Create key status: {response.status_code}")
            
            if response.status_code == 201:
                key_data = response.json()
                logger.info(f"✅ Outline key created successfully")
                logger.debug(f"Key data: {key_data}")
                return {
                    'success': True,
                    'data': key_data
                }
            else:
                error_msg = f"Outline API Error {response.status_code}: {response.text}"
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"Outline create key error: {type(e).__name__}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_keys(self) -> Dict[str, Any]:
        """Barcha kalitlarni olish"""
        try:
            url = f"{self.base_url}/access-keys"
            logger.debug(f"Get keys URL: {url}")
            
            response = requests.get(
                url,
                headers={'Content-Type': 'application/json'},
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"Outline API Error {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }