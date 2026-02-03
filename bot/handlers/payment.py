# bot/handlers/payment.py - TO'LIQ TUZATILGAN VERSIYA
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
import logging

from bot.database import Database
from bot.config import Config

router = Router()
logger = logging.getLogger(__name__)
db = Database()

# To'lov turlari uchun class
class PaymentStates(StatesGroup):
    waiting_for_screenshot = State()

# To'lov narxlari
PAYMENT_PRICES = {
    "1_month": {
        "amount": Config.PRICE_1_MONTH,
        "label": "1 oy"
    },
    "3_month": {
        "amount": Config.PRICE_3_MONTH,
        "label": "3 oy"
    },
    "1_year": {
        "amount": Config.PRICE_1_YEAR,
        "label": "1 yil"
    }
}

def get_payment_keyboard():
    """To'lov menyusi"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text=f"💰 1 oy - {Config.PRICE_1_MONTH} RUB", 
            callback_data="payment_1_month"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text=f"💰 3 oy - {Config.PRICE_3_MONTH} RUB", 
            callback_data="payment_3_month"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text=f"💰 1 yil - {Config.PRICE_1_YEAR} RUB", 
            callback_data="payment_1_year"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Orqaga", callback_data="main_menu")
    )
    
    return builder.as_markup()

def get_payment_details_keyboard(payment_type: str):
    """To'lov tafsilotlari"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ To'lov qildim", 
            callback_data=f"confirm_payment_{payment_type}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")
    )
    
    return builder.as_markup()

@router.callback_query(F.data == "payment_menu")
async def show_payment_menu(callback: CallbackQuery):
    """To'lov menyusini ko'rsatish"""
    await callback.message.edit_text(
        "💳 <b>To'lov menyusi</b>\n\n"
        "Quyidagi tariflardan birini tanlang:",
        reply_markup=get_payment_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("payment_"))
async def process_payment_selection(callback: CallbackQuery):
    """To'lov turini tanlash"""
    payment_type = callback.data.replace("payment_", "")
    
    if payment_type not in PAYMENT_PRICES:
        await callback.answer("❌ Noto'g'ri tanlov!")
        return
    
    price_info = PAYMENT_PRICES[payment_type]
    
    # Karta ma'lumotlari
    card_number = Config.PAYMENT_CARD_NUMBER
    card_name = Config.PAYMENT_CARD_NAME
    bank_name = Config.PAYMENT_BANK
    
    message_text = (
        f"💳 <b>To'lov ma'lumotlari</b>\n\n"
        
        f"📋 <b>Tarif:</b> {price_info['label']}\n"
        f"💰 <b>Summa:</b> {price_info['amount']} RUB\n\n"
        
        f"🏦 <b>Bank ma'lumotlari:</b>\n"
        f"• Bank: {bank_name}\n"
        f"• Karta raqami: <code>{card_number}</code>\n"
        f"• Karta egasi: {card_name}\n\n"
        
        f"📝 <b>To'lov qilish tartibi:</b>\n"
        f"1. Yuqoridagi karta raqamiga {price_info['amount']} RUB o'tkazing\n"
        f"2. To'lov chekini (screenshot) yuboring\n"
        f"3. Admin to'lovni tekshiradi\n"
        f"4. Sizning hisobingizga {price_info['amount']} RUB qo'shiladi\n\n"
        
        f"⚠️ <b>Eslatma:</b> To'lov chekida summa va vaqt ko'rinishi kerak!"
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_payment_details_keyboard(payment_type),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_payment_"))
async def confirm_payment(callback: CallbackQuery, state: FSMContext):
    """To'lovni tasdiqlash va screenshot kutish"""
    payment_type = callback.data.replace("confirm_payment_", "")
    
    if payment_type not in PAYMENT_PRICES:
        await callback.answer("❌ Noto'g'ri to'lov turi!")
        return
    
    # Foydalanuvchi ma'lumotlarini saqlash
    await state.update_data(
        payment_type=payment_type,
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name
    )
    
    # Screenshot kutish holatiga o'tamiz
    await state.set_state(PaymentStates.waiting_for_screenshot)
    
    await callback.message.edit_text(
        "📸 <b>To'lov chekini yuboring</b>\n\n"
        "Iltimos, to'lov cheki (screenshot) rasmini yuboring.\n"
        "Rasmda quyidagilar ko'rinishi kerak:\n"
        "• To'lov summasi\n"
        "• Vaqt\n"
        "• Karta raqamining oxirgi 4 ta raqami\n\n"
        "❌ Bekor qilish uchun /cancel",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(PaymentStates.waiting_for_screenshot)
async def receive_screenshot(message: Message, state: FSMContext):
    """Screenshot qabul qilish"""
    # Agar rasm bo'lmasa
    if not message.photo:
        await message.answer(
            "❌ Iltimos, to'lov chekini rasmini yuboring!\n"
            "Yoki /cancel buyrug'i bilan bekor qiling."
        )
        return
    
    # State ma'lumotlarini olish
    data = await state.get_data()
    payment_type = data.get('payment_type')
    user_id = data.get('user_id')
    username = data.get('username', 'Noma\'lum')
    first_name = data.get('first_name', 'Foydalanuvchi')
    
    if payment_type not in PAYMENT_PRICES:
        await message.answer("❌ Xatolik! Qaytadan urinib ko'ring.")
        await state.clear()
        return
    
    price_info = PAYMENT_PRICES[payment_type]
    
    # To'lovni bazaga qo'shish
    payment_id = db.add_payment(user_id, price_info['amount'], payment_type, screenshot_id=message.photo[-1].file_id)
    
    if not payment_id:
        await message.answer("❌ To'lovni saqlashda xatolik!")
        await state.clear()
        return
    
    # Adminlarga xabar yuborish
    if Config.ADMIN_CHAT_ID:
        try:
            admin_text = (
                f"🆕 <b>Yangi to'lov so'rovi!</b>\n\n"
                f"👤 <b>Foydalanuvchi:</b> {first_name} (@{username})\n"
                f"🆔 <b>ID:</b> {user_id}\n"
                f"💰 <b>Tarif:</b> {price_info['label']}\n"
                f"💵 <b>Summa:</b> {price_info['amount']} RUB\n"
                f"📋 <b>To'lov ID:</b> {payment_id}\n\n"
                f"✅ Tasdiqlash: /approve_{user_id}_{payment_type}\n"
                f"❌ Rad etish: /reject_{user_id}"
            )
            
            # Rasmni adminlarga yuborish
            await message.bot.send_photo(
                chat_id=int(Config.ADMIN_CHAT_ID),
                photo=message.photo[-1].file_id,
                caption=admin_text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Adminga xabar yuborishda xatolik: {e}")
    
    # Foydalanuvchiga javob
    await message.answer(
        f"✅ <b>To'lov cheki qabul qilindi!</b>\n\n"
        f"Adminlar to'lovni tekshirishadi va "
        f"{price_info['amount']} RUB hisobingizga qo'shiladi.\n\n"
        f"⏳ <b>Tezkor javob uchun:</b> @admin",
        parse_mode="HTML"
    )
    
    # State ni tozalash
    await state.clear()

# =========== ADMIN TO'LOV TASDIQLASH ===========

def get_success_keyboard():
    """To'lov tasdiqlangandan keyingi klaviatura"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🗝 VPN Kalit olish", callback_data="get_key")
    )
    
    builder.row(
        InlineKeyboardButton(text="📊 Mening balansim", callback_data="my_stats"),
        InlineKeyboardButton(text="💳 Yana to'lov qilish", callback_data="payment_menu")
    )
    
    return builder.as_markup()

@router.message(F.text)
async def approve_payment(message: Message):
    """To'lovni tasdiqlash (admin)"""
    # Avval text borligini tekshirish
    if not message.text or not message.text.startswith('/approve_'):
        return
    
    # Admin tekshiruvi
    if message.from_user.id not in Config.ADMIN_IDS:
        return
    
    try:
        # Komandani ajratish
        command = message.text.strip()
        logger.info(f"📝 Processing approve command: {command}")
        
        # /approve_ ni olib tashlaymiz
        rest = command[9:]  # "/approve_" = 9 ta belgi
        
        # USERID va PAYMENT_TYPE ni ajratamiz
        parts = rest.split('_', 1)
        
        if len(parts) != 2:
            await message.answer(
                "❌ Noto'g'ri format!\n"
                "Format: /approve_USERID_1_month\n"
                "Masalan: /approve_7322186151_1_month"
            )
            return
        
        user_id_str = parts[0]
        payment_type = parts[1]
        
        # User ID ni raqamga o'tkazamiz
        try:
            user_id = int(user_id_str)
        except ValueError:
            await message.answer(f"❌ User ID raqam emas: {user_id_str}")
            return
        
        # To'lov turlari tekshiruvi
        if payment_type not in PAYMENT_PRICES:
            await message.answer(
                f"❌ Noto'g'ri to'lov turi: '{payment_type}'\n"
                f"To'g'ri turlar: 1_month, 3_month, 1_year"
            )
            return
        
        price_info = PAYMENT_PRICES[payment_type]
        
        logger.info(f"🔄 Processing payment for user {user_id}, type {payment_type}")
        
        # 1. Foydalanuvchini tekshirish
        user = db.get_user(user_id)
        if not user:
            await message.answer(f"❌ Foydalanuvchi topilmadi: {user_id}")
            return
        
        logger.info(f"✅ User found: {user['first_name']}, Current balance: {user['balance_rub']} RUB")  # ⬅️ FIXED
        
        # 2. To'lovni tasdiqlash
        if db.approve_payment(user_id, payment_type):
            logger.info(f"✅ Payment approved for user {user_id}")
        else:
            logger.warning(f"⚠️ Payment approval note for user {user_id}")
        
        # 3. Yangilangan foydalanuvchi
        updated_user = db.get_user(user_id)
        if not updated_user:
            await message.answer("❌ Yangilangan foydalanuvchini olishda xatolik")
            return
        
        new_balance = updated_user['balance_rub']  # ⬅️ FIXED
        logger.info(f"✅ New balance for user {user_id}: {new_balance} RUB")
        
        # 4. Foydalanuvchiga xabar yuborish
        try:
            keyboard = get_success_keyboard()
            
            await message.bot.send_message(
                chat_id=user_id,
                text=(
                    f"🎉 <b>To'lovingiz tasdiqlandi!</b>\n\n"
                    f"✅ <b>Tarif:</b> {price_info['label']}\n"
                    f"💰 <b>To'lov:</b> {price_info['amount']} RUB\n"
                    f"📊 <b>Yangi balans:</b> {new_balance} RUB\n\n"
                    f"🎁 <b>Rahmat! Endi VPN kalit olishingiz mumkin.</b>\n\n"
                    f"👇 Quyidagi tugmalardan foydalaning:"
                ),
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            logger.info(f"✅ Notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"❌ User notification error: {e}")
            await message.answer(f"⚠️ Foydalanuvchiga xabar yuborishda xatolik: {e}")
        
        # 5. Adminga muvaffaqiyatli javob
        success_msg = (
            f"✅ <b>To'lov tasdiqlandi va balans yangilandi!</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {user_id}\n"
            f"📛 <b>Ism:</b> {user['first_name']}\n"
            f"💰 <b>Tarif:</b> {price_info['label']}\n"
            f"💵 <b>Summa:</b> {price_info['amount']} RUB\n"
            f"📊 <b>Yangi balans:</b> {new_balance} RUB\n\n"
            f"📨 <b>Foydalanuvchiga xabar yuborildi.</b>"
        )
        
        await message.answer(success_msg, parse_mode="HTML")
        logger.info(f"✅ Payment fully processed for user {user_id}")
        
    except Exception as e:
        error_msg = f"❌ Xatolik: {type(e).__name__}: {str(e)}"
        await message.answer(error_msg)
        logger.error(f"Approve payment error: {e}")
        import traceback
        traceback.print_exc()

# Bekor qilish komandasi
@router.message(F.text == "/cancel")
async def cancel_payment(message: Message, state: FSMContext):
    """To'lovni bekor qilish"""
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.clear()
    await message.answer(
        "❌ To'lov bekor qilindi.\n\n"
        "Asosiy menyuga qaytish uchun /start buyrug'ini yuboring.",
        parse_mode="HTML"
    )