#!/usr/bin/env python3
# main.py - TO'LIQ ISHLAYDI
import asyncio
import logging
import os
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database
from bot.database import Database
db = Database()

# Admin tekshiruvi
def is_admin(user_id: int) -> bool:
    """Admin tekshiruvi"""
    admin_ids = [7813148656, 7322186151]  # Hardcode admin ID lar
    return user_id in admin_ids

async def main():
    """Asosiy funksiya"""
    try:
        # Bot tokenni olish
        BOT_TOKEN = os.getenv("BOT_TOKEN", "8539085576:AAEkAp8oGqUSdKhw0oGlzQQRXRAVu2MGU1o")
        
        if not BOT_TOKEN or ":" not in BOT_TOKEN:
            logger.error("❌ Noto'g'ri bot token!")
            return
        
        logger.info("🤖 Bot ishga tushmoqda...")
        
        # Bot va dispatcher
        bot = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # ========== HANDLERLAR ==========
        
        # START
        @dp.message(CommandStart())
        async def start_cmd(message: Message):
            """Start komandasi"""
            user_id = message.from_user.id
            username = message.from_user.username
            first_name = message.from_user.first_name
            
            # Foydalanuvchini bazaga qo'shish
            db.add_user(user_id, username, first_name)
            
            # Asosiy keyboard
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
• 🔐 Xavfsiz VPN ulanish
• 💳 To'lov qilish (150/400/1200 RUB)
• 📊 Trafik monitoring (10GB limit)
• 👥 Referal tizimi (50 RUB bonus)
• ⚡ Tezkor serverlar

💎 *Boshlash uchun:* Quyidagi menyudan tanlang!
            """, reply_markup=keyboard, parse_mode="Markdown")
        
        # STATISTIKA
        @dp.message(lambda m: m.text and "📊 Mening statistikam" in m.text)
        async def stats_cmd(message: Message):
            """Foydalanuvchi statistikasi"""
            user_id = message.from_user.id
            user = db.get_user(user_id)
            
            if not user:
                await message.answer("❌ Foydalanuvchi topilmadi!")
                return
            
            # Aktiv kalitlar
            active_keys = db.get_active_keys(user_id)
            
            # To'lovlar soni
            payments = db.get_user_payments(user_id)
            
            stats_text = f"""
📊 *Sizning statistikangiz:*

👤 *Ism:* {user['first_name']}
💰 *Balans:* {user['balance_rub']} RUB
🔑 *Aktiv kalitlar:* {len(active_keys)} ta
💳 *To'lovlar:* {len(payments)} ta
📅 *Ro'yxatdan:* {user['created_at'].split()[0]}
            """
            
            await message.answer(stats_text, parse_mode="Markdown")
        
        # TO'LOV MENYUSI
        @dp.message(lambda m: m.text and "💳 To'lov qilish" in m.text)
        async def payment_menu(message: Message):
            """To'lov menyusi"""
            user = db.get_user(message.from_user.id)
            
            payment_text = f"""
💳 *TO'LOV QILISH*

💰 *Joriy balansingiz:* {user['balance_rub']} RUB

🏦 *Bank ma'lumotlari:*
🔢 *Karta raqami:* `2202208022460399`
👤 *Karta egasi:* Наврузбек Бобобеков
🏛️ *Bank:* Сбербанк

📦 *PAKETLAR:*
1️⃣ *1 oylik:* 150 RUB (30 kun)
2️⃣ *3 oylik:* 400 RUB (90 kun)  
3️⃣ *1 yillik:* 1200 RUB (365 kun)

📸 *QADAMLAR:*
1. Yuqoridagi karta raqamiga to'lov qiling
2. To'lov chekini yuboring
3. Admin to'lovni tasdiqlaydi (1-24 soat)
4. Balansingizga pul qo'shiladi
5. VPN kalit yaratasiz
            """
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="1️⃣ 1 oylik - 150 RUB", callback_data="pay_1_month"),
                        InlineKeyboardButton(text="2️⃣ 3 oylik - 400 RUB", callback_data="pay_3_month")
                    ],
                    [
                        InlineKeyboardButton(text="3️⃣ 1 yillik - 1200 RUB", callback_data="pay_1_year")
                    ]
                ]
            )
            
            await message.answer(payment_text, reply_markup=keyboard, parse_mode="Markdown")
        
        # VPN KALITLAR
        @dp.message(lambda m: m.text and "🔑 VPN kalitlarim" in m.text)
        async def vpn_keys_cmd(message: Message):
            """VPN kalitlar ro'yxati"""
            user_id = message.from_user.id
            keys = db.get_active_keys(user_id)
            
            if not keys:
                await message.answer("""
🔑 *VPN kalitlaringiz*

❌ Sizda aktiv VPN kalit yo'q.

💳 Avval to'lov qiling, keyin VPN kalit yarating.
                """, parse_mode="Markdown")
                return
            
            response = "🔑 *VPN kalitlaringiz:*\n\n"
            
            for key in keys[:5]:  # Faqat 5 tasini ko'rsatish
                expires = key['expires_at'].split()[0] if key['expires_at'] else "N/A"
                response += f"""
📌 *Kalit ID:* `{key['key_id']}`
💰 *To'lov:* {key['amount_rub']} RUB
📅 *Muddati:* {expires}
🔗 *URL:* `{key['access_url'][:50]}...`
                """
                response += "➖➖➖➖➖➖➖\n"
            
            await message.answer(response, parse_mode="Markdown")
        
        # REFERAL TIZIMI
        @dp.message(lambda m: m.text and "👥 Referal tizimi" in m.text)
        async def referral_cmd(message: Message):
            """Referal tizimi"""
            user_id = message.from_user.id
            
            # Referal statistikasi
            stats = db.get_referrals_count(user_id)
            
            # Referal link
            referral_code = db.get_or_create_referral_link(user_id)
            bot_info = await bot.get_me()
            full_link = f"https://t.me/{bot_info.username}?start=ref{referral_code}"
            
            response = f"""
👥 *REFERAL TIZIMI*

💰 *Bonuslar:*
• Har bir taklif: *50 RUB*
• Do'stingiz to'lov qilsa: *+50 RUB*

📊 *Sizning statistikangiz:*
• Jami takliflar: {stats['total']}
• Faol takliflar: {stats['active']}
• Umumiy bonus: {stats['total_bonus']} RUB

🔗 *Sizning referal havolangiz:*
`{full_link}`

📝 *Qanday ishlaydi:*
1. Havolani do'stlaringizga yuboring
2. Ular havola orqali botga kirsin
3. Siz darhol 50 RUB bonus olasiz!
4. Ular to'lov qilsa, yana 50 RUB bonus!
            """
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="📤 Havolani ulashish", 
                                           url=f"https://t.me/share/url?url={full_link}&text=VPN bot orqali tez va xavfsiz internet!"),
                        InlineKeyboardButton(text="📱 Copy link", callback_data="copy_referral")
                    ]
                ]
            )
            
            await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
        # YORDAM
        @dp.message(lambda m: m.text and "ℹ️ Yordam" in m.text)
        async def help_cmd(message: Message):
            """Yordam"""
            await message.answer("""
ℹ️ *YORDAM*

📞 *Bog'lanish:* @navnav123667

❓ *Ko'p beriladigan savollar:*

1. *VPN qanday ishlatiladi?*
   • Outline ilovasini yuklang
   • Access URL ni kiriting
   • VPN yoqib qo'ying

2. *To'lovni qanday qilaman?*
   • "To'lov qilish" menyusidan
   • Karta ma'lumotlariga to'lov
   • Chekni yuboring

3. *Referal tizimi nima?*
   • Do'stlaringizni taklif qiling
   • Har bir taklif uchun 50 RUB bonus
   • Do'stingiz to'lov qilsa yana 50 RUB

4. *Muammo bo'lsa nima qilish kerak?*
   • @navnav123667 ga yozing
   • Yoki admin bilan bog'laning

💎 *Buyruqlar:*
/start - Botni ishga tushirish
/profile - Profilim
/payment - To'lov qilish  
/vpn - VPN kalitlarim
/referral - Referal tizimi
/admin - Admin panel
            """, parse_mode="Markdown")
        
        # ADMIN PANEL
        @dp.message(Command("admin"))
        async def admin_cmd(message: Message):
            """Admin panel"""
            if not is_admin(message.from_user.id):
                await message.answer("❌ Siz admin emassiz!")
                return
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
                    [InlineKeyboardButton(text="📋 To'lovlar", callback_data="admin_payments")],
                    [InlineKeyboardButton(text="👤 Foydalanuvchilar", callback_data="admin_users")],
                    [InlineKeyboardButton(text="✅ To'lovni tasdiqlash", callback_data="admin_approve")]
                ]
            )
            
            await message.answer("👑 *Admin Panel*", reply_markup=keyboard, parse_mode="Markdown")
        
        # PROFIL
        @dp.message(Command("profile"))
        async def profile_cmd(message: Message):
            """Profil"""
            user_id = message.from_user.id
            user = db.get_user(user_id)
            
            if not user:
                await message.answer("❌ Foydalanuvchi topilmadi!")
                return
            
            await message.answer(f"""
📊 *Sizning profilingiz:*

👤 Ism: {user['first_name']}
💰 Balans: {user['balance_rub']} RUB
📅 Ro'yxatdan: {user['created_at'].split()[0]}

💳 To'lov qilish uchun "To'lov qilish" tugmasini bosing.
            """, parse_mode="Markdown")
        
        # TO'LOV (buyruq)
        @dp.message(Command("payment"))
        async def payment_cmd(message: Message):
            """To'lov"""
            await payment_menu(message)
        
        # VPN (buyruq)
        @dp.message(Command("vpn"))
        async def vpn_cmd(message: Message):
            """VPN"""
            await vpn_keys_cmd(message)
        
        # REFERAL (buyruq)
        @dp.message(Command("referral"))
        async def referral_cmd(message: Message):
            """Referal"""
            await referral_cmd(message)
        
        # FOTO TO'LOV CHEKI
        @dp.message(lambda m: m.photo)
        async def handle_payment_screenshot(message: Message):
            """To'lov chekini qabul qilish"""
            user_id = message.from_user.id
            
            # Oxirgi to'lovni topish (pending)
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id FROM payments 
                WHERE user_id = ? AND status = 'pending'
                ORDER BY created_at DESC LIMIT 1
                ''', (user_id,))
                
                payment = cursor.fetchone()
                
                if not payment:
                    await message.answer("❌ Avval to'lov summasini tanlang!")
                    return
                
                payment_id = payment[0]
                
                # Screenshot ID sini saqlash
                cursor.execute('UPDATE payments SET screenshot_id = ? WHERE id = ?', 
                             (message.photo[-1].file_id, payment_id))
                conn.commit()
            
            await message.answer("""
✅ To'lov cheki qabul qilindi!

⏳ Admin to'lovni tekshirgach, balansingizga pul qo'shiladi.

💎 Eslatma: Tasdiqlash uchun 1-24 soat vaqt ketishi mumkin.
            """)
            
            # Adminlarga xabar
            admin_ids = [7813148656]
            for admin_id in admin_ids:
                try:
                    await bot.send_photo(
                        admin_id,
                        photo=message.photo[-1].file_id,
                        caption=f"📥 Yangi to'lov cheki!\nUser: {user_id}"
                    )
                except:
                    pass
        
        # ========== CALBACK QUERY ==========
        
        @dp.callback_query(lambda c: c.data == "admin_stats")
        async def admin_stats_callback(callback):
            """Admin statistika"""
            if not is_admin(callback.from_user.id):
                await callback.answer("❌ Siz admin emassiz!", show_alert=True)
                return
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM users')
                total = cursor.fetchone()[0]
                
                cursor.execute('SELECT SUM(balance_rub) FROM users')
                balance = cursor.fetchone()[0] or 0
                
                cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "pending"')
                pending = cursor.fetchone()[0]
            
            await callback.message.edit_text(
                f"📊 *Statistika:*\n\n👥 Users: {total}\n💰 Balance: {balance} RUB\n⏳ Pending: {pending}",
                parse_mode="Markdown"
            )
            await callback.answer()
        
        @dp.callback_query(lambda c: c.data.startswith("pay_"))
        async def payment_callback(callback):
            """To'lov tanlash"""
            payment_type = callback.data.replace("pay_", "")
            
            # Narxlar
            prices = {"1_month": 150, "3_month": 400, "1_year": 1200}
            
            if payment_type not in prices:
                await callback.answer("❌ Noto'g'ri to'lov turi!")
                return
            
            amount = prices[payment_type]
            user_id = callback.from_user.id
            
            # To'lovni bazaga qo'shish
            payment_id = db.add_payment(user_id, amount, payment_type)
            
            if payment_id:
                await callback.message.answer(f"""
✅ *To'lov saqlandi!*

💰 *Summa:* {amount} RUB
📦 *Paket:* {payment_type}

📸 Endi to'lov chekini (screenshot) yuboring.

🏦 *Karta ma'lumotlari:*
2202208022460399
Наврузбек Бобобеков
Сбербанк
                """, parse_mode="Markdown")
                await callback.answer()
            else:
                await callback.answer("❌ To'lovni saqlashda xatolik!", show_alert=True)
        
        # ========== BOTNI ISHGA TUSHIRISH ==========
        
        logger.info("✅ Database tekshirildi")
        
        # Webhook ni o'chirish
        await bot.delete_webhook(drop_pending_updates=True)
        
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot ishga tushdi: @{bot_info.username}")
        logger.info(f"🆔 Bot ID: {bot_info.id}")
        
        # Polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Botda xatolik: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("👋 Bot to'xtatildi")

if __name__ == "__main__":
    asyncio.run(main())
