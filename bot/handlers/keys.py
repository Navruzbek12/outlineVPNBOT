# bot/handlers/keys.py - TO'LIQ TUZATILGAN
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder  # ⬅️ BU MUHIM
from aiogram.filters import Command
import logging

from bot.database import Database
from bot.config import Config

router = Router()
logger = logging.getLogger(__name__)

# Database va Outline API obyektlari
db = Database()

# Outline API ni yuklash
try:
    from bot.outline_api import OutlineAPI
    outline_api = OutlineAPI()
    logger.info("OutlineAPI loaded successfully")
except ImportError as e:
    logger.warning(f"OutlineAPI not found: {e}, using mock")
    from bot.mock_outline import MockOutlineAPI
    outline_api = MockOutlineAPI()
except Exception as e:
    logger.error(f"Error loading OutlineAPI: {e}")
    from bot.mock_outline import MockOutlineAPI
    outline_api = MockOutlineAPI()

def get_vpn_menu_keyboard():
    """VPN menyusi"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🗝 VPN Kalit olish", callback_data="get_key")
    )
    
    builder.row(
        InlineKeyboardButton(text="📋 Mening kalitlarim", callback_data="my_keys")
    )
    
    builder.row(
        InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")
    )
    
    return builder.as_markup()

@router.message(Command("vpn"))
async def cmd_vpn(message: Message):
    """VPN komandasi"""
    menu_text = (
        "🔐 <b>VPN bo'limi</b>\n\n"
        "Bu yerda siz VPN kalitlarini boshqarishingiz mumkin:\n"
        "• Yangi VPN kalit olish\n"
        "• Mavjud kalitlarni ko'rish\n"
        "• Kalitlarni boshqarish\n\n"
        "👇 Quyidagi tugmalardan foydalaning:"
    )
    
    await message.answer(
        menu_text,
        reply_markup=get_vpn_menu_keyboard(),
        parse_mode="HTML"
    )
# bot/handlers/keys.py - YANGILANGAN
@router.callback_query(F.data == "get_key")
async def get_vpn_key(callback: CallbackQuery):
    """VPN kalit olish - YANGI SISTEMA"""
    telegram_id = callback.from_user.id
    
    try:
        # 1. Foydalanuvchini tekshirish
        user = db.get_user(telegram_id)
        if not user:
            await callback.answer("❌ Foydalanuvchi topilmadi")
            return
        
        # 2. Balansni tekshirish (kunlik to'lov uchun)
        if user['balance_rub'] < 5:  # ⬅️ 5 RUB minimal
            await callback.answer("❌ Balansingiz yetarli emas!")
            
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="💳 Balans to'ldirish", callback_data="payment_menu")
            )
            
            await callback.message.answer(
                f"💰 <b>Balansingiz yetarli emas!</b>\n\n"
                f"📊 <b>Joriy balans:</b> {user['balance_rub']} RUB\n"
                f"💳 <b>Minimal talab:</b> 5 RUB (1 kun)\n\n"
                f"⚠️ <b>Eslatma:</b> Har kuni 5 RUB avtomatik yechiladi.",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            return
        
        # 3. Kalit yaratilmagan to'lovlarni olish
        payments_without_keys = db.get_payments_without_keys(telegram_id)
        
        if not payments_without_keys:
            await callback.answer("❌ Kalit olish uchun to'lov qilmagansiz!")
            
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="💳 To'lov qilish", callback_data="payment_menu")
            )
            
            await callback.message.answer(
                "💳 <b>Kalit olish uchun to'lov qilishingiz kerak!</b>\n\n"
                "Har bir to'lov uchun 1 ta VPN kalit olish mumkin.\n"
                "Har kuni 5 RUB avtomatik yechiladi.",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            return
        
        # 4. Faol kalitlar sonini tekshirish
        active_keys = db.get_active_keys(telegram_id)
        
        if active_keys:
            # Faol kalitlar ro'yxati
            keys_text = "🔑 <b>Sizda aktiv kalitlar bor:</b>\n\n"
            for key in active_keys:
                keys_text += f"• {key['payment_type']} - {key['amount_rub']} RUB\n"
            
            await callback.answer("❌ Sizda aktiv kalit bor!")
            await callback.message.answer(
                f"{keys_text}\n"
                f"⚠️ <b>Har bir to'lov uchun faqat 1 ta kalit!</b>\n"
                f"💰 <b>Kunlik to'lov:</b> 5 RUB",
                parse_mode="HTML"
            )
            return
        
        # 5. Birinchi to'lov uchun kalit yaratish
        payment = payments_without_keys[0]  # Birinchi to'lov
        
        # Kalit yaratish
        key_name = f"{user['first_name']}_{payment['payment_type']}"
        result = outline_api.create_key(key_name, Config.DEFAULT_KEY_LIMIT_GB)
        
        if not result['success']:
            await callback.answer("❌ Serverda xatolik")
            return
        
        key_data = result['data']
        key_id = key_data.get('id')
        access_url = key_data.get('accessUrl')
        
        # Bazaga saqlash
        db.add_vpn_key(telegram_id, payment['id'], key_id, access_url)
        
        # 6. Yangi balans
        updated_user = db.get_user(telegram_id)
        
        # 7. Xabar yuborish
        key_text = (
            f"🎉 <b>VPN kalit muvaffaqiyatli yaratildi!</b>\n\n"
            f"📋 <b>Tarif:</b> {payment['payment_type']}\n"
            f"💰 <b>To'lov:</b> {payment['amount_rub']} RUB\n"
            f"📊 <b>Traffic limit:</b> {Config.DEFAULT_KEY_LIMIT_GB} GB\n"
            f"⏳ <b>Muddati:</b> 30 kun\n\n"
            
            f"💳 <b>Kunlik to'lov:</b> 5 RUB\n"
            f"📊 <b>Balansingiz:</b> {updated_user['balance_rub']} RUB\n\n"
            
            f"📲 <b>Qo'shish usuli:</b>\n"
            f"1. Outline ilovasini oching\n"
            f"2. 'Add Key' tugmasini bosing\n"
            f"3. Quyidagi linkni qo'shing:\n\n"
            f"<code>{access_url}</code>\n\n"
            
            f"⚠️ <b>Ogohlantirish:</b>\n"
            f"• Har kuni 00:00 da 5 RUB avtomatik yechiladi\n"
            f"• Balans 5 RUB dan kam bo'lsa, kalit o'chiriladi\n"
            f"• Har bir to'lov uchun faqat 1 ta kalit"
        )
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📋 Kalitlarni ko'rish", callback_data="my_keys")
        )
        builder.row(
            InlineKeyboardButton(text="💰 Balansim", callback_data="my_stats"),
            InlineKeyboardButton(text="💳 To'ldirish", callback_data="payment_menu")
        )
        
        await callback.message.answer(
            key_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer("✅ VPN kalit yaratildi!")
        
    except Exception as e:
        logger.error(f"Key creation error: {e}")
        await callback.answer("❌ Xatolik yuz berdi")