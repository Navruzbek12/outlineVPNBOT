# check_imports.py
import sys
print(f"Python path: {sys.path}")

try:
    from bot.database import Database
    print("✅ Database import success")
    
    db = Database()
    print("✅ Database created")
    
except Exception as e:
    print(f"❌ Database error: {e}")

try:
    from bot.outline_api import OutlineAPI
    print("✅ OutlineAPI import success")
    
    outline = OutlineAPI()
    print("✅ OutlineAPI created")
    
except Exception as e:
    print(f"❌ OutlineAPI error: {e}")

try:
    from bot.config import Config
    print("✅ Config import success")
    
    print(f"Bot token exists: {bool(Config.BOT_TOKEN)}")
    
except Exception as e:
    print(f"❌ Config error: {e}")

try:
    from bot.handlers import setup_routers
    print("✅ Handlers import success")
except Exception as e:
    print(f"❌ Handlers error: {e}")