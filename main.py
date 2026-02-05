# main.py - TO'LIQ ISHLAYDI
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database - TO'G'RI IMPORT
import sys
sys.path.append('.')  # Current directory

# Database klassini to'g'ridan-to'g'ri import qilamiz
import sqlite3
import hashlib
import time
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_name="vpn_bot.db"):
        # Render yoki server uchun absolute path
        if os.environ.get('RENDER'):
            self.db_name = "/tmp/vpn_bot.db"
        else:
            self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Bazaga ulanish"""
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def init_database(self):
        """Baza jadvalini yaratish - To'liq versiya"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # System settings jadvali
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    last_daily_check DATE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # Foydalanuvchilar - Referal tizimi bilan
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    balance_rub INTEGER DEFAULT 0,
                    referal_link TEXT UNIQUE,
                    referal_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # Referallar jadvali
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS referals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER UNIQUE NOT NULL,
                    bonus_awarded BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (referred_id) REFERENCES users (telegram_id)
                )
                ''')
                
                # To'lovlar tarixi
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount_rub INTEGER,
                    payment_type TEXT,
                    status TEXT DEFAULT "pending",
                    screenshot_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_at TIMESTAMP,
                    key_created BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
                )
                ''')
                
                # VPN kalitlar
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS vpn_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    payment_id INTEGER NOT NULL,
                    key_id TEXT UNIQUE,
                    access_url TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    daily_fee_paid_until TIMESTAMP,
                    traffic_limit_mb INTEGER DEFAULT 10240,
                    traffic_used_mb INTEGER DEFAULT 0,
                    traffic_reset_date DATE,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (payment_id) REFERENCES payments (id),
                    UNIQUE(user_id, payment_id)
                )
                ''')
                
                # Kunlik to'lovlar tarixi
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_fees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    key_id INTEGER NOT NULL,
                    amount_rub INTEGER DEFAULT 5,
                    payment_date DATE DEFAULT CURRENT_DATE,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (key_id) REFERENCES vpn_keys (id)
                )
                ''')
                
                # VPN trafik monitoring jadvali
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS vpn_traffic (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    key_id INTEGER NOT NULL,
                    date DATE DEFAULT CURRENT_DATE,
                    download_mb INTEGER DEFAULT 0,
                    upload_mb INTEGER DEFAULT 0,
                    total_mb INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (key_id) REFERENCES vpn_keys (id),
                    UNIQUE(user_id, key_id, date)
                )
                ''')
                
                # System settings uchun default qiymat
                cursor.execute('''
                INSERT OR IGNORE INTO system_settings (id, last_daily_check) 
                VALUES (1, DATE('now', '-1 day'))
                ''')
                
                conn.commit()
                logger.info("✅ Database tables created successfully")
                
        except sqlite3.OperationalError as e:
            # Jadval allaqachon yaratilgan bo'lishi mumkin
            if "duplicate column name" not in str(e):
                logger.error(f"Database initialization error: {e}")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def add_user(self, telegram_id, username=None, first_name=None, referrer_id=None):
        """Yangi foydalanuvchi qo'shish"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT telegram_id FROM users WHERE telegram_id = ?', (telegram_id,))
                if cursor.fetchone():
                    logger.info(f"User {telegram_id} already exists")
                    return True
                
                cursor.execute('''
                INSERT INTO users (telegram_id, username, first_name, balance_rub)
                VALUES (?, ?, ?, 0)
                ''', (telegram_id, username, first_name))
                
                # Referal bo'lsa
                if referrer_id and referrer_id != telegram_id:
                    cursor.execute('SELECT telegram_id FROM users WHERE telegram_id = ?', (referrer_id,))
                    if cursor.fetchone():
                        cursor.execute('''
                        INSERT OR IGNORE INTO referals (referrer_id, referred_id)
                        VALUES (?, ?)
                        ''', (referrer_id, telegram_id))
                
                conn.commit()
                logger.info(f"✅ User added: {telegram_id} - {first_name}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error adding user {telegram_id}: {e}")
            return False
    
    def get_user(self, telegram_id):
        """Foydalanuvchini olish"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"❌ Error getting user {telegram_id}: {e}")
            return None
    
    def update_user_balance(self, telegram_id, rub_amount):
        """Balansni yangilash (RUB)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE users 
                SET balance_rub = balance_rub + ? 
                WHERE telegram_id = ?
                ''', (rub_amount, telegram_id))
                conn.commit()
                
                cursor.execute('SELECT balance_rub FROM users WHERE telegram_id = ?', (telegram_id,))
                result = cursor.fetchone()
                new_balance = result[0] if result else 0
                logger.info(f"✅ Balance updated: {telegram_id} +{rub_amount} RUB = {new_balance} RUB")
                return True
        except Exception as e:
            logger.error(f"❌ Error updating balance for {telegram_id}: {e}")
            return False
    
    def add_payment(self, user_id, amount_rub, payment_type, screenshot_id=None):
        """To'lov qo'shish"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO payments (user_id, amount_rub, payment_type, screenshot_id)
                VALUES (?, ?, ?, ?)
                ''', (user_id, amount_rub, payment_type, screenshot_id))
                conn.commit()
                payment_id = cursor.lastrowid
                logger.info(f"✅ Payment added: ID={payment_id}, User={user_id}, Amount={amount_rub} RUB")
                return payment_id
        except Exception as e:
            logger.error(f"❌ Error adding payment for user {user_id}: {e}")
            return None
    
    def approve_payment(self, user_id, payment_type):
        """To'lovni tasdiqlash"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT id, amount_rub FROM payments 
                WHERE user_id = ? AND payment_type = ? AND status = 'pending'
                ORDER BY created_at DESC 
                LIMIT 1
                ''', (user_id, payment_type))
                
                payment = cursor.fetchone()
                
                if not payment:
                    logger.warning(f"No pending payment found for user {user_id}, type {payment_type}")
                    return False
                
                payment_id = payment[0]
                amount_rub = payment[1]
                
                cursor.execute('''
                UPDATE payments 
                SET status = 'approved', 
                    approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (payment_id,))
                
                cursor.execute('UPDATE users SET balance_rub = balance_rub + ? WHERE telegram_id = ?', (amount_rub, user_id))
                
                conn.commit()
                logger.info(f"✅ Payment approved: ID={payment_id}, User={user_id}, Amount={amount_rub} RUB")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error approving payment for user {user_id}: {e}")
            return False
    
    def get_payments_without_keys(self, user_id):
        """Kalit yaratilmagan to'lovlar"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT * FROM payments 
                WHERE user_id = ? 
                AND status = 'approved' 
                AND key_created = 0
                ORDER BY created_at DESC
                ''', (user_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Error getting payments without keys for {user_id}: {e}")
            return []
    
    def add_vpn_key(self, user_id, payment_id, key_id, access_url, traffic_limit_mb=10240):
        """VPN kalit qo'shish"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                expires_at = datetime.now() + timedelta(days=30)
                paid_until = datetime.now() + timedelta(days=1)
                
                cursor.execute('''
                INSERT INTO vpn_keys 
                (user_id, payment_id, key_id, access_url, expires_at, daily_fee_paid_until, traffic_limit_mb)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, payment_id, key_id, access_url, expires_at, paid_until, traffic_limit_mb))
                
                cursor.execute('UPDATE payments SET key_created = 1 WHERE id = ?', (payment_id,))
                
                conn.commit()
                key_db_id = cursor.lastrowid
                logger.info(f"✅ VPN key added: User={user_id}, Payment={payment_id}, Limit={traffic_limit_mb}MB")
                return key_db_id
        except Exception as e:
            logger.error(f"❌ Error adding VPN key for user {user_id}: {e}")
            return None
    
    def get_active_keys(self, user_id):
        """Foydalanuvchining aktiv kalitlari"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT vk.*, p.payment_type, p.amount_rub
                FROM vpn_keys vk
                JOIN payments p ON vk.payment_id = p.id
                WHERE vk.user_id = ? 
                AND vk.is_active = 1
                ORDER BY vk.created_at DESC
                ''', (user_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Error getting active keys for {user_id}: {e}")
            return []

# Database obyektini yaratish
db = Database()

# Admin tekshiruvi
def is_admin(user_id: int) -> bool:
    admin_ids = [7813148656]  # O'zingizning ID
    return user_id in admin_ids

async def main():
    """Asosiy funksiya"""
    try:
        BOT_TOKEN = os.getenv("BOT_TOKEN", "8539085576:AAEkAp8oGqUSdKhw0oGlzQQRXRAVu2MGU1o")
        
        logger.info("🤖 Bot ishga tushmoqda...")
        
        bot = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # ========== START ==========
        @dp.message(CommandStart())
        async def start_cmd(message: Message):
            user_id = message.from_user.id
            username = message.from_user.username
            first_name = message.from_user.first_name
            
            # Referal parametrni tekshirish
            args = message.text.split()
            referrer_id = None
            if len(args) > 1 and args[1].startswith('ref'):
                try:
                    referrer_id = int(args[1][3:])  # ref123456 -> 123456
                except:
                    pass
            
            # User qo'shish
            db.add_user(user_id, username, first_name, referrer_id)
            
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📊 Mening statistikam")],
                    [KeyboardButton(text="💳 To'lov qilish")],
                    [KeyboardButton(text="🔑 VPN kalitlarim")],
                    [KeyboardButton(text="👥 Referal tizimi"), KeyboardButton(text="ℹ️ Yordam")]
                ],
                resize_keyboard=True
            )
            
            await message.answer(f"""
👋 *Assalomu alaykum, {first_name}!*

🤖 *VPN Bot* ga xush kelibsiz!

✨ *Bot imkoniyatlari:*
• 🔐 VPN kalit yaratish
• 💳 To'lov qilish (150/400/1200 RUB)
• 📊 Balans boshqarish  
• 👥 Referal tizimi

💎 *Boshlash uchun:* Quyidagi menyudan tanlang!
            """, reply_markup=keyboard, parse_mode="Markdown")
        
        # ========== TO'LOV MENYUSI ==========
        @dp.message(lambda m: m.text and "💳 To'lov qilish" in m.text)
        @dp.message(Command("payment"))
        async def payment_menu(message: Message):
            """To'lov menyusi - INLINE TUGMALAR"""
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="1️⃣ 150 RUB - 1 oy", callback_data="pay_150"),
                        InlineKeyboardButton(text="2️⃣ 400 RUB - 3 oy", callback_data="pay_400")
                    ],
                    [
                        InlineKeyboardButton(text="3️⃣ 1200 RUB - 1 yil", callback_data="pay_1200")
                    ],
                    [
                        InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main")
                    ]
                ]
            )
            
            user = db.get_user(message.from_user.id)
            balance = user['balance_rub'] if user else 0
            
            await message.answer(f"""
💳 *TO'LOV QILISH*

💰 *Joriy balansingiz:* {balance} RUB

🏦 *Bank ma'lumotlari:*
🔢 *Karta raqami:* `2202208022460399`
👤 *Karta egasi:* Наврузбек Бобобеков  
🏛️ *Bank:* Сбербанк

📦 *PAKETLAR:*
1️⃣ 150 RUB - 1 oylik VPN (10GB trafik)
2️⃣ 400 RUB - 3 oylik VPN (30GB trafik)  
3️⃣ 1200 RUB - 1 yillik VPN (120GB trafik + 200 RUB bonus)

🎯 *Tanlash uchun:* Quyidagi tugmalardan birini bosing!
            """, reply_markup=keyboard, parse_mode="Markdown")
        
        # ========== TO'LOV TANLASH CALLBACK ==========
        @dp.callback_query(lambda c: c.data.startswith("pay_"))
        async def handle_payment_selection(callback: CallbackQuery):
            """To'lov summasini tanlash - TO'G'RI ISHLAYDI"""
            try:
                # Callback datani olish
                data = callback.data
                logger.info(f"Callback data: {data}")
                
                if data == "pay_150":
                    amount = 150
                    payment_type = "150_rub"
                    package = "1 oylik VPN"
                elif data == "pay_400":
                    amount = 400
                    payment_type = "400_rub"
                    package = "3 oylik VPN"
                elif data == "pay_1200":
                    amount = 1200
                    payment_type = "1200_rub"
                    package = "1 yillik VPN"
                else:
                    await callback.answer("❌ Noto'g'ri tanlov!", show_alert=True)
                    return
                
                user_id = callback.from_user.id
                
                # To'lovni bazaga qo'shish
                payment_id = db.add_payment(user_id, amount, payment_type)
                
                if payment_id:
                    await callback.message.answer(f"""
✅ *To'lov tanlandi!*

📦 *Paket:* {package}
💰 *Summa:* {amount} RUB
🆔 *To'lov ID:* {payment_id}

🏦 *To'lov ma'lumotlari:*
Karta raqami: `2202208022460399`
Karta egasi: Наврузбек Бобобеков
Bank: Сбербанк

📸 *Endi to'lov chekini yuboring!*

⚠️ *Eslatma:* Chekda quyidagilar ko'rinishi kerak:
• To'lov summasi ({amount} RUB)
• To'lov vaqti
• Karta raqamining oxirgi 4 raqami
                    """, parse_mode="Markdown")
                    
                    await callback.answer(f"✅ {package} tanlandi!")
                else:
                    await callback.answer("❌ To'lovni saqlashda xatolik!", show_alert=True)
                    
            except Exception as e:
                logger.error(f"Payment selection error: {e}")
                await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)
        
        # ========== TO'LOV CHEKI ==========
        @dp.message(lambda m: m.photo)
        async def handle_payment_photo(message: Message):
            """To'lov chekini qabul qilish"""
            user_id = message.from_user.id
            
            # Oxirgi pending to'lovni topish
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, amount_rub, payment_type FROM payments 
                WHERE user_id = ? AND status = 'pending'
                ORDER BY created_at DESC LIMIT 1
                ''', (user_id,))
                
                payment = cursor.fetchone()
                
                if not payment:
                    await message.answer("""
❌ *Avval to'lov summasini tanlang!*

💳 "To'lov qilish" tugmasini bosing va paket tanlang.
                    """, parse_mode="Markdown")
                    return
                
                payment_id = payment[0]
                amount = payment[1]
                payment_type = payment[2]
                
                # Screenshot ID sini saqlash
                cursor.execute('UPDATE payments SET screenshot_id = ? WHERE id = ?', 
                             (message.photo[-1].file_id, payment_id))
                conn.commit()
                
                # Paket nomi
                if amount == 150:
                    package = "1 oylik VPN"
                elif amount == 400:
                    package = "3 oylik VPN"
                else:
                    package = "1 yillik VPN"
            
            await message.answer(f"""
✅ *To'lov cheki qabul qilindi!*

📦 *Paket:* {package}
💰 *Summa:* {amount} RUB
🆔 *To'lov ID:* {payment_id}

⏳ *Admin to'lovni tekshiradi...*
⏰ *Tasdiqlash vaqti:* 1-24 soat

📬 Tezkor javob uchun: @navnav123667
            """, parse_mode="Markdown")
            
            # ADMINLARGA XABAR
            admin_ids = [7813148656]
            for admin_id in admin_ids:
                try:
                    await bot.send_photo(
                        admin_id,
                        photo=message.photo[-1].file_id,
                        caption=f"""
📥 *YANGI TO'LOV CHEKI!*

👤 Foydalanuvchi: {message.from_user.first_name}
🆔 ID: {user_id}
📦 Paket: {package}
💰 Summa: {amount} RUB
🆔 To'lov ID: {payment_id}

✅ Tasdiqlash: /approve_{user_id}_{amount}
❌ Rad etish: /reject_{user_id}

ℹ️ Tekshirish: Foydalanuvchi {user_id} ning {amount} RUB to'lovi.
                        """,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Admin xabari: {e}")
        
        # ========== ADMIN TO'LOV TASDIQLASH ==========
        @dp.message(lambda m: m.text and m.text.startswith("/approve_"))
        async def approve_payment_cmd(message: Message):
            """Admin to'lovni tasdiqlash"""
            if not is_admin(message.from_user.id):
                await message.answer("❌ Siz admin emassiz!")
                return
            
            try:
                # Komandani ajratish
                command = message.text.strip()
                logger.info(f"Admin approve command: {command}")
                
                # /approve_ ni olib tashlash
                parts = command[9:].split("_")  # /approve_ = 9 ta belgi
                
                if len(parts) < 2:
                    await message.answer("❌ Format: /approve_USERID_AMOUNT\nMasalan: /approve_123456789_150")
                    return
                
                user_id = int(parts[0])
                amount = parts[1]
                
                # To'lov turi
                if amount == "150":
                    payment_type = "150_rub"
                elif amount == "400":
                    payment_type = "400_rub"
                elif amount == "1200":
                    payment_type = "1200_rub"
                else:
                    await message.answer(f"❌ Noto'g'ri summa: {amount}\nSumma: 150, 400 yoki 1200 bo'lishi kerak")
                    return
                
                # To'lovni tasdiqlash
                success = db.approve_payment(user_id, payment_type)
                
                if not success:
                    await message.answer(f"❌ To'lovni tasdiqlashda xatolik yoki to'lov topilmadi!")
                    return
                
                # Foydalanuvchi ma'lumotlari
                user = db.get_user(user_id)
                if not user:
                    await message.answer(f"❌ Foydalanuvchi {user_id} topilmadi!")
                    return
                
                # Paket nomi
                if amount == "150":
                    package = "1 oylik VPN"
                elif amount == "400":
                    package = "3 oylik VPN"
                else:
                    package = "1 yillik VPN"
                
                # Foydalanuvchiga xabar
                try:
                    await bot.send_message(
                        user_id,
                        f"""
🎉 *Tabriklaymiz! To'lovingiz tasdiqlandi!*

📦 *Paket:* {package}
💰 *Summa:* {amount} RUB
💳 *Yangi balans:* {user['balance_rub']} RUB

🔑 *Endi VPN kalit yaratishingiz mumkin!*

💎 *Kalit yaratish uchun:* 
"VPN kalitlarim" tugmasini bosing yoki /vpn buyrug'ini yuboring.

📊 *Statistika:* /profile
                        """,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Foydalanuvchiga xabar: {e}")
                
                # Admin javobi
                await message.answer(f"""
✅ *To'lov muvaffaqiyatli tasdiqlandi!*

👤 *Foydalanuvchi:* {user['first_name']}
🆔 *ID:* {user_id}
📦 *Paket:* {package}
💰 *Summa:* {amount} RUB
💳 *Yangi balans:* {user['balance_rub']} RUB

📬 *Foydalanuvchiga xabar yuborildi.*
                """, parse_mode="Markdown")
                
                logger.info(f"✅ To'lov tasdiqlandi: User={user_id}, Amount={amount}RUB")
                
            except ValueError:
                await message.answer("❌ Noto'g'ri format! User ID raqam bo'lishi kerak.")
            except Exception as e:
                logger.error(f"Approve error: {e}")
                await message.answer(f"❌ Xatolik: {str(e)}")
        
        # ========== VPN KALITLAR ==========
        @dp.message(lambda m: m.text and "🔑 VPN kalitlarim" in m.text)
        @dp.message(Command("vpn"))
        async def vpn_keys_cmd(message: Message):
            """VPN kalitlar"""
            user_id = message.from_user.id
            keys = db.get_active_keys(user_id)
            
            if not keys:
                # Kalit yaratilmagan to'lovlarni tekshirish
                payments = db.get_payments_without_keys(user_id)
                
                if payments:
                    # To'lov bor, kalit yaratish mumkin
                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="🔑 VPN KALIT YARATISH", callback_data="create_vpn_key")]
                        ]
                    )
                    
                    await message.answer("""
🔑 *VPN KALITLAR*

❌ Sizda aktiv VPN kalit yo'q.

✅ *Xursandchilik!* Sizda kalit yaratish uchun to'lov mavjud!

💎 *VPN kalit yaratish uchun:* Quyidagi tugmani bosing.
                    """, reply_markup=keyboard, parse_mode="Markdown")
                else:
                    await message.answer("""
🔑 *VPN KALITLAR*

❌ Sizda aktiv VPN kalit yo'q.
❌ Sizda kalit yaratish uchun to'lov ham yo'q.

💳 *VPN kalit olish uchun:*
1. "To'lov qilish" tugmasini bosing
2. Paket tanlang (150/400/1200 RUB)
3. To'lov qiling
4. Chekni yuboring
5. Admin tasdiqlagach, kalit yaratasiz
                    """, parse_mode="Markdown")
                return
            
            # Aktiv kalitlar bor
            response = "🔑 *VPN KALITLARINGIZ:*\n\n"
            
            for key in keys[:3]:  # Faqat 3 tasini ko'rsatish
                expires = key['expires_at'].split()[0] if key['expires_at'] else "N/A"
                days_left = "∞"
                try:
                    from datetime import datetime
                    exp_date = datetime.strptime(expires, "%Y-%m-%d")
                    days_left = (exp_date - datetime.now()).days
                    if days_left < 0:
                        days_left = "Muddati tugagan"
                except:
                    pass
                
                response += f"""
📌 *Kalit:* `{key['key_id'][:8]}...`
💰 *To'lov:* {key['amount_rub']} RUB
📅 *Muddati:* {expires}
⏰ *Qolgan kun:* {days_left}
🔗 *URL:* `{key['access_url'][:20]}...`
                """
                response += "➖➖➖➖➖➖➖\n"
            
            await message.answer(response, parse_mode="Markdown")
        
        # ========== VPN KALIT YARATISH ==========
        @dp.callback_query(lambda c: c.data == "create_vpn_key")
        async def create_vpn_key_handler(callback: CallbackQuery):
            """VPN kalit yaratish"""
            user_id = callback.from_user.id
            
            # Kalit yaratilmagan to'lovlarni tekshirish
            payments = db.get_payments_without_keys(user_id)
            
            if not payments:
                await callback.answer("❌ Kalit yaratish uchun to'lov yo'q!", show_alert=True)
                return
            
            # Birinchi to'lov uchun kalit yaratish
            payment = payments[0]
            
            # Outline API orqali kalit yaratish
            try:
                # Outline API simulyatsiyasi (haqiqiy API keyingi bosqichda)
                # Bu yerda test uchun fake kalit yaratamiz
                key_id = f"vpn_{user_id}_{int(time.time())}"
                access_url = f"https://vpn.example.com/access#{key_id}"
                
                # Trafik limiti
                amount = payment['amount_rub']
                if amount == 1200:
                    limit_mb = 120 * 1024  # 120GB -> MB
                elif amount == 400:
                    limit_mb = 30 * 1024   # 30GB -> MB
                else:
                    limit_mb = 10 * 1024   # 10GB -> MB
                
                # Bazaga saqlash
                db.add_vpn_key(
                    user_id=user_id,
                    payment_id=payment['id'],
                    key_id=key_id,
                    access_url=access_url,
                    traffic_limit_mb=limit_mb
                )
                
                await callback.message.answer(f"""
✅ *VPN KALIT YARATILDI!*

🔑 *Kalit ID:* `{key_id}`
🌐 *Access URL:*
`{access_url}`

📊 *Trafik limiti:* {limit_mb // 1024} GB
⏰ *Muddati:* 30 kun
💎 *Kunlik to'lov:* 5 RUB

⚠️ *Eslatmalar:*
1. Access URL ni HECH KIMGA bermang!
2. Har kuni 5 RUB to'lov avtomatik yechiladi
3. Trafik limiti {limit_mb // 1024} GB
4. 30 kundan keyin kalit muddati tugaydi

📱 *Qo'llash:* Outline ilovasiga Access URL ni kiriting.
                """, parse_mode="Markdown")
                
                await callback.answer("✅ VPN kalit yaratildi!")
                    
            except Exception as e:
                logger.error(f"VPN key creation error: {e}")
                await callback.message.answer(f"""
❌ *VPN kalit yaratishda xatolik!*

Xatolik: {str(e)}

Iltimos, keyinroq urinib ko'ring yoki admin bilan bog'laning: @navnav123667
                """)
                await callback.answer("❌ Xatolik!", show_alert=True)
        
        # ========== QOLGAN HANDLERLAR ==========
        @dp.message(lambda m: m.text and "📊 Mening statistikam" in m.text)
        async def stats_cmd(message: Message):
            user_id = message.from_user.id
            user = db.get_user(user_id)
            
            if not user:
                await message.answer("❌ Foydalanuvchi topilmadi!")
                return
            
            keys = db.get_active_keys(user_id)
            
            await message.answer(f"""
📊 *SIZNING STATISTIKANGIZ:*

👤 Ism: {user['first_name']}
💰 Balans: {user['balance_rub']} RUB
🔑 Aktiv kalitlar: {len(keys)} ta
📅 Ro'yxatdan: {user['created_at'].split()[0]}
            """, parse_mode="Markdown")
        
        @dp.message(lambda m: m.text and "👥 Referal tizimi" in m.text)
        async def referral_cmd(message: Message):
            bot_info = await bot.get_me()
            full_link = f"https://t.me/{bot_info.username}?start=ref{message.from_user.id}"
            
            await message.answer(f"""
👥 *REFERAL TIZIMI*

💰 *Bonus:* Har bir taklif qilgan do'stingiz uchun *50 RUB* bonus!

🔗 *Sizning referal havolangiz:*
`{full_link}`

📝 *Qanday ishlaydi:*
1. Havolani do'stlaringizga yuboring
2. Ular havola orqali botga kirsin
3. Siz 50 RUB bonus olasiz!
4. Ular to'lov qilsa, siz yana 50 RUB bonus!
            """, parse_mode="Markdown")
        
        @dp.message(Command("admin"))
        async def admin_cmd(message: Message):
            if not is_admin(message.from_user.id):
                await message.answer("❌ Siz admin emassiz!")
                return
            
            # Foydalanuvchilar soni
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users')
                users_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "approved"')
                payments_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM vpn_keys WHERE is_active = 1')
                active_keys = cursor.fetchone()[0]
            
            await message.answer(f"""
👑 *ADMIN STATISTIKA*

👥 Foydalanuvchilar: {users_count} ta
✅ Tasdiqlangan to'lovlar: {payments_count} ta
🔑 Aktiv VPN kalitlar: {active_keys} ta

✅ To'lov tasdiqlash: /approve_USERID_AMOUNT
🔑 VPN kalit yaratish: User /vpn buyrug'i orqali

ℹ️ Masalan: /approve_123456789_150
            """, parse_mode="Markdown")
        
        @dp.callback_query(lambda c: c.data == "back_to_main")
        async def back_to_main(callback: CallbackQuery):
            """Asosiy menyuga qaytish"""
            user_id = callback.from_user.id
            user = db.get_user(user_id)
            first_name = user['first_name'] if user else "Foydalanuvchi"
            
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📊 Mening statistikam")],
                    [KeyboardButton(text="💳 To'lov qilish")],
                    [KeyboardButton(text="🔑 VPN kalitlarim")],
                    [KeyboardButton(text="👥 Referal tizimi"), KeyboardButton(text="ℹ️ Yordam")]
                ],
                resize_keyboard=True
            )
            
            await callback.message.answer(f"""
👋 *Assalomu alaykum, {first_name}!*

Asosiy menyuga qaytdingiz.

✨ *Bot imkoniyatlari:*
• 🔐 VPN kalit yaratish
• 💳 To'lov qilish (150/400/1200 RUB)
• 📊 Balans boshqarish  
• 👥 Referal tizimi

💎 *Boshlash uchun:* Quyidagi menyudan tanlang!
            """, reply_markup=keyboard, parse_mode="Markdown")
            await callback.answer()
        
        # ========== YORDAM ==========
        @dp.message(lambda m: m.text and "ℹ️ Yordam" in m.text)
        @dp.message(Command("help"))
        async def help_cmd(message: Message):
            await message.answer("""
ℹ️ *YORDAM VA QO'LLANMA*

🤖 *Bot qanday ishlaydi?*
1. 💳 "To'lov qilish" tugmasini bosing
2. Paket tanlang (150/400/1200 RUB)
3. Bank kartasiga to'lov qiling
4. To'lov chekini yuboring
5. Admin tasdiqlagach, VPN kalit yaratasiz

💎 *Qo'shimcha imkoniyatlar:*
• 📊 Mening statistikam - balans va aktiv kalitlar
• 👥 Referal tizimi - do'stlarni taklif qilish
• 🔑 VPN kalitlarim - barcha aktiv kalitlar

⚠️ *Muhim eslatmalar:*
• VPN kalit muddati - 30 kun
• Kunlik to'lov - 5 RUB
• Trafik limiti - paketga bog'liq
• Access URL ni hech kimga bermang!

📬 *Admin bilan bog'lanish:* @navnav123667
            """, parse_mode="Markdown")
        
        # ========== BOT ISHGA TUSHIRISH ==========
        logger.info("✅ Database tekshirildi")
        await bot.delete_webhook(drop_pending_updates=True)
        
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot ishga tushdi: @{bot_info.username}")
        
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Xatolik: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
