# bot/handlers/referral.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.deep_linking import create_start_link, decode_payload
from bot.database import Database
import logging

router = Router()
db = Database()
logger = logging.getLogger(__name__)

@router.message(F.text.contains("👥 Referal"))
@router.message(Command("referral"))
async def referral_command(message: Message):
    """Referal tizimi asosiy menyusi"""
    user_id = message.from_user.id
    
    try:
        # Statistikani olish
        stats = db.get_referrals_count(user_id)
        
        # Referral link olish
        referral_code = db.get_or_create_referral_link(user_id)
        
        # Bot username ni olish
        bot_info = await message.bot.get_me()
        bot_username = bot_info.username
        
        # To'liq referral link
        full_link = f"https://t.me/{bot_username}?start=ref{referral_code}"
        
        # Inline keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Referal ro'yxati", callback_data="referral_list"),
                InlineKeyboardButton(text="💰 Bonuslar", callback_data="referral_bonus")
            ],
            [
                InlineKeyboardButton(text="📤 Havolani ulashish", 
                                    url=f"https://t.me/share/url?url={full_link}&text=VPN bot orqali tez va xavfsiz internet!"),
                InlineKeyboardButton(text="📱 Copy link", callback_data="copy_referral_link")
            ]
        ])
        
        response = f"""
👥 *REFERAL TIZIMI*

💰 *Bonuslar:*
• Har bir taklif: *50 RUB*
• Do'stingiz to'lov qilsa: *+50 RUB*

📊 *Sizning statistikangiz:*
• Jami takliflar: {stats['total']}
• Faol takliflar: {stats['active']}
• Kutilayotgan: {stats['pending']}
• Umumiy bonus: {stats['total_bonus']} RUB

🔗 *Sizning referal havolangiz:*
`{full_link}`

📝 *Qanday ishlaydi:*
1. Havolani do'stlaringizga yuboring
2. Ular havola orqali botga kirsin
3. Siz darhol 50 RUB bonus olasiz!
4. Ular to'lov qilsa, yana 50 RUB bonus!

💡 *Maslahat:* Ko'proq do'stlaringizni taklif qiling va bonuslarni yig'ing!
"""
        
        await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Referral command error: {e}")
        await message.answer("❌ Referral ma'lumotlarini olishda xatolik!")

@router.callback_query(F.data == "referral_list")
async def show_referral_list(callback: CallbackQuery):
    """Referal ro'yxatini ko'rsatish"""
    user_id = callback.from_user.id
    
    try:
        referrals = db.get_referrals_list(user_id, limit=15)
        
        if not referrals:
            await callback.message.edit_text(
                "📭 Hali hech kimni taklif qilmagansiz.\n\n"
                "Do'stlaringizni taklif qilish uchun 'Havolani ulashish' tugmasini bosing!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_referral")]
                ])
            )
            return
        
        response = "📋 *So'nggi takliflaringiz:*\n\n"
        
        for i, ref in enumerate(referrals, 1):
            response += f"{i}. {ref['name']} (@{ref['username']})\n"
            response += f"   📅 {ref['joined_date'].split()[0] if ref['joined_date'] else 'N/A'}\n"
            response += f"   💰 Holat: {ref['status']}\n"
            response += f"   {'✅ Balansi bor' if ref['has_balance'] else '❌ Balans yo\'q'}\n\n"
        
        response += f"\n📊 *Jami: {len(referrals)} ta*"
        
        await callback.message.edit_text(
            response,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Yangilash", callback_data="referral_list"),
                 InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_referral")]
            ]),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"❌ Referral list error: {e}")
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)

@router.callback_query(F.data == "referral_bonus")
async def show_referral_bonus(callback: CallbackQuery):
    """Bonus ma'lumotlari"""
    user_id = callback.from_user.id
    
    try:
        stats = db.get_referrals_count(user_id)
        
        response = f"""
💰 *REFERAL BONUSLARI*

📈 *Sizning statistikangiz:*
• Jami takliflar: {stats['total']}
• Faol (bonus berilgan): {stats['active']}
• Kutilayotgan: {stats['pending']}
• Umumiy bonus: {stats['total_bonus']} RUB

🎁 *Bonus tizimi:*
1. Do'stingiz botga kirsa: *50 RUB*
2. Do'stingiz to'lov qilsa: *+50 RUB*
3. Har bir yangi do'st: *50 RUB*

💳 *Bonuslarni qanday ishlatish mumkin:*
• VPN kalit yaratish uchun
• Kunlik to'lovlarni to'lash uchun
• Yangi to'lovlar uchun

📊 *Maksimal bonus:* Cheksiz!
Har bir yangi do'st yangi bonus demakdir!

🔗 Do'stlaringizni ko'proq taklif qiling!
"""
        
        await callback.message.edit_text(
            response,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📤 Do'stlarni taklif qilish", callback_data="invite_friends"),
                 InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_referral")]
            ]),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"❌ Referral bonus error: {e}")
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)

@router.callback_query(F.data == "copy_referral_link")
async def copy_referral_link(callback: CallbackQuery):
    """Referal linkni nusxalash"""
    user_id = callback.from_user.id
    
    try:
        referral_code = db.get_or_create_referral_link(user_id)
        bot_info = await callback.bot.get_me()
        full_link = f"https://t.me/{bot_info.username}?start=ref{referral_code}"
        
        # Telegram Web App orqali clipboard ga copy qilish
        await callback.answer(
            f"✅ Link nusxalandi!\n\n{full_link}",
            show_alert=True
        )
        
    except Exception as e:
        logger.error(f"❌ Copy link error: {e}")
        await callback.answer("❌ Linkni nusxalashda xatolik!", show_alert=True)

@router.callback_query(F.data == "back_to_referral")
async def back_to_referral(callback: CallbackQuery):
    """Asosiy referral menyusiga qaytish"""
    await referral_command(callback.message)

@router.callback_query(F.data == "invite_friends")
async def invite_friends(callback: CallbackQuery):
    """Do'stlarni taklif qilish"""
    user_id = callback.from_user.id
    
    try:
        referral_code = db.get_or_create_referral_link(user_id)
        bot_info = await callback.bot.get_me()
        full_link = f"https://t.me/{bot_info.username}?start=ref{referral_code}"
        
        share_text = f"""
🎯 Do'stim, VPN bot orqali tez va xavfsiz internetdan foydalanishni taklif qilaman!

🔗 Havola: {full_link}

✨ Afzalliklari:
• Tez va xavfsiz VPN
• Arzon narxlar (kuniga 5 RUB)
• 10GB trafik limiti
• O'zbekiston serverlari

💎 Bonus: Siz havola orqali kirsangiz, men 50 RUB bonus olaman!
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📤 Telegramda ulashish", 
                                 url=f"https://t.me/share/url?url={full_link}&text={share_text}")],
            [InlineKeyboardButton(text="📱 Linkni nusxalash", callback_data="copy_referral_link")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_referral")]
        ])
        
        await callback.message.edit_text(
            "👥 *Do'stlaringizni taklif qilish*\n\n"
            "Quyidagi tugmalar orqali do'stlaringizga havolani yuboring:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"❌ Invite friends error: {e}")
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)

@router.message(Command("start"))
async def start_with_referral(message: Message):
    """Start komandasi bilan referralni qayta ishlash"""
    user_id = message.from_user.id
    command_args = message.text.split()
    
    # Foydalanuvchini bazaga qo'shish
    db.add_user(
        telegram_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    # Referral linkni tekshirish
    referrer_id = None
    if len(command_args) > 1 and command_args[1].startswith('ref'):
        referral_code = command_args[1][3:]  # 'ref' dan keyingi qism
        
        # Referral kod bo'yicha referrer ni topish
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT telegram_id FROM users WHERE referal_link = ?', (referral_code,))
            result = cursor.fetchone()
            
            if result and result[0] != user_id:
                referrer_id = result[0]
                
                # Referral ni bazaga qo'shish
                cursor.execute('''
                INSERT OR IGNORE INTO referals (referrer_id, referred_id, bonus_awarded)
                VALUES (?, ?, 0)
                ''', (referrer_id, user_id))
                
                # Referrer ga darhol 50 RUB bonus
                if cursor.rowcount > 0:  # Agar yangi referral qo'shilgan bo'lsa
                    cursor.execute('''
                    UPDATE users 
                    SET balance_rub = balance_rub + 50 
                    WHERE telegram_id = ?
                    ''', (referrer_id,))
                    
                    # Referral'ga 50 RUB bonus berildi deb belgilash
                    cursor.execute('''
                    UPDATE referals 
                    SET bonus_awarded = 1 
                    WHERE referrer_id = ? AND referred_id = ?
                    ''', (referrer_id, user_id))
                    
                    conn.commit()
                    
                    # Referrer'ga xabar
                    try:
                        await message.bot.send_message(
                            referrer_id,
                            f"🎉 Tabriklaymiz! Siz yangi foydalanuvchini taklif qildingiz!\n"
                            f"👤 {message.from_user.first_name or message.from_user.username}\n"
                            f"💰 Sizga 50 RUB bonus qo'shildi!\n"
                            f"📊 Endi do'stingiz to'lov qilsa, yana 50 RUB bonus olasiz!"
                        )
                    except:
                        pass
    
    # Asosiy start xabari
    welcome_text = f"""
👋 Assalomu alaykum, {message.from_user.first_name}!

🤖 *VPN BOT* ga xush kelibsiz!

{('🎁 Siz referal orqali kirdingiz va taklif qilgan foydalanuvchi 50 RUB bonus oldi!' if referrer_id else '')}

✨ *Bot imkoniyatlari:*
• 🔐 Xavfsiz VPN ulanish
• 💳 To'lov qilish (100/400/1200 RUB)
• 📊 Trafik monitoring (10GB limit)
• 👥 Referal tizimi (50 RUB bonus)
• ⚡ Tezkor serverlar

💎 *Boshlash uchun:* Menyudan kerakli bo'limni tanlang!

ℹ️ Yordam kerak bo'lsa /help buyrug'ini yuboring.
"""
    
    from bot.keyboards import get_main_menu
    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="Markdown")
