# bot/handlers/payment.py - TO'LIQ TUZATILGAN (303-QATORNI TEKSHIRISH)
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
            text=f"1 oy - {Config.PRICE_1_MONTH} RUB", 
            callback_data="payment_1_month"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text=f"3 oy - {Config.PRICE_3_MONTH} RUB", 
            callback_data="payment_3_month"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text=f"1 yil - {Config.PRICE_1_YEAR} RUB", 
            callback_data="payment_1_year"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="Orqaga", callback_data="main_menu")
    )
    
    return builder.as_markup()

def get_payment_details_keyboard(payment_type: str):
    """To'lov tafsilotlari"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="To'lov qildim", 
            callback_data=f"confirm_payment_{payment_type}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="Bekor qilish", callback_data="main_menu")
    )
    
    return builder.as_markup()

@router.callback_query(F.data == "payment_menu")
async def show_payment_menu(callback: CallbackQuery):
    """To'lov menyusini ko'rsatish"""
    await callback.message.edit_text(
        "To'lov menyusi\n\n"
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
        await callback.answer("Notogri tanlov!")
        return
    
    price_info = PAYMENT_PRICES[payment_type]
    
    # Karta ma'lumotlari
    card_number = Config.PAYMENT_CARD_NUMBER
    card_name = Config.PAYMENT_CARD_NAME
    bank_name = Config.PAYMENT_BANK
    
    message_text = (
        f"To'lov ma'lumotlari\n\n"
        
        f"Tarif: {price_info['label']}\n"
        f"Summa: {price_info['amount']} RUB\n\n"
        
        f"Bank ma'lumotlari:\n"
        f"• Bank: {bank_name}\n"
        f"• Karta raqami: {card_number}\n"
        f"• Karta egasi: {card_name}\n\n"
        
        f"To'lov qilish tartibi:\n"
        f"1. Yuqoridagi karta raqamiga {price_info['amount']} RUB otkazing\n"
        f"2. To'lov chekini (screenshot) yuboring\n"
        f"3. Admin to'lovni tekshiradi\n"
        f"4. Sizning hisobingizga {price_info['amount']} RUB qoshiladi\n\n"
        
        f"Eslatma: To'lov chekida summa va vaqt korinishi kerak!"
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
        await callback.answer("Notogri to'lov turi!")
        return
    
    # Foydalanuvchi ma'lumotlarini saqlash
    await state.update_data(
        payment_type=payment_type,
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name
    )
    
    # Screenshot kutish holatiga otamiz
    await state.set_state(PaymentStates.waiting_for_screenshot)
    
    await callback.message.edit_text(
        "To'lov chekini yuboring\n\n"
        "Iltimos, to'lov cheki (screenshot) rasmini yuboring.\n"
        "Rasmda quyidagilar korinishi kerak:\n"
        "• To'lov summasi\n"
        "• Vaqt\n"
        "• Karta raqamining oxirgi 4 ta raqami\n\n"
        "Bekor qilish uchun /cancel",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(PaymentStates.waiting_for_screenshot)
async def receive_screenshot(message: Message, state: FSMContext):
    """Screenshot qabul qilish"""
    # Agar rasm bolmasa
    if not message.photo:
        await message.answer(
            "Iltimos, to'lov chekini rasmini yuboring!\n"
            "Yoki /cancel buyrug'i bilan bekor qiling."
        )
        return
    
    # State ma'lumotlarini olish
    data = await state.get_data()
    payment_type = data.get('payment_type')
    user_id = data.get('user_id')
    username = data.get('username', 'Nomalum')
    first_name = data.get('first_name', 'Foydalanuvchi')
    
    if payment_type not in PAYMENT_PRICES:
        await message.answer("Xatolik! Qaytadan urinib koring.")
        await state.clear()
        return
    
    price_info = PAYMENT_PRICES[payment_type]
    
    # To'lovni bazaga qoshish
    payment_id = db.add_payment(user_id, price_info['amount'], payment_type, screenshot_id=message.photo[-1].file_id)
    
    if not payment_id:
        await message.answer("To'lovni saqlashda xatolik!")
        await state.clear()
        return
    
    # Adminlarga xabar yuborish
    if Config.ADMIN_CHAT_ID:
        try:
            admin_text = (
                f"Yangi to'lov so'rovi!\n\n"
                f"Foydalanuvchi: {first_name} (@{username})\n"
                f"ID: {user_id}\n"
                f"Tarif: {price_info['label']}\n"
                f"Summa: {price_info['amount']} RUB\n"
                f"To'lov ID: {payment_id}\n\n"
                f"Tasdiqlash: /approve_{user_id}_{payment_type}\n"
                f"Rad etish: /reject_{user_id}"
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
        f"To'lov cheki qabul qilindi!\n\n"
        f"Adminlar to'lovni tekshirishadi va "
        f"{price_info['amount']} RUB hisobingizga qoshiladi.\n\n"
        f"Tezkor javob uchun: @admin",
        parse_mode="HTML"
    )
    
    # State ni tozalash
    await state.clear()

def get_success_keyboard():
    """To'lov tasdiqlangandan keyingi klaviatura"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="VPN Kalit olish", callback_data="get_key")
    )
    
    builder.row(
        InlineKeyboardButton(text="Mening balansim", callback_data="my_stats"),
        InlineKeyboardButton(text="Yana to'lov qilish", callback_data="payment_menu")
    )
    
    return builder.as_markup()

# REFERAL BONUS FUNCTIONS
async def award_referral_bonus(user_id: int, first_name: str, username: str, bot):
    """To'lov qilgan foydalanuvchi uchun referal bonus berish"""
    try:
        # Referalni kim taklif qilganini topish
        from bot.database import Database
        db = Database()
        
        referrals = db.get_referrals_by_referred(user_id)
        
        for referral in referrals:
            if referral.get('status') == 'active' and not referral.get('bonus_awarded', 0):
                referrer_id = referral['referrer_id']
                
                # Bonus berish
                bonus_days = Config.REFERRAL_BONUS_DAYS
                bonus_rub = bonus_days * Config.DAILY_FEE_RUB
                
                # Referrer balansini yangilash
                db.update_user_balance(referrer_id, bonus_rub)
                
                # Referal holatini yangilash
                try:
                    db.cursor.execute('''
                        UPDATE referrals 
                        SET bonus_awarded = 1, status = 'completed'
                        WHERE referred_id = ? AND referrer_id = ?
                    ''', (user_id, referrer_id))
                    db.conn.commit()
                except Exception as e:
                    logger.error(f"Referral update error: {e}")
                
                logger.info(f"Referral bonus awarded: {referrer_id} <- {user_id} ({bonus_rub} RUB)")
                
                # Referrer ga xabar
                try:
                    referrer = db.get_user(referrer_id)
                    if referrer:
                        referrer_name = referrer.get('first_name', 'Foydalanuvchi')
                        
                        await bot.send_message(
                            referrer_id,
                            f"Tabriklaymiz! Sizning referalingiz to'lov qildi!\n\n"
                            f"Referal: {first_name} (@{username if username else 'Nomalum'})\n"
                            f"Bonus: {bonus_days} kunlik VPN ({bonus_rub} RUB)\n"
                            f"Eski balans: {referrer['balance_rub']} RUB\n"
                            f"Yangi balans: {referrer['balance_rub'] + bonus_rub} RUB\n\n"
                            f"Bonus avtomatik balansingizga qoshildi!",
                            parse_mode="HTML"
                        )
                except Exception as e:
                    logger.error(f"Referrer notification error: {e}")
    except Exception as e:
        logger.error(f"Referral bonus error: {e}")

@router.message(F.text)
async def approve_payment(message: Message):
    """To'lovni tasdiqlash (admin) - REFERAL BONUS QOSHILGAN"""
    # Avval text borligini tekshirish
    if not message.text or not message.text.startswith('/approve_'):
        return
    
    # Admin tekshiruvi
    if message.from_user.id not in Config.ADMIN_IDS:
        return
    
    try:
        # Komandani ajratish
        command = message.text.strip()
        logger.info(f"Processing approve command: {command}")
        
        # /approve_ ni olib tashlaymiz
        rest = command[9:]  # "/approve_" = 9 ta belgi
        
        # USERID va PAYMENT_TYPE ni ajratamiz
        parts = rest.split('_', 1)
        
        if len(parts) != 2:
            await message.answer(
                "Notogri format!\n"
                "Format: /approve_USERID_1_month\n"
                "Masalan: /approve_7322186151_1_month"
            )
            return
        
        user_id_str = parts[0]
        payment_type = parts[1]
        
        # User ID ni raqamga otkazamiz
        try:
            user_id = int(user_id_str)
        except ValueError:
            await message.answer(f"User ID raqam emas: {user_id_str}")
            return
        
        # To'lov turlari tekshiruvi
        if payment_type not in PAYMENT_PRICES:
            await message.answer(
                f"Notogri to'lov turi: '{payment_type}'\n"
                f"Togri turlar: 1_month, 3_month, 1_year"
            )
            return
        
        price_info = PAYMENT_PRICES[payment_type]
        
        logger.info(f"Processing payment for user {user_id}, type {payment_type}")
        
        # 1. Foydalanuvchini tekshirish
        user = db.get_user(user_id)
        if not user:
            await message.answer(f"Foydalanuvchi topilmadi: {user_id}")
            return
        
        logger.info(f"User found: {user['first_name']}, Current balance: {user.get('balance_rub', 0)} RUB")
        
        # 2. To'lovni tasdiqlash
        if db.approve_payment(user_id, payment_type):
            logger.info(f"Payment approved for user {user_id}")
        else:
            logger.warning(f"Payment approval note for user {user_id}")
        
        # 3. Yangilangan foydalanuvchi
        updated_user = db.get_user(user_id)
        if not updated_user:
            await message.answer("Yangilangan foydalanuvchini olishda xatolik")
            return
        
        new_balance = updated_user.get('balance_rub', 0)
        logger.info(f"New balance for user {user_id}: {new_balance} RUB")
        
        # 4. REFERAL BONUS BERISH
        await award_referral_bonus(
            user_id=user_id,
            first_name=user['first_name'],
            username=user.get('username', ''),
            bot=message.bot
        )
        
        # 5. Foydalanuvchiga xabar yuborish
        try:
            keyboard = get_success_keyboard()
            
            await message.bot.send_message(
                chat_id=user_id,
                text=(
                    f"To'lovingiz tasdiqlandi!\n\n"
                    f"Tarif: {price_info['label']}\n"
                    f"To'lov: {price_info['amount']} RUB\n"
                    f"Yangi balans: {new_balance} RUB\n\n"
                    f"Rahmat! Endi VPN kalit olishingiz mumkin.\n\n"
                    f"Quyidagi tugmalardan foydalaning:"
                ),
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            logger.info(f"Notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"User notification error: {e}")
            await message.answer(f"Foydalanuvchiga xabar yuborishda xatolik: {e}")
        
        # 6. Adminga muvaffaqiyatli javob
        success_msg = (
            f"To'lov tasdiqlandi va balans yangilandi!\n\n"
            f"Foydalanuvchi: {user_id}\n"
            f"Ism: {user['first_name']}\n"
            f"Tarif: {price_info['label']}\n"
            f"Summa: {price_info['amount']} RUB\n"
            f"Yangi balans: {new_balance} RUB\n\n"
            f"Referal bonus tekshirildi va berildi (agar bor bolsa)\n"
            f"Foydalanuvchiga xabar yuborildi."
        )
        
        await message.answer(success_msg, parse_mode="HTML")
        logger.info(f"Payment fully processed for user {user_id}")
        
    except Exception as e:
        error_msg = f"Xatolik: {type(e).__name__}: {str(e)}"
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
        "To'lov bekor qilindi.\n\n"
        "Asosiy menyuga qaytish uchun /start buyrug'ini yuboring.",
        parse_mode="HTML"
    )
