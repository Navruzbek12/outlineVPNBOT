# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import Config
from bot.handlers import setup_routers
from bot.outline_api import OutlineAPI

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Asosiy funksiya"""
    try:
        # Konfiguratsiyani tekshirish
        Config.validate()
        logger.info("✅ Konfiguratsiya muvaffaqiyatli yuklandi")
        
        # Database yaratish
        from bot.database import Database
        db = Database()
        logger.info("✅ Database yaratildi")
        
        # Outline API ulanishini test qilish
        outline_api = OutlineAPI()
        if outline_api.test_connection():
            logger.info("✅ Outline serveriga muvaffaqiyatli ulanildi")
        else:
            logger.warning("⚠️ Outline serveriga ulanib bo'lmadi!")
        
        # Botni yaratish
        bot = Bot(token=Config.BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Routerlarni qo'shish
        dp.include_router(setup_routers())
        
        # Bot haqida ma'lumot
        bot_info = await bot.get_me()
        logger.info(f"🤖 Bot ishga tushdi: @{bot_info.username}")
        
        # Pollingni boshlash
        await dp.start_polling(bot)
        
    except ValueError as e:
        logger.error(f"❌ Konfiguratsiya xatosi: {e}")
    except Exception as e:
        logger.error(f"❌ Botda xatolik: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("🛑 Bot to'xtatildi")

if __name__ == "__main__":
    asyncio.run(main())