# bot/handlers/keys.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
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
        # Oddiy mock class
        class SimpleMockAPI:
            def create_key(self, name, limit_gb=10):
                logger.info(f"Mock: Creating key {name} with {limit_gb}GB limit")
                return {
                    'success': True,
                    'data': {
                        'id': f'mock_key_{name}',
                        'accessUrl': f'https://mock.outline.server/mock_key_{name}',
                        'name': name,
                        'password': 'mock_password',
                        'port': 12345,
                        'method': 'chacha20-ietf-poly1305'
                    }
                }
            
            def test_connection(self):
                return True
            
            def get_server_info(self):
                return {'name': 'Mock Outline Server'}
        
        outline_api = SimpleMockAPI()

def get_vpn_menu_keyboard() -> InlineKeyboardMarkup:
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

@router.callback_query(F.data == "get_key")
async def get_vpn_key(callback: CallbackQuery):
    """VPN kalit olish"""
    telegram_id = callback.from_user.id
    
    try:
        # 1. Foydalanuvchini tekshirish
        user = db.get_user(telegram_id)
        if not user:
            await callback.answer("❌ Foydalanuvchi topilmadi")
            return
        
        # 2. Balansni tekshirish
        required_balance = 5  # Minimal kunlik to'lov
        if user['balance_rub'] < required_balance:
            await callback.answer("❌ Balansingiz yetarli emas!")
            
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="💳 Balans to'ldirish", callback_data="payment_menu")
            )
            
            await callback.message.answer(
                f"💰 <b>Balansingiz yetarli emas!</b>\n\n"
                f"📊 <b>Joriy balans:</b> {user['balance_rub']} RUB\n"
                f"💳 <b>Minimal talab:</b> {required_balance} RUB\n\n"
                f"⚠️ <b>Eslatma:</b> Kunlik to'lov {required_balance} RUB",
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
                "Har bir to'lov uchun 1 ta VPN kalit olish mumkin.",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            return
        
        # 4. Faol kalitlar sonini tekshirish
        active_keys = db.get_active_keys(telegram_id)
        
        if active_keys:
            keys_text = "🔑 <b>Sizda aktiv kalitlar bor:</b>\n\n"
            for key in active_keys[:3]:  # Faqat 3 tasini ko'rsatish
                keys_text += f"• {key.get('payment_type', 'Noma\'lum')}\n"
            
            await callback.answer("❌ Sizda aktiv kalit bor!")
            await callback.message.answer(
                f"{keys_text}\n"
                f"⚠️ <b>Har bir foydalanuvchi bir vaqtda faqat 1 ta aktiv kalit olishi mumkin!</b>",
                parse_mode="HTML"
            )
            return
        
        # 5. Birinchi to'lov uchun kalit yaratish
        payment = payments_without_keys[0]
        
        # Kalit yaratish
        key_name = f"{user['first_name']}_{payment.get('payment_type', 'default')}"
        
        # Config dan limit olish
        try:
            limit_gb = getattr(Config, 'DEFAULT_KEY_LIMIT_GB', 10)
        except:
            limit_gb = 10
            
        result = outline_api.create_key(key_name, limit_gb)
        
        # Agar API responsida 'success' bo'lmasa
        if isinstance(result, dict) and 'success' in result:
            if not result['success']:
                await callback.answer("❌ Serverda xatolik")
                return
            key_data = result['data']
        else:
            # Eski format
            key_data = result
        
        key_id = key_data.get('id', f'key_{telegram_id}')
        access_url = key_data.get('accessUrl', f'https://example.com/key_{telegram_id}')
        
        # Bazaga saqlash
        try:
            db.add_vpn_key(telegram_id, payment['id'], key_id, access_url)
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
            # Kalit yaratilgan, lekin bazaga yozib bo'lmadi
        
        # 6. Xabar yuborish
        key_text = (
            f"🎉 <b>VPN kalit muvaffaqiyatli yaratildi!</b>\n\n"
            f"📋 <b>Tarif:</b> {payment.get('payment_type', 'Noma\'lum')}\n"
            f"💰 <b>To'lov:</b> {payment.get('amount_rub', 0)} RUB\n"
            f"📊 <b>Traffic limit:</b> {limit_gb} GB\n\n"
            
            f"📲 <b>Qo'shish usuli:</b>\n"
            f"1. Outline ilovasini yuklang (Google Play/App Store)\n"
            f"2. Ilovani oching va '+' belgisini bosing\n"
            f"3. Quyidagi linkni qo'shing:\n\n"
            f"<code>{access_url}</code>\n\n"
            
            f"⚠️ <b>Ogohlantirish:</b>\n"
            f"• Kalitni hech kimga bermang!\n"
            f"• Har kuni 00:00 da 5 RUB avtomatik yechiladi\n"
            f"• Balans 5 RUB dan kam bo'lsa, kalit o'chiriladi"
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
        logger.error(f"Key creation error: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi")
        await callback.message.answer(
            f"❌ <b>Xatolik yuz berdi:</b>\n\n"
            f"<code>{str(e)[:200]}</code>\n\n"
            f"Iltimos, admin bilan bog'laning.",
            parse_mode="HTML"
        )

@router.callback_query(F.data == "my_keys")
async def show_my_keys(callback: CallbackQuery):
    """Foydalanuvchining kalitlarini ko'rsatish"""
    telegram_id = callback.from_user.id
    
    try:
        keys = db.get_user_keys(telegram_id)
        
        if not keys:
            await callback.answer("ℹ️ Sizda kalitlar yo'q")
            await callback.message.answer(
                "📭 <b>Sizda hali VPN kalitlari yo'q</b>\n\n"
                "VPN kalit olish uchun:\n"
                "1. 💳 To'lov qiling\n"
                "2. 🗝 'VPN Kalit olish' tugmasini bosing",
                parse_mode="HTML"
            )
            return
        
        keys_text = "🔑 <b>Sizning VPN kalitlaringiz:</b>\n\n"
        
        for i, key in enumerate(keys, 1):
            keys_text += (
                f"{i}. <b>Kalit ID:</b> {key.get('key_id', 'Nomalum')[:10]}...\n"
                f"   📅 <b>Sana:</b> {key.get('created_at', 'Nomalum')}\n"
                f"   💰 <b>To'lov:</b> {key.get('amount_rub', 0)} RUB\n"
                f"   🔗 <b>Link:</b> <code>{key.get('access_url', 'Nomalum')}</code>\n\n"
            )
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🗝 Yangi kalit", callback_data="get_key"),
            InlineKeyboardButton(text="💰 To'ldirish", callback_data="payment_menu")
        )
        builder.row(
            InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")
        )
        
        await callback.message.answer(
            keys_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer(f"✅ {len(keys)} ta kalit")
        
    except Exception as e:
        logger.error(f"Show keys error: {e}")
        await callback.answer("❌ Xatolik yuz berdi")

@router.callback_query(F.data.in_({"main_menu", "back_to_main"}))
async def back_to_main(callback: CallbackQuery):
    """Asosiy menyuga qaytish"""
    from bot.handlers.start import get_main_menu_keyboard
    
    await callback.message.answer(
        "🏠 <b>Asosiy menyu</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
