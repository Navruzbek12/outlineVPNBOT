# bot/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot token
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Outline API - TO'G'RI O'QISH
    OUTLINE_SERVER_URL = os.getenv('OUTLINE_SERVER_URL', '')
    OUTLINE_API_PORT = os.getenv('OUTLINE_API_PORT', '43437')
    OUTLINE_API_SECRET = os.getenv('OUTLINE_API_SECRET', '')
    
    # To'lov karta ma'lumotlari
    PAYMENT_CARD_NUMBER = os.getenv('PAYMENT_CARD_NUMBER', '')
    PAYMENT_CARD_NAME = os.getenv('PAYMENT_CARD_NAME', '')
    PAYMENT_BANK = os.getenv('PAYMENT_BANK', '')
    
    
    admin_ids_str = os.getenv("ADMIN_IDS", "7813148656")
    ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip().isdigit()]
    ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "7813148656"))
    
    # Sozlamalar
    REFERRAL_BONUS_DAYS = int(os.getenv('REFERRAL_BONUS_DAYS', '7'))
    DEFAULT_KEY_LIMIT_GB = int(os.getenv('DEFAULT_KEY_LIMIT_GB', '10'))
    FREE_TRIAL_DAYS = int(os.getenv('FREE_TRIAL_DAYS', '3'))
    
    # To'lov narxlari
    PRICE_1_MONTH = int(os.getenv('PRICE_1_MONTH', '150'))
    BONUS_DAYS_1_MONTH = int(os.getenv('BONUS_DAYS_1_MONTH', '30'))
    
    PRICE_3_MONTH = int(os.getenv('PRICE_3_MONTH', '400'))
    BONUS_DAYS_3_MONTH = int(os.getenv('BONUS_DAYS_3_MONTH', '90'))
    
    PRICE_1_YEAR = int(os.getenv('PRICE_1_YEAR', '1200'))
    BONUS_DAYS_1_YEAR = int(os.getenv('BONUS_DAYS_1_YEAR', '365'))
    
    # Database
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'vpn_bot.db')
    PORT = int(os.getenv("PORT", 8080))  # <-- Port qo'shildi

    DAILY_FEE_RUB = int(os.getenv('DAILY_FEE_RUB', '5'))  # Kunlik to'lov
    MIN_BALANCE_FOR_KEY = int(os.getenv('MIN_BALANCE_FOR_KEY', '5'))  # Kalit uchun minimal balans
    KEY_EXPIRE_DAYS = int(os.getenv('KEY_EXPIRE_DAYS', '30'))  # Kalit muddati
    
    @classmethod
    def validate(cls):
        """Sozlamalarni tekshirish"""
        missing = []
        
        if not cls.BOT_TOKEN:
            missing.append("BOT_TOKEN")
        if not cls.OUTLINE_SERVER_URL:
            missing.append("OUTLINE_SERVER_URL")
        if not cls.OUTLINE_API_SECRET:
            missing.append("OUTLINE_API_SECRET")
        
        if missing:
            raise ValueError(f"Quyidagi sozlamalar .env faylida mavjud emas: {', '.join(missing)}")
