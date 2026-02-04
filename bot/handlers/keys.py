
# bot/handlers/keys.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
import logging

from bot.database import Database
from bot.config import Config

router = Router()
logger = logging.getLogger(__name__)

# Database obyekti
db = Database()

# Outline API ni yuklash
# keys.py da quyidagini o'zgartiring:
try:
    from bot.outline_api import OutlineAPI
    outline_api = OutlineAPI()
    logger.info("✅ OutlineAPI loaded successfully")
except Exception as e:
    logger.warning(f"⚠️ OutlineAPI not found: {e}, using mock")
    try:
        from bot.mock_outline import MockOutlineAPI
        outline_api = MockOutlineAPI()
    except ImportError:
        class SimpleMockAPI:
            def create_key(self, name, limit_gb=10):
                return {'success': True, 'data': {'id': 'mock', 'accessUrl': 'https://example.com/key'}}
            def test_connection(self): return True
        outline_api = SimpleMockAPI()

def get_vpn_menu_keyboard():
    """VPN menyusi"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🗝 VPN Kalit olish", callback_data="get_key"))
    builder.row(InlineKeyboardButton(text="📋 Mening kalitlarim", callback_data="my_keys"))
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    return builder.as_markup()

@router.message(Command("vpn"))
async def cmd_vpn(message: Message):
    """VPN komandasi"""
    menu_text = (
        "🔐 VPN bo'limi\n\n"
        "Bu yerda siz VPN kalitlarini boshqarishingiz mumkin:\n"
        "• Yangi VPN kalit olish\n"
        "• Mavjud kalitlarni ko'rish\n"
        "• Kalitlarni boshqarish\n\n"
        "👇 Quyidagi tugmalardan foydalaning:"
    )
    await message.answer(menu_text, reply_markup=get_vpn_menu_keyboard())

@router.callback_query(F.data == "get_key")
async def get_vpn_key(callback: CallbackQuery):
    """VPN kalit olish"""
    telegram_id = callback.from_user.id
    
    try:
        user = db.get_user(telegram_id)
        if not user:
            await callback.answer("Foydalanuvchi topilmadi")
            return
        
        if user.get('balance_rub', 0) < 5:
            await callback.answer("Balansingiz yetarli emas")
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="Balans to'ldirish", callback_data="payment_menu"))
            await callback.message.answer(
                f"Balansingiz yetarli emas. Joriy balans: {user.get('balance_rub', 0)} RUB",
                reply_markup=builder.as_markup()
            )
            return
        
        # Kalit yaratish
        key_name = f"{user.get('first_name', 'User')}_key"
        limit_gb = getattr(Config, 'DEFAULT_KEY_LIMIT_GB', 10)
        result = outline_api.create_key(key_name, limit_gb)
        
        key_text = (
            f"VPN kalit yaratildi\n\n"
            f"Traffic limit: {limit_gb} GB\n"
            f"Link: https://example.com/key\n\n"
            f"Ogohlantirish: Kalitni hech kimga bermang"
        )
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="Kalitlarni ko'rish", callback_data="my_keys"))
        
        await callback.message.answer(key_text, reply_markup=builder.as_markup())
        await callback.answer("VPN kalit yaratildi")
        
    except Exception as e:
        logger.error(f"Key creation error: {e}")
        await callback.answer("Xatolik yuz berdi")

@router.callback_query(F.data == "my_keys")
async def show_my_keys(callback: CallbackQuery):
    """Foydalanuvchining kalitlarini ko'rsatish"""
    telegram_id = callback.from_user.id
    
    try:
        keys = db.get_user_keys(telegram_id) or []
        
        if not keys:
            await callback.answer("Sizda kalitlar yo'q")
            await callback.message.answer("Sizda hali VPN kalitlari yo'q")
            return
        
        keys_text = "Sizning VPN kalitlaringiz:\n\n"
        
        for i, key in enumerate(keys, 1):
            # BACKSLASH XATOSINI HAL QILISH - O'ZGARUVCHIGA AJRATING
            payment_type = key.get('payment_type', "Noma'lum")
            key_id = key.get('key_id', "Noma'lum")[:10]
            amount = key.get('amount_rub', 0)
            created = key.get('created_at', "Noma'lum")
            
            keys_text += (
                f"{i}. Kalit ID: {key_id}...\n"
                f"   Sana: {created}\n"
                f"   To'lov: {amount} RUB\n\n"
            )
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="Yangi kalit", callback_data="get_key"),
            InlineKeyboardButton(text="To'ldirish", callback_data="payment_menu")
        )
        
        await callback.message.answer(keys_text, reply_markup=builder.as_markup())
        await callback.answer(f"{len(keys)} ta kalit")
        
    except Exception as e:
        logger.error(f"Show keys error: {e}")
        await callback.answer("Xatolik yuz berdi")

@router.callback_query(F.data.in_({"main_menu", "back_to_main"}))
async def back_to_main(callback: CallbackQuery):
    """Asosiy menyuga qaytish"""
    from bot.handlers.start import get_main_menu_keyboard
    
    await callback.message.answer(
        "Asosiy menyu",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
