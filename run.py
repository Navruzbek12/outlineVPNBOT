
import asyncio
import logging
import os
from dotenv import load_dotenv

# .env ni yuklash
load_dotenv()

# Importlar
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Outline API
try:
    from bot.outline_api import OutlineAPI
    from bot.database import Database
    
    # Sozlamalarni o'qish
    API_URL = os.getenv('OUTLINE_API_URL', '').strip()
    API_SECRET = os.getenv('OUTLINE_API_SECRET', '').strip()
    
    # Database yaratish
    db = Database()
    
    if API_URL and API_SECRET:
        print("\n" + "="*50)
        print("🔗 Outline API sozlanmoqda...")
        print("="*50)
        
        outline_api = OutlineAPI(api_url=API_URL, api_secret=API_SECRET)
        
        # Test connection
        print("🔄 Serverga ulanilmoqda...")
        if outline_api.test_connection():
            print("✅ Outline serverga muvaffaqiyatli ulanildi!")
            OUTLINE_AVAILABLE = True
            
            # Server info olish
            server_info = outline_api.get_server_info()
            if server_info['success']:
                info = server_info['data']
                print(f"📊 Server ma'lumotlari:")
                print(f"   Nomi: {info.get('name', 'Outline Server')}")
                print(f"   Port: {info.get('portForNewAccessKeys', 'N/A')}")
                print(f"   Versiya: {info.get('version', 'N/A')}")
        else:
            print("❌ Outline serverga ulanib bo'lmadi!")
            OUTLINE_AVAILABLE = False
    else:
        print("\n⚠️ Outline API sozlanmagan")
        OUTLINE_AVAILABLE = False
        outline_api = None
        
except ImportError as e:
    print(f"\n❌ Import xatosi: {e}")
    OUTLINE_AVAILABLE = False
    outline_api = None
    db = None
except Exception as e:
    print(f"\n❌ Xatolik: {e}")
    OUTLINE_AVAILABLE = False
    outline_api = None
    db = None

async def main():
    """Asosiy funksiya"""
    try:
        # Token ni o'qiymiz
        TOKEN = os.getenv('BOT_TOKEN')
        if not TOKEN:
            print("❌ BOT_TOKEN .env faylida mavjud emas!")
            return
        
        print("\n" + "="*50)
        print("🤖 Outline VPN Bot ishga tushmoqda...")
        print("="*50)
        
        bot = Bot(token=TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Import qilish (circular importdan qochish uchun)
        from bot.handlers.start import router as start_router
        from bot.handlers.payment import router as payment_router
        from bot.handlers.keys import router as keys_router
        
        # Routerlarni qo'shish
        dp.include_router(start_router)
        dp.include_router(payment_router)
        dp.include_router(keys_router)
        
        # Bot haqida ma'lumot
        bot_info = await bot.get_me()
        logger.info(f"Bot ishga tushdi: @{bot_info.username}")
        
        print("\n" + "="*50)
        print(f"✅ Bot muvaffaqiyatli ishga tushdi!")
        print(f"🤖 Username: @{bot_info.username}")
        print(f"👤 Name: {bot_info.full_name}")
        print(f"🆔 ID: {bot_info.id}")
        print("="*50)
        print(f"\n📊 Outline server holati: {'🟢 FAOL' if OUTLINE_AVAILABLE else '🔴 NOFAOL'}")
        print(f"💳 To'lov tizimi: ✅ Faol")
        print(f"📱 Botga boring: https://t.me/{bot_info.username}")
        print("\n📋 Mavjud xizmatlar:")
        print("  • VPN kalit olish")
        print("  • To'lov qilish (manual)")
        print("  • Balansni ko'rish")
        print("  • Referal tizimi")
        print("\n🛑 Botni to'xtatish uchun Ctrl+C ni bosing...")
        
        # Pollingni boshlash
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Botda xatolik: {e}")
        print(f"❌ Xatolik: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("Bot to'xtatildi")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot to'xtatildi!")