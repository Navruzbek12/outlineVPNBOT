,# bot/handlers/start.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command
import logging

from bot.database import Database
from bot.config import Config

router = Router()
logger = logging.getLogger(__name__)
db = Database()

def get_main_menu_keyboard():
    """Asosiy menyu"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🗝 VPN Kalit olish", callback_data="get_key")
    )
    
    builder.row(
        InlineKeyboardButton(text="📊 Mening balansim", callback_data="my_stats"),
        InlineKeyboardButton(text="💳 Hisob to'ldirish", callback_data="payment_menu")
    )
    
    builder.row(
        InlineKeyboardButton(text="👥 Do'stlarni taklif qilish", callback_data="referral_menu"),
        InlineKeyboardButton(text="🆘 Yordam", callback_data="help_menu")
    )
    
    # Admin panel (agar admin bo'lsa)
    if Config.ADMIN_IDS:
        builder.row(
            InlineKeyboardButton(text="👑 Admin panel", callback_data="admin_panel")
        )
    
    return builder.as_markup()

# bot/handlers/start.py - START HANDLER WITH REFERRAL
@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject = None):
    """Start komandasi - referal bilan"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    
    # Referal parametrini tekshirish
    referrer_id = None
    if command and command.args:
        try:
            # "ref12345" formatidan raqamni olish
            if command.args.startswith('ref'):
                referrer_id = int(command.args[3:])
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

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Yordam"""
    help_text = (
        "🆘 <b>Yordam</b>\n\n"
        
        "📋 <b>Bot qanday ishlaydi?</b>\n"
        "1. Hisobingizni to'ldiring (💳 Hisob to'ldirish)\n"
        "2. VPN kalit oling (🗝 VPN Kalit olish)\n"
        "3. Outline ilovasiga kalitni qo'shing\n"
        "4. Internetdan bemalol foydalaning!\n\n"
        
        "💰 <b>To'lov turlari:</b>\n"
        "• 1 oy - 150 RUB\n"
        "• 3 oy - 400 RUB\n"
        "• 1 yil - 1200 RUB\n\n"
        
        "📞 <b>Aloqa:</b>\n"
        "Savollar uchun: @admin\n\n"
        "⚠️ <b>Muhim eslatma:</b>\n"
        "• VPN faqat taqiqlangan saytlarni ochish uchun\n"
        "• Qonunga xilof ishlarda foydalanmang"
    )
    
    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery):
    """Asosiy menyuni ko'rsatish"""
    await callback.message.edit_text(
        "🏠 <b>Asosiy menyu</b>\n\n"
        "👇 Quyidagi tugmalardan foydalaning:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# bot/handlers/start.py - YANGILANGAN
@router.callback_query(F.data == "my_stats")
async def show_my_stats(callback: CallbackQuery):
    """Foydalanuvchi statistikasi - YANGI VERSIYA"""
    telegram_id = callback.from_user.id
    
    # Kunlik to'lovlarni tekshirish
    db.check_and_deduct_daily()
    
    user = db.get_user(telegram_id)
    if not user:
        await callback.answer("❌ Foydalanuvchi topilmadi")
        return
    
    # Foydalanuvchi statistikasi
    stats = db.get_user_stats(telegram_id)
    if not stats:
        await callback.answer("❌ Statistika topilmadi")
        return
    
    # Kunlik to'lovlar tarixi - AGAR METOD BO'LMASA, BO'SH RO'YXAT
    try:
        daily_fees = db.get_daily_fee_history(telegram_id, 7)
    except AttributeError:
        daily_fees = []  # Agar metod bo'lmasa
    
    stats_text = (
        f"📊 <b>Sizning statistikangiz</b>\n\n"
        f"👤 <b>Ism:</b> {user['first_name']}\n"
        f"🆔 <b>ID:</b> {telegram_id}\n\n"
        
        f"💰 <b>Balans:</b> {stats['balance_rub']} RUB\n"
        f"🗝 <b>Aktiv kalitlar:</b> {stats['active_keys']} ta\n"
        f"💳 <b>To'lovlar soni:</b> {stats['total_payments']} ta\n"
        f"📈 <b>Jami to'lov:</b> {stats['total_amount']} RUB\n"
    )
    
    if daily_fees:
        stats_text += f"\n📅 <b>Oxirgi 7 kunlik to'lovlar:</b>\n"
        total_daily = 0
        for fee in daily_fees:
            stats_text += f"• {fee['payment_date']}: -{fee['amount_rub']} RUB\n"
            total_daily += fee['amount_rub']
        
        if total_daily > 0:
            stats_text += f"\n📊 <b>Jami kunlik to'lov:</b> -{total_daily} RUB (7 kun)\n"
    
    stats_text += f"\n⚠️ <b>Kunlik to'lov:</b> 5 RUB (har kuni 00:00)\n"
    stats_text += f"💡 <b>Maslahat:</b> Balansingiz kamida 10-15 RUB bo'lsin"
    
    builder = InlineKeyboardBuilder()
    
    # Kalit olish tugmasi (agar balans yetarli bo'lsa)
    if stats['balance_rub'] >= 5:
        builder.row(
            InlineKeyboardButton(text="🗝 VPN Kalit olish", callback_data="get_key")
        )
    
    builder.row(
        InlineKeyboardButton(text="💳 Balans to'ldirish", callback_data="payment_menu"),
        InlineKeyboardButton(text="📋 Kalitlarim", callback_data="my_keys")
    )
    
    builder.row(
        InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()
