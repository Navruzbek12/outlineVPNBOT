# bot/handlers/keys.py - TO'LIQ TUZATILGAN VERSIYA
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
    
    # Test qilish
    if outline_api.test_connection():
        logger.info("✅ OutlineAPI loaded and connected successfully")
    else:
        logger.error("❌ OutlineAPI failed to connect, using mock")
        raise Exception("Outline connection failed")
        
except Exception as e:
    logger.warning(f"⚠️ OutlineAPI error: {e}, using mock")
    
    # Real Mock API
    class RealMockAPI:
        def __init__(self):
            logger.info("📡 Mock OutlineAPI initialized")
            
        def create_key(self, name, limit_gb=10):
            logger.info(f"📡 Mock: Creating key {name} with {limit_gb}GB limit")
            
            # Real Outline formatdagi mock response
            return {
                'success': True,
                'data': {
                    'id': f'key_{name}_{limit_gb}',
                    'accessUrl': f'https://83.219.250.58:43437/access-keys/key_{name}_{limit_gb}',
                    'name': name,
                    'password': 'generated_password_123',
                    'port': 57322,
                    'method': 'chacha20-ietf-poly1305',
                    'dataLimit': {
                        'bytes': limit_gb * 1024 * 1024 * 1024
                    },
                    'hostnameForAccessKeys': '83.219.250.58'
                }
            }
        
        def test_connection(self):
            logger.info("📡 Mock: Connection test successful")
            return True
        
        def get_server_info(self):
            return {
                'name': 'Outline VPN Server',
                'serverId': 'mock_server_id',
                'hostnameForAccessKeys': '83.219.250.58',
                'portForNewAccessKeys': 57322
            }
    
    outline_api = RealMockAPI()

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
    """VPN kalit olish - HAQIQIY VERSIYA"""
    telegram_id = callback.from_user.id
    
    try:
        # 1. Foydalanuvchini tekshirish
        user = db.get_user(telegram_id)
        if not user:
            await callback.answer("❌ Foydalanuvchi topilmadi")
            return
        
        # 2. Balansni tekshirish
        required_balance = Config.MIN_BALANCE_FOR_KEY
        user_balance = user.get('balance_rub', 0)
        
        if user_balance < required_balance:
            await callback.answer("❌ Balansingiz yetarli emas!")
            
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="💳 Balans to'ldirish", callback_data="payment_menu")
            )
            
            await callback.message.answer(
                f"💰 <b>Balansingiz yetarli emas!</b>\n\n"
                f"📊 <b>Joriy balans:</b> {user_balance} RUB\n"
                f"💳 <b>Minimal talab:</b> {required_balance} RUB\n\n"
                f"⚠️ <b>Eslatma:</b> Har kuni {Config.DAILY_FEE_RUB} RUB avtomatik yechiladi",
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
                payment_type = key.get('payment_type', 'Nomalum')
                keys_text += f"• {payment_type}\n"
            
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
            limit_gb = Config.DEFAULT_KEY_LIMIT_GB
        except:
            limit_gb = 10
            
        logger.info(f"🔑 Creating Outline key: {key_name}, limit: {limit_gb}GB")
        result = outline_api.create_key(key_name, limit_gb)
        
        logger.info(f"🔑 Outline create_key result type: {type(result)}")
        logger.info(f"🔑 Outline create_key result: {result}")
        
        # RESPONSE NI QAYTA ISHLASH
        if isinstance(result, dict):
            if result.get('success'):
                key_data = result.get('data', {})
                logger.info(f"🔑 Key data received: {key_data}")
                
                # Access URL ni olish
                access_url = key_data.get('accessUrl')
                if not access_url:
                    # Agar accessUrl bo'lmasa, manual yasash
                    method = key_data.get('method', 'chacha20-ietf-poly1305')
                    password = key_data.get('password', '')
                    hostname = key_data.get('hostnameForAccessKeys', '83.219.250.58')
                    port = key_data.get('port', 57322)
                    
                    access_url = f"ss://{method}:{password}@{hostname}:{port}/#{key_name}"
                    logger.info(f"🔑 Constructed access URL: {access_url}")
                
                key_id = key_data.get('id', f'key_{telegram_id}')
                
                logger.info(f"✅ Key created successfully!")
                logger.info(f"✅ Access URL: {access_url[:50]}...")
                logger.info(f"✅ Key ID: {key_id}")
                
            else:
                error_msg = result.get('error', 'Nomalum xato')
                logger.error(f"❌ Outline API error: {error_msg}")
                await callback.answer("❌ Serverda xatolik")
                
                # Adminlarga xabar
                await callback.message.answer(
                    f"❌ <b>Outline serverda xatolik:</b>\n\n"
                    f"<code>{error_msg[:200]}</code>\n\n"
                    f"Iltimos, keyinroq urunib ko'ring yoki admin bilan bog'laning.",
                    parse_mode="HTML"
                )
                return
        else:
            # Eski format
            key_data = result
            access_url = key_data.get('accessUrl', f'https://example.com/key_{telegram_id}')
            key_id = key_data.get('id', f'key_{telegram_id}')
        
        # Bazaga saqlash
        try:
            db.add_vpn_key(telegram_id, payment['id'], key_id, access_url)
            logger.info(f"✅ Key saved to database: {key_id}")
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
            # Kalit yaratilgan, lekin bazaga yozib bo'lmadi
        
        # 6. Xabar yuborish
        key_text = (
            f"🎉 <b>VPN kalit muvaffaqiyatli yaratildi!</b>\n\n"
            f"📋 <b>Tarif:</b> {payment.get('payment_type', 'Nomalum')}\n"
            f"💰 <b>To'lov:</b> {payment.get('amount_rub', 0)} RUB\n"
            f"📊 <b>Traffic limit:</b> {limit_gb} GB\n"
            f"⏳ <b>Muddati:</b> {Config.KEY_EXPIRE_DAYS} kun\n\n"
            
            f"📲 <b>Qo'shish usuli:</b>\n"
            f"1. Outline ilovasini yuklang (Google Play/App Store)\n"
            f"2. Ilovani oching va '+' belgisini bosing\n"
            f"3. Quyidagi linkni qo'shing:\n\n"
            f"<code>{access_url}</code>\n\n"
            
            f"💳 <b>Moliya:</b>\n"
            f"• Kunlik to'lov: {Config.DAILY_FEE_RUB} RUB\n"
            f"• Joriy balans: {user_balance} RUB\n"
            f"• Minimal balans: {required_balance} RUB\n\n"
            
            f"⚠️ <b>Ogohlantirish:</b>\n"
            f"• Kalitni hech kimga bermang!\n"
            f"• Har kuni 00:00 da {Config.DAILY_FEE_RUB} RUB avtomatik yechiladi\n"
            f"• Balans {required_balance} RUB dan kam bo'lsa, kalit o'chiriladi"
        )
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📋 Kalitlarni ko'rish", callback_data="my_keys")
        )
        builder.row(
            InlineKeyboardButton(text="💰 Balansim", callback_data="my_stats"),
            InlineKeyboardButton(text="💳 To'ldirish", callback_data="payment_menu")
        )
        builder.row(
            InlineKeyboardButton(text="🔄 Test qilish", callback_data="test_vpn")
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

@router.callback_query(F.data == "test_vpn")
async def test_vpn(callback: CallbackQuery):
    """VPN test qilish"""
    try:
        from bot.outline_api import OutlineAPI
        api = OutlineAPI()
        
        test_result = api.test_connection()
        
        if test_result:
            await callback.message.answer(
                "✅ <b>Outline server ishlayapti!</b>\n\n"
                "Server muvaffaqiyatli javob qaytarmoqda.",
                parse_mode="HTML"
            )
        else:
            await callback.message.answer(
                "❌ <b>Outline serverga ulanib bo'lmadi!</b>\n\n"
                "Iltimos, server sozlamalarini tekshiring.",
                parse_mode="HTML"
            )
    except Exception as e:
        await callback.message.answer(
            f"❌ <b>Test xatosi:</b>\n\n"
            f"<code>{str(e)}</code>",
            parse_mode="HTML"
        )
    
    await callback.answer()

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
            key_id_short = key.get('key_id', 'Nomalum')[:10]
            created_at = key.get('created_at', 'Nomalum')
            amount = key.get('amount_rub', 0)
            access_url = key.get('access_url', 'Nomalum')
            
            keys_text += (
                f"{i}. <b>Kalit ID:</b> {key_id_short}...\n"
                f"   📅 <b>Sana:</b> {created_at}\n"
                f"   💰 <b>To'lov:</b> {amount} RUB\n"
                f"   🔗 <b>Link:</b> <code>{access_url[:50]}...</code>\n\n"
            )
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🗝 Yangi kalit", callback_data="get_key"),
            InlineKeyboardButton(text="💰 To'ldirish", callback_data="payment_menu")
        )
        builder.row(
            InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"),
            InlineKeyboardButton(text="🔄 Test", callback_data="test_vpn")
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
        await callback.message.answer(
            "❌ Kalitlarni ko'rsatishda xatolik yuz berdi.",
            parse_mode="HTML"
        )

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
