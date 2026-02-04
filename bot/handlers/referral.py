# bot/handlers/referral.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
import logging

from bot.database import Database
from bot.config import Config

router = Router()
logger = logging.getLogger(__name__)
db = Database()

def get_referral_menu_keyboard():
    """Referal menyusi"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📤 Referal linkim", callback_data="my_referral_link"),
        InlineKeyboardButton(text="👥 Mening referallarim", callback_data="my_referrals")
    )
    
    builder.row(
        InlineKeyboardButton(text="💰 Bonuslar", callback_data="referral_bonuses"),
        InlineKeyboardButton(text="📊 Statistika", callback_data="referral_stats")
    )
    
    builder.row(
        InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")
    )
    
    return builder.as_markup()

@router.message(Command("ref", "referral"))
async def cmd_referral(message: Message):
    """Referal komandasi"""
    user_id = message.from_user.id
    
    referral_text = (
        "👥 <b>Do'stlar taklif qilish tizimi</b>\n\n"
        "Do'stlaringizni taklif qiling va bonuslar oling!\n\n"
        "🎁 <b>Bonus:</b> Har bir taklif qilgan do'stingiz uchun "
        f"{Config.REFERRAL_BONUS_DAYS} kunlik VPN beriladi "
        f"({Config.REFERRAL_BONUS_DAYS * Config.DAILY_FEE_RUB} RUB)\n\n"
        "📊 <b>Qoidalar:</b>\n"
        "1. Do'stingiz sizning referal havolangiz orqali botga kirishi kerak\n"
        "2. Do'stingiz /start bosishi kerak\n"
        "3. Do'stingiz balansini to'ldirishi va to'lov qilishi kerak\n"
        "4. Sizga bonus avtomatik beriladi\n\n"
        "👇 Quyidagi bo'limlardan birini tanlang:"
    )
    
    await message.answer(
        referral_text,
        reply_markup=get_referral_menu_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "referral_menu")
async def show_referral_menu(callback: CallbackQuery):
    """Referal menyusini ko'rsatish"""
    user_id = callback.from_user.id
    
    referral_text = (
        "👥 <b>Do'stlar taklif qilish</b>\n\n"
        f"Har bir taklif qilgan do'stingiz uchun {Config.REFERRAL_BONUS_DAYS} kunlik bonus!\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    
    await callback.message.edit_text(
        referral_text,
        reply_markup=get_referral_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "my_referral_link")
async def show_referral_link(callback: CallbackQuery):
    """Foydalanuvchining referal linkini ko'rsatish"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    # Referal link yaratish
    bot_username = (await callback.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    
    referrals_count = db.get_referrals_count(user_id)
    
    link_text = (
        "🔗 <b>Sizning referal havolangiz:</b>\n\n"
        f"<code>{referral_link}</code>\n\n"
        f"📤 <b>Ushbu havolani do'stlaringizga yuboring</b>\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"• Taklif qilgan do'stlar: {referrals_count} ta\n"
        f"• Olingan bonus: {referrals_count * Config.REFERRAL_BONUS_DAYS} kun\n"
        f"• Bonus qiymati: {referrals_count * Config.REFERRAL_BONUS_DAYS * Config.DAILY_FEE_RUB} RUB\n\n"
        f"⚠️ <b>Eslatma:</b> Bonus faqat do'stingiz to'lov qilgandan keyin beriladi."
    )
    
    builder = InlineKeyboardBuilder()
    
    # Share buttons
    builder.row(
        InlineKeyboardButton(
            text="📤 Telegramda ulashish",
            url=f"https://t.me/share/url?url={referral_link}&text=VPN bot - Tezkor va xavfsiz VPN xizmati"
        )
    )
    
    # Copy button
    builder.row(
        InlineKeyboardButton(
            text="📋 Havolani nusxalash",
            callback_data=f"copy_link_{referral_link}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="referral_menu"),
        InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        link_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("copy_link_"))
async def copy_referral_link(callback: CallbackQuery):
    """Referal linkni nusxalash"""
    link = callback.data.replace("copy_link_", "")
    
    await callback.answer(
        "✅ Havola nusxalandi! Endi do'stlaringizga yuborishingiz mumkin.",
        show_alert=True
    )

@router.callback_query(F.data == "my_referrals")
async def show_my_referrals(callback: CallbackQuery):
    """Foydalanuvchining referallarini ko'rsatish"""
    user_id = callback.from_user.id
    
    referrals = db.get_referrals(user_id)
    
    if not referrals:
        await callback.message.edit_text(
            "📭 <b>Siz hali hech qanday do'st taklif qilmagansiz</b>\n\n"
            "Referal havolangizni do'stlaringizga yuboring va bonuslar oling!",
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    referrals_text = "👥 <b>Sizning taklif qilgan do'stlaringiz:</b>\n\n"
    
    for i, ref in enumerate(referrals, 1):
        status_emoji = "✅" if ref.get('status') == 'completed' else "⏳"
        name = ref.get('first_name', 'Noma\'lum')
        username = f"@{ref.get('username')}" if ref.get('username') else ""
        created = ref.get('created_at', 'Noma\'lum')
        
        referrals_text += (
            f"{i}. {status_emoji} <b>{name}</b> {username}\n"
            f"   📅 {created}\n"
            f"   🎁 {Config.REFERRAL_BONUS_DAYS if ref.get('status') == 'completed' else 0} kun bonus\n\n"
        )
    
    total_bonus = sum(1 for r in referrals if r.get('status') == 'completed') * Config.REFERRAL_BONUS_DAYS
    
    referrals_text += (
        f"\n📊 <b>Jami:</b>\n"
        f"• Takliflar: {len(referrals)} ta\n"
        f"• Faol: {sum(1 for r in referrals if r.get('status') == 'completed')} ta\n"
        f"• Kutilyapti: {sum(1 for r in referrals if r.get('status') != 'completed')} ta\n"
        f"• Olingan bonus: {total_bonus} kun\n"
        f"• Bonus qiymati: {total_bonus * Config.DAILY_FEE_RUB} RUB"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔗 Havolam", callback_data="my_referral_link"),
        InlineKeyboardButton(text="💰 Balansim", callback_data="my_stats")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="referral_menu"),
        InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        referrals_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "referral_bonuses")
async def show_referral_bonuses(callback: CallbackQuery):
    """Bonuslar haqida ma'lumot"""
    bonuses_text = (
        "💰 <b>Referal bonuslari</b>\n\n"
        
        "🎁 <b>Bonus miqdori:</b>\n"
        f"• Har bir taklif qilgan do'stingiz uchun: {Config.REFERRAL_BONUS_DAYS} kun VPN\n"
        f"• Bonus qiymati: {Config.REFERRAL_BONUS_DAYS * Config.DAILY_FEE_RUB} RUB\n\n"
        
        "📋 <b>Bonus olish shartlari:</b>\n"
        "1. Do'stingiz sizning referal havolangiz orqali kirishi\n"
        "2. Do'stingiz /start komandasini ishga tushirishi\n"
        "3. Do'stingiz balansini to'ldirishi (kamida 5 RUB)\n"
        "4. Do'stingiz to'lov qilishi\n"
        "5. Sizga bonus avtomatik beriladi\n\n"
        
        "📊 <b>Statistika:</b>\n"
        "• Cheklovlar yo'q - cheksiz taklif qilishingiz mumkin\n"
        "• Bonuslar darhol balansingizga qo'shiladi\n"
        "• Bonuslarni VPN kalit olish uchun ishlatishingiz mumkin\n\n"
        
        "⚠️ <b>Muhim:</b>\n"
        "• O'zingizni taklif qila olmaysiz\n"
        "• Bir xil foydalanuvchini qayta taklif qila olmaysiz\n"
        "• Faqat haqiqiy do'stlaringizni taklif qiling"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔗 Havolamni olish", callback_data="my_referral_link"),
        InlineKeyboardButton(text="👥 Mening referallarim", callback_data="my_referrals")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="referral_menu"),
        InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        bonuses_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "referral_stats")
async def show_referral_stats(callback: CallbackQuery):
    """Referal statistikasi"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    referrals = db.get_referrals(user_id)
    completed_count = sum(1 for r in referrals if r.get('status') == 'completed')
    pending_count = len(referrals) - completed_count
    
    total_bonus_days = completed_count * Config.REFERRAL_BONUS_DAYS
    total_bonus_rub = total_bonus_days * Config.DAILY_FEE_RUB
    
    stats_text = (
        "📊 <b>Sizning referal statistikangiz</b>\n\n"
        
        f"👤 <b>Umumiy:</b>\n"
        f"• Jami takliflar: {len(referrals)} ta\n"
        f"• Faol takliflar: {completed_count} ta\n"
        f"• Kutilyapti: {pending_count} ta\n\n"
        
        f"💰 <b>Bonuslar:</b>\n"
        f"• Olingan kunlar: {total_bonus_days} kun\n"
        f"• Bonus qiymati: {total_bonus_rub} RUB\n"
        f"• Joriy balans: {user.get('balance_rub', 0)} RUB\n\n"
        
        f"🎯 <b>Maqsadlar:</b>\n"
        f"• 5 ta taklif: {5 * Config.REFERRAL_BONUS_DAYS} kun bonus\n"
        f"• 10 ta taklif: {10 * Config.REFERRAL_BONUS_DAYS} kun bonus\n"
        f"• 20 ta taklif: {20 * Config.REFERRAL_BONUS_DAYS} kun bonus\n\n"
        
        f"📈 <b>Reyting:</b>\n"
    )
    
    # Progress bar
    progress = min(len(referrals) / 20 * 100, 100)
    progress_bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
    stats_text += f"• {progress_bar} {progress:.1f}%\n"
    
    if len(referrals) >= 20:
        stats_text += "🏆 <b>VIP status</b> - Ajoyib natija!\n"
    elif len(referrals) >= 10:
        stats_text += "🥈 <b>Kumush status</b> - Juda yaxshi!\n"
    elif len(referrals) >= 5:
        stats_text += "🥉 <b>Bronza status</b> - Yaxshi ish!\n"
    else:
        stats_text += "🎯 <b>Boshlang'ich</b> - Davom eting!\n"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔗 Taklif qilish", callback_data="my_referral_link"),
        InlineKeyboardButton(text="👥 Ko'rish", callback_data="my_referrals")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="referral_menu"),
        InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()
