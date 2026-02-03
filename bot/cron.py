# bot/cron.py - Kunlik tekshiruv
import schedule
import time
import logging
from bot.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def daily_check():
    """Har kuni 00:00 da ishlaydi"""
    logger.info("🔄 Kunlik to'lovlarni tekshirish...")
    db = Database()
    db.check_and_deduct_daily()
    logger.info("✅ Kunlik tekshiruv tugadi")

def run_cron():
    """Cron job ni ishga tushirish"""
    # Har kuni 00:00 da
    schedule.every().day.at("00:00").do(daily_check)
    
    # Test uchun har 10 minutda
    # schedule.every(10).minutes.do(daily_check)
    
    logger.info("⏰ Cron job ishga tushdi")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Har minut tekshirish

if __name__ == "__main__":
    run_cron()