# bot/database.py - TO'G'RILANGAN VERSIYA
import sqlite3
import logging
from datetime import datetime, timedelta
import os
import hashlib
import time

logger = logging.getLogger(__name__)

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
                
                # System settings uchun default qiymat
                cursor.execute('''
                INSERT OR IGNORE INTO system_settings (id, last_daily_check) 
                VALUES (1, DATE('now', '-1 day'))
                ''')
                
                conn.commit()
                logger.info("✅ Database tables created successfully")
                
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def check_and_deduct_daily(self):
        """Har kuni 5 RUB avtomatik yechish"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                today = datetime.now().date().isoformat()
                
                cursor.execute("SELECT last_daily_check FROM system_settings WHERE id = 1")
                result = cursor.fetchone()
                last_check = result[0] if result else None
                
                if last_check != today:
                    logger.info(f"🔄 Kunlik to'lovlarni tekshirish: {today}")
                    
                    cursor.execute('''
                    SELECT DISTINCT u.telegram_id, u.balance_rub, vk.id as key_id
                    FROM users u
                    JOIN vpn_keys vk ON u.telegram_id = vk.user_id
                    WHERE vk.is_active = 1 
                    AND (vk.daily_fee_paid_until IS NULL OR vk.daily_fee_paid_until < DATE('now'))
                    ''')
                    
                    users_with_keys = cursor.fetchall()
                    
                    for user_row in users_with_keys:
                        user_id = user_row[0]
                        balance = user_row[1]
                        key_id = user_row[2]
                        
                        if balance >= 5:
                            cursor.execute('UPDATE users SET balance_rub = balance_rub - 5 WHERE telegram_id = ?', (user_id,))
                            cursor.execute('INSERT INTO daily_fees (user_id, key_id, amount_rub) VALUES (?, ?, 5)', (user_id, key_id))
                            cursor.execute('UPDATE vpn_keys SET daily_fee_paid_until = DATE("now", "+1 day") WHERE id = ?', (key_id,))
                            logger.info(f"✅ Kunlik 5 RUB yechildi: User={user_id}, Balance={balance-5}")
                        else:
                            cursor.execute('UPDATE vpn_keys SET is_active = 0 WHERE id = ?', (key_id,))
                            logger.warning(f"⚠️ Balans yetmadi, kalit o'chirildi: User={user_id}")
                    
                    cursor.execute('UPDATE system_settings SET last_daily_check = DATE("now"), updated_at = CURRENT_TIMESTAMP WHERE id = 1')
                    conn.commit()
                    logger.info("✅ Kunlik to'lovlar tekshirildi")
                    
        except Exception as e:
            logger.error(f"❌ Kunlik to'lov tekshirishda xatolik: {e}")
    
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
                new_balance = cursor.fetchone()[0]
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
    
    def add_vpn_key(self, user_id, payment_id, key_id, access_url):
        """VPN kalit qo'shish"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                expires_at = datetime.now() + timedelta(days=30)
                paid_until = datetime.now() + timedelta(days=1)
                
                cursor.execute('''
                INSERT INTO vpn_keys 
                (user_id, payment_id, key_id, access_url, expires_at, daily_fee_paid_until)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, payment_id, key_id, access_url, expires_at, paid_until))
                
                cursor.execute('UPDATE payments SET key_created = 1 WHERE id = ?', (payment_id,))
                
                conn.commit()
                key_db_id = cursor.lastrowid
                logger.info(f"✅ VPN key added: User={user_id}, Payment={payment_id}")
                return key_db_id
        except Exception as e:
            logger.error(f"❌ Error adding VPN key for user {user_id}: {e}")
            return None
    
    def get_user_stats(self, user_id):
        """Foydalanuvchi statistikasi"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,))
                user_row = cursor.fetchone()
                if not user_row:
                    return None
                
                user = dict(user_row)
                active_keys = self.get_active_keys(user_id)
                
                cursor.execute('SELECT COUNT(*) as count, COALESCE(SUM(amount_rub), 0) as total FROM payments WHERE user_id = ? AND status = "approved"', (user_id,))
                payments_row = cursor.fetchone()
                payments = dict(payments_row) if payments_row else {'count': 0, 'total': 0}
                
                cursor.execute('''
                SELECT COALESCE(SUM(amount_rub), 0) as total 
                FROM daily_fees 
                WHERE user_id = ? 
                AND payment_date >= DATE('now', '-7 days')
                ''', (user_id,))
                daily_fees_row = cursor.fetchone()
                daily_fees = daily_fees_row[0] if daily_fees_row else 0
                
                stats = {
                    'user': user,
                    'balance_rub': user.get('balance_rub', 0),
                    'active_keys': len(active_keys),
                    'total_payments': payments.get('count', 0),
                    'total_amount': payments.get('total', 0),
                    'daily_fees_7days': daily_fees,
                    'created_at': user.get('created_at')
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Error getting stats for user {user_id}: {e}")
            return None
    
    def generate_referal_link(self, user_id):
        """Referal link yaratish"""
        hash_input = f"{user_id}_{time.time()}"
        referal_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        referal_link = f"ref_{referal_hash}"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                UPDATE users 
                SET referal_link = ? 
                WHERE telegram_id = ?
                ''', (referal_link, user_id))
                
                conn.commit()
                return referal_link
                
        except Exception as e:
            logger.error(f"❌ Error generating referal link: {e}")
            return None
    
    def get_referal_info(self, user_id):
        """Referal ma'lumotlari"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT referal_link, referal_count FROM users WHERE telegram_id = ?', (user_id,))
                user_info = cursor.fetchone()
                
                cursor.execute('''
                SELECT r.referred_id, u.first_name, u.username, r.created_at
                FROM referals r
                JOIN users u ON r.referred_id = u.telegram_id
                WHERE r.referrer_id = ?
                ORDER BY r.created_at DESC
                ''', (user_id,))
                referals = cursor.fetchall()
                
                return {
                    'referal_link': user_info[0] if user_info else None,
                    'referal_count': user_info[1] if user_info else 0,
                    'referals': [dict(row) for row in referals]
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting referal info: {e}")
            return None
    
    def check_referal_code(self, referal_code):
        """Referal kodni tekshirish"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT telegram_id FROM users WHERE referal_link = ?', (referal_code,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ Error checking referal code: {e}")
            return None

