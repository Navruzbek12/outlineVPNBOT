# main.py
import asyncio
import logging
import sys
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot.config import Config
from bot.handlers import setup_routers
from bot.outline_api import OutlineAPI

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Health check endpoint
async def health_check(request):
    return web.Response(text="OK")

# Botni ishga tushirish funksiyasi
async def start_bot():
    """Botni ishga tushirish"""
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
        bot = Bot(
            token=Config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Avvalgi webhook ni o'chirish
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Bot webhook cleared")
        
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

async def start_background_tasks(app):
    """Background task sifatida botni ishga tushirish"""
    app['bot_task'] = asyncio.create_task(start_bot())

async def cleanup_background_tasks(app):
    """Background tasklarni tozalash"""
    if 'bot_task' in app:
        app['bot_task'].cancel()
        try:
            await app['bot_task']
        except asyncio.CancelledError:
            pass

def main():
    """Asosiy funksiya"""
    # Portni olish
    port = int(os.environ.get("PORT", 8080))
    
    # Aiohttp application yaratish
    app = web.Application()
    
    # Health check endpoint
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    # Botni background da ishga tushirish
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    
    logger.info(f"🚀 Starting web server on port {port}")
    
    # Serverni ishga tushirish
    web.run_app(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()
