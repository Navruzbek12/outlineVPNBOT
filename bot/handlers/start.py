# bot/handlers/start.py - TO'LIQ TO'G'RILANGAN
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

def get_main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="💰 Balans", callback_data="my_stats"),
        InlineKeyboardButton(text="💳 To'lov", callback_data="payment_menu")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔐 VPN", callback_data="vpn_menu"),
        InlineKeyboardButton(text="👥 Do'st taklif qilish", callback_data="referral_menu")
    )
    
    builder.row(
        InlineKeyboardButton(text="🆘 Yordam", callback_data="help_menu"),
        InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="settings_menu")
    )
    
    return builder.as_markup()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Start komandasi"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    
    # Referal parametrini tekshirish
    referrer_id = None
    command_args = message.text.split()
    if len(command_args) > 1:
        try:
            # "ref12345" formatidan raqamni olish
            if command_args[1].startswith('ref'):
                referrer_id = int(command_args[1][3:])
                logger.info(f"Referral detected: {referrer_id} -> {user_id}")
        except:
            pass
    
    # Foydalanuvchi mavjudligini tekshirish
    user_exists = db.get_user(user_id)
    
    if not user_exists:
        # Yangi foydalanuvchi qo'shish
        db.add_user(user_id, first_name, username)
        logger.info(f"✅ New user added: {user_id} - {first_name}")
        
        # Agar referal orqali kelsa
        if referrer_id and referrer_id != user_id:
            # Referalni qo'shish
            db.add_referral(referrer_id, user_id)
            
            welcome_text = (
                f"👋 Salom, {first_name}!\n\n"
                f"🎉 Siz do'stingiz taklifi bilan botga qo'shildingiz!\n\n"
                f"🤝 <b>Do'stingiz bonus oldi:</b>\n"
                f"• {Config.REFERRAL_BONUS_DAYS} kunlik VPN\n"
                f"• {Config.REFERRAL_BONUS_DAYS * Config.DAILY_FEE_RUB} RUB qiymatida\n\n"
                f"🚀 <b>Boshlash uchun:</b>\n"
                f"1. 💳 Balansingizni to'ldiring\n"
                f"2. 🔐 VPN kalit oling\n"
                f"3. 📱 Outline ilovasini o'rnating\n\n"
                f"Siz ham do'stlaringizni taklif qilib bonus olishingiz mumkin!"
            )
        else:
            welcome_text = (
                f"👋 Salom, {first_name}!\n\n"
                f"🚀 <b>VPN botiga xush kelibsiz!</b>\n\n"
                f"🔐 <b>Xizmatlar:</b>\n"
                f"• Tezkor va xavfsiz VPN\n"
                f"• Cheklovsiz internet\n"
                f"• Bloklangan saytlarga kirish\n\n"
                f"💰 <b>Narxlar:</b>\n"
                f"• Kunlik: {Config.DAILY_FEE_RUB} RUB\n"
                f"• Oylik: {Config.PRICE_1_MONTH} RUB\n"
                f"• Yillik: {Config.PRICE_1_YEAR} RUB\n\n"
                f"👥 <b>Bonus:</b> Do'stlaringizni taklif qiling va "
                f"{Config.REFERRAL_BONUS_DAYS} kunlik bonus oling!"
            )
    else:
        welcome_text = (
            f"👋 Qaytganingiz bilan, {first_name}!\n\n"
            f"🤖 <b>VPN botiga xush kelibsiz!</b>\n"
            f"Quyidagi bo'limlardan foydalaning:"
        )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.in_({"main_menu", "back_to_main"}))
async def back_to_main(callback: CallbackQuery):
    """Asosiy menyuga qaytish"""
    await callback.message.answer(
        "🏠 <b>Asosiy menyu</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Menyu komandasi"""
    await message.answer(
        "🏠 <b>Asosiy menyu</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )

# Tezkor handlerlar
@router.callback_query(F.data == "my_stats")
async def show_my_stats(callback: CallbackQuery):
    """Foydalanuvchi statistikasi"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Foydalanuvchi topilmadi")
        return
    
    stats_text = (
        f"📊 <b>Sizning statistikangiz</b>\n\n"
        f"👤 <b>Ism:</b> {user['first_name']}\n"
        f"💰 <b>Balans:</b> {user.get('balance_rub', 0)} RUB\n"
        f"📅 <b>Ro'yxatdan o'tgan:</b> {user.get('created_at', 'Noma\'lum')}\n\n"
        f"🔑 <b>Aktiv kalitlar:</b> {len(db.get_active_keys(user_id))} ta\n"
        f"💳 <b>To'lovlar:</b> {len(db.get_user_payments(user_id))} ta\n"
        f"👥 <b>Referallar:</b> {db.get_referrals_count(user_id)} ta\n\n"
        f"⚠️ <b>Kunlik to'lov:</b> {Config.DAILY_FEE_RUB} RUB"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 To'ldirish", callback_data="payment_menu"),
        InlineKeyboardButton(text="🗝 VPN", callback_data="vpn_menu")
    )
    builder.row(
        InlineKeyboardButton(text="👥 Referal", callback_data="referral_menu"),
        InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu")
    )
    
    await callback.message.answer(
        stats_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()
