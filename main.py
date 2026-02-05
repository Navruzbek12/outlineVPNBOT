# main.py - ESKI SISTEMANIZ UCHUN
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database
from bot.database import Database
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
            
            # User qo'shish
            db.add_user(user_id, username, first_name)
            
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📊 Mening statistikam")],
                    [KeyboardButton(text="💳 To'lov qilish")],
                    [KeyboardButton(text="🔑 VPN kalitlarim")],
                    [KeyboardButton(text="👥 Referal tizimi")]
                ],
                resize_keyboard=True
            )
            
            await message.answer(f"""
👋 Salom {first_name}!

🤖 VPN Botga xush kelibsiz!

💎 *Imkoniyatlar:*
• 🔐 VPN kalit yaratish
• 💳 To'lov qilish (150/400/1200 RUB)
• 📊 Balans boshqarish
• 👥 Referal tizimi

📊 *Statistika:* /stats
💳 *To'lov:* /payment
🔑 *VPN:* /vpn
👑 *Admin:* /admin
            """, reply_markup=keyboard, parse_mode="Markdown")
        
        # ========== TO'LOV MENYUSI ==========
        @dp.message(lambda m: m.text and "💳 To'lov qilish" in m.text)
        @dp.message(Command("payment"))
        async def payment_menu(message: Message):
            """ESKI SISTEMA: To'lov menyusi"""
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="1️⃣ 1 oylik - 150 RUB", callback_data="pay_150")],
                    [InlineKeyboardButton(text="2️⃣ 3 oylik - 400 RUB", callback_data="pay_400")],
                    [InlineKeyboardButton(text="3️⃣ 1 yillik - 1200 RUB", callback_data="pay_1200")]
                ]
            )
            
            await message.answer(f"""
💳 *TO'LOV QILISH*

🏦 *Bank ma'lumotlari:*
🔢 Karta raqami: `2202208022460399`
👤 Karta egasi: Наврузбек Бобобеков
🏛️ Bank: Сбербанк

📦 *Paketlar:*
1️⃣ 150 RUB - 1 oylik VPN (10GB trafik)
2️⃣ 400 RUB - 3 oylik VPN (30GB trafik)  
3️⃣ 1200 RUB - 1 yillik VPN (120GB trafik + 200 RUB bonus)

📸 *Qadamlar:*
1. Paketni tanlang
2. Kartaga to'lov qiling
3. Chek rasmini yuboring
4. Admin tasdiqlaydi
5. Kalit olasiz
            """, reply_markup=keyboard, parse_mode="Markdown")
        
        # ========== TO'LOV TANLASH ==========
        @dp.callback_query(lambda c: c.data.startswith("pay_"))
        async def payment_select(callback):
            """To'lov summasini tanlash"""
            amount = callback.data.replace("pay_", "")
            amounts = {"150": 150, "400": 400, "1200": 1200}
            
            if amount not in amounts:
                await callback.answer("❌ Noto'g'ri summa!")
                return
            
            user_id = callback.from_user.id
            payment_type = f"{amount}_rub"
            
            # To'lovni bazaga qo'shish
            payment_id = db.add_payment(user_id, amounts[amount], payment_type)
            
            if payment_id:
                await callback.message.answer(f"""
✅ *To'lov saqlandi!*

💰 *Summa:* {amount} RUB

📸 Endi to'lov chekini (screenshot) yuboring.

🏦 *Karta ma'lumotlari:*
2202208022460399
Наврузбек Бобобеков
Сбербанк

⚠️ *Eslatma:* Chekda summa va vaqt ko'rinishi kerak!
                """, parse_mode="Markdown")
                await callback.answer()
            else:
                await callback.answer("❌ Xatolik!", show_alert=True)
        
        # ========== TO'LOV CHEKI ==========
        @dp.message(lambda m: m.photo)
        async def handle_payment_screenshot(message: Message):
            """ESKI SISTEMA: To'lov chekini qabul qilish"""
            user_id = message.from_user.id
            
            # Oxirgi to'lovni topish
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, amount_rub FROM payments 
                WHERE user_id = ? AND status = 'pending'
                ORDER BY created_at DESC LIMIT 1
                ''', (user_id,))
                
                payment = cursor.fetchone()
                
                if not payment:
                    await message.answer("❌ Avval to'lov summasini tanlang!")
                    return
                
                payment_id = payment[0]
                amount = payment[1]
                
                # Screenshot ID sini saqlash
                cursor.execute('UPDATE payments SET screenshot_id = ? WHERE id = ?', 
                             (message.photo[-1].file_id, payment_id))
                conn.commit()
            
            await message.answer("""
✅ *To'lov cheki qabul qilindi!*

⏳ Admin to'lovni tekshirgach, balansingizga pul qo'shiladi.

⏰ *Tasdiqlash vaqti:* 1-24 soat

ℹ️ Tezkor javob uchun: @navnav123667
            """, parse_mode="Markdown")
            
            # ADMINLARGA XABAR
            admin_ids = [7813148656]
            for admin_id in admin_ids:
                try:
                    await bot.send_photo(
                        admin_id,
                        photo=message.photo[-1].file_id,
                        caption=f"""
📥 *YANGI TO'LOV!*

👤 Foydalanuvchi: {message.from_user.first_name}
🆔 ID: {user_id}
💰 Summa: {amount} RUB
📊 To'lov ID: {payment_id}

✅ Tasdiqlash: /approve_{user_id}_{amount}
❌ Rad etish: /reject_{user_id}
                        """
                    )
                except Exception as e:
                    logger.error(f"Admin xabari: {e}")
        
        # ========== ADMIN TO'LOVNI TASDIQLASH ==========
        @dp.message(lambda m: m.text and m.text.startswith("/approve_"))
        async def approve_payment_admin(message: Message):
            """ESKI SISTEMA: Admin to'lovni tasdiqlaydi"""
            if not is_admin(message.from_user.id):
                await message.answer("❌ Siz admin emassiz!")
                return
            
            try:
                # Komandani ajratish: /approve_USERID_AMOUNT
                parts = message.text.split("_")
                if len(parts) < 3:
                    await message.answer("❌ Format: /approve_USERID_AMOUNT")
                    return
                
                user_id = int(parts[1])
                amount = parts[2]
                payment_type = f"{amount}_rub"
                
                # To'lovni tasdiqlash
                success = db.approve_payment(user_id, payment_type)
                
                if not success:
                    await message.answer(f"❌ To'lovni tasdiqlashda xatolik!")
                    return
                
                # Foydalanuvchi ma'lumotlari
                user = db.get_user(user_id)
                
                # Foydalanuvchiga xabar
                try:
                    await bot.send_message(
                        user_id,
                        f"""
✅ *To'lovingiz tasdiqlandi!*

💰 *Summa:* {amount} RUB
📊 *Yangi balans:* {user['balance_rub']} RUB

🔑 Endi VPN kalit yaratishingiz mumkin!

💳 *Kalit yaratish uchun:* 
"VPN kalitlarim" tugmasini bosing yoki /vpn buyrug'ini yuboring.
                        """,
                        parse_mode="Markdown"
                    )
                except:
                    pass
                
                await message.answer(f"""
✅ *To'lov tasdiqlandi!*

👤 Foydalanuvchi: {user['first_name']}
🆔 ID: {user_id}
💰 Summa: {amount} RUB
📊 Yangi balans: {user['balance_rub']} RUB

📬 Foydalanuvchiga xabar yuborildi.
                """)
                
            except Exception as e:
                await message.answer(f"❌ Xatolik: {str(e)}")
        
        # ========== VPN KALITLAR ==========
        @dp.message(lambda m: m.text and "🔑 VPN kalitlarim" in m.text)
        @dp.message(Command("vpn"))
        async def vpn_keys(message: Message):
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
                            [InlineKeyboardButton(text="🔑 VPN kalit yaratish", callback_data="create_vpn_key")]
                        ]
                    )
                    
                    await message.answer("""
🔑 *VPN KALITLAR*

❌ Sizda aktiv VPN kalit yo'q.

✅ Sizda kalit yaratish uchun to'lov mavjud!

💎 *VPN kalit yaratish uchun:* Quyidagi tugmani bosing.
                    """, reply_markup=keyboard, parse_mode="Markdown")
                else:
                    await message.answer("""
🔑 *VPN KALITLAR*

❌ Sizda aktiv VPN kalit yo'q.
❌ Sizda kalit yaratish uchun to'lov ham yo'q.

💳 *Avval to'lov qiling:* 
"To'lov qilish" tugmasini bosing yoki /payment buyrug'ini yuboring.
                    """, parse_mode="Markdown")
                return
            
            # Aktiv kalitlar bor
            response = "🔑 *VPN kalitlaringiz:*\n\n"
            
            for key in keys[:3]:
                expires = key['expires_at'].split()[0] if key['expires_at'] else "N/A"
                response += f"""
📌 *Kalit ID:* `{key['key_id'][:15]}...`
💰 *To'lov:* {key['amount_rub']} RUB
📅 *Muddati:* {expires}
🔗 *URL:* `{key['access_url'][:30]}...`
                """
                response += "➖➖➖➖➖➖➖\n"
            
            await message.answer(response, parse_mode="Markdown")
        
        # ========== VPN KALIT YARATISH ==========
        @dp.callback_query(lambda c: c.data == "create_vpn_key")
        async def create_vpn_key_callback(callback):
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
                from bot.outline_api import OutlineAPI
                outline = OutlineAPI()
                
                # Kalit nomi
                user = db.get_user(user_id)
                key_name = f"{user['first_name']}_{user_id}_{payment['id']}"
                
                # Trafik limiti
                amount = payment['amount_rub']
                if amount >= 1200:
                    limit_gb = 120  # 1 yil
                elif amount >= 400:
                    limit_gb = 30   # 3 oy
                else:
                    limit_gb = 10   # 1 oy
                
                # Kalit yaratish
                result = outline.create_key(name=key_name, limit_gb=limit_gb)
                
                if result['success']:
                    # Bazaga saqlash
                    db.add_vpn_key(
                        user_id=user_id,
                        payment_id=payment['id'],
                        key_id=result['key_id'],
                        access_url=result['access_url']
                    )
                    
                    await callback.message.answer(f"""
✅ *VPN kalit yaratildi!*

🔑 *Kalit ID:* `{result['key_id']}`
🌐 *Access URL:*
`{result['access_url']}`

📊 *Trafik limiti:* {limit_gb} GB
⏰ *Muddati:* 30 kun
💎 *Kunlik to'lov:* 5 RUB

⚠️ *Eslatma:* Access URL ni hech kimga bermang!

📱 *Qo'llash:* Outline ilovasiga Access URL ni kiriting.
                    """, parse_mode="Markdown")
                    
                    await callback.answer()
                else:
                    await callback.message.answer(f"""
❌ *VPN kalit yaratishda xatolik!*

Xatolik: {result.get('error', 'Noma\'lum xatolik')}

Iltimos, keyinroq urinib ko'ring yoki admin bilan bog'laning.
                    """)
                    
            except Exception as e:
                logger.error(f"VPN key error: {e}")
                await callback.message.answer("❌ VPN kalit yaratishda xatolik!")
        
        # ========== STATISTIKA ==========
        @dp.message(lambda m: m.text and "📊 Mening statistikam" in m.text)
        async def stats_cmd(message: Message):
            user_id = message.from_user.id
            user = db.get_user(user_id)
            
            if not user:
                await message.answer("❌ Foydalanuvchi topilmadi!")
                return
            
            await message.answer(f"""
📊 *Sizning statistikangiz:*

👤 Ism: {user['first_name']}
💰 Balans: {user['balance_rub']} RUB
📅 Ro'yxatdan: {user['created_at'].split()[0]}
            """, parse_mode="Markdown")
        
        # ========== REFERAL ==========
        @dp.message(lambda m: m.text and "👥 Referal tizimi" in m.text)
        async def referral_cmd(message: Message):
            user_id = message.from_user.id
            
            # Referal link
            import hashlib
            referral_code = hashlib.md5(str(user_id).encode()).hexdigest()[:8]
            bot_info = await bot.get_me()
            full_link = f"https://t.me/{bot_info.username}?start=ref{referral_code}"
            
            await message.answer(f"""
👥 *REFERAL TIZIMI*

💰 *Bonus:* Har bir taklif qilgan do'stingiz uchun *50 RUB* bonus!

🔗 *Sizning referal havolangiz:*
`{full_link}`

📊 *Statistika:* Hali hech kimni taklif qilmagansiz

📝 *Qo'llanma:*
1. Havolani do'stlaringizga yuboring
2. Ular havola orqali botga kirsin
3. Siz 50 RUB bonus olasiz!
4. Ular to'lov qilsa, siz yana 50 RUB bonus!
            """, parse_mode="Markdown")
        
        # ========== ADMIN BUYRUQLARI ==========
        @dp.message(Command("admin"))
        async def admin_cmd(message: Message):
            if not is_admin(message.from_user.id):
                await message.answer("❌ Siz admin emassiz!")
                return
            
            await message.answer("""
👑 *ADMIN PANEL*

📊 Statistika: /stats_admin
👥 Foydalanuvchilar: /users_admin
💳 To'lovlar: /payments_admin

✅ To'lov tasdiqlash: /approve_USERID_AMOUNT
🔑 VPN kalit yaratish: /create_key_USERID
            """, parse_mode="Markdown")
        
        @dp.message(Command("stats_admin"))
        async def stats_admin(message: Message):
            if not is_admin(message.from_user.id):
                return
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM users')
                total = cursor.fetchone()[0]
                
                cursor.execute('SELECT SUM(balance_rub) FROM users')
                balance = cursor.fetchone()[0] or 0
                
                cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "pending"')
                pending = cursor.fetchone()[0]
                
            await message.answer(f"""
📊 *Admin statistika:*

👥 Foydalanuvchilar: {total}
💰 Umumiy balans: {balance} RUB
⏳ Kutilayotgan to'lovlar: {pending}
            """)
        
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
