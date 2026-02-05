# main.py - TO'G'RILANGAN VERSIYA
import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def main():
    """Asosiy funksiya - FAQQAT BOT"""
    try:
        # Bot tokenini o'qish
        BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan!")
        
        logger.info("🤖 Bot ishga tushmoqda...")
        
        # Botni yaratish
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Avvalgi webhook ni o'chirish
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Bot webhook cleared")
        
        # Dispatcher yaratish
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Handlerni import qilish
        logger.info("📦 Handlerni yuklash...")
        
        from bot.handlers.start import router as start_router
        from bot.handlers.admin import router as admin_router
        from bot.handlers.payment import router as payment_router
        from bot.handlers.profile import router as profile_router
        from bot.handlers.vpn import router as vpn_router
        from bot.handlers.referral import router as referral_router
        
        # Routerlarni qo'shish
        dp.include_router(start_router)
        dp.include_router(admin_router)
        dp.include_router(payment_router)
        dp.include_router(profile_router)
        dp.include_router(vpn_router)
        dp.include_router(referral_router)
        
        logger.info("✅ Barcha handlerni yuklandi")
        
        # Database test
        from bot.database import Database
        db = Database()
        logger.info("✅ Database yaratildi")
        
        # Outline test (agar sozlamalar bor bo'lsa)
        try:
            from bot.outline_api import OutlineAPI
            outline_api = OutlineAPI()
            if outline_api.test_connection():
                logger.info("✅ Outline serveriga ulanildi")
            else:
                logger.warning("⚠️ Outline serveriga ulanib bo'lmadi")
        except Exception as e:
            logger.warning(f"⚠️ Outline test xatosi: {e}")
        
        # Bot haqida ma'lumot
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot ishga tushdi: @{bot_info.username}")
        logger.info(f"🆔 Bot ID: {bot_info.id}")
        
        # Pollingni boshlash
        logger.info("🔄 Polling boshlandi...")
        await dp.start_polling(bot)
        
    except ValueError as e:
        logger.error(f"❌ Konfiguratsiya xatosi: {e}")
        logger.info("ℹ️ .env faylini tekshiring yoki muhit o'zgaruvchilarini o'rnating")
    except KeyboardInterrupt:
        logger.info("🛑 Bot foydalanuvchi tomonidan to'xtatildi")
    except Exception as e:
        logger.error(f"❌ Botda kutilmagan xatolik: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        logger.info("👋 Bot dasturi tugadi")

def run_bot():
    """Botni ishga tushirish funksiyasi"""
    # FAQAT BOTNI ISHGA TUSHIRISH
    asyncio.run(main())

if __name__ == "__main__":
    run_bot()
