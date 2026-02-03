# bot/handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
import logging

from bot.database import Database
from bot.config import Config

router = Router()
logger = logging.getLogger(__name__)
db = Database()

def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id in Config.ADMIN_IDS

def get_admin_keyboard():
    """Admin panel klaviaturasi"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")
    )
    
    builder.row(
        InlineKeyboardButton(text="👤 Foydalanuvchilar", callback_data="admin_users"),
        InlineKeyboardButton(text="💰 To'lovlar", callback_data="admin_payments")
    )
    
    builder.row(
        InlineKeyboardButton(text="⏰ Balans qo'shish", callback_data="admin_add_balance"),
        InlineKeyboardButton(text="🗝 VPN kalitlar", callback_data="admin_keys")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu")
    )
    
    return builder.as_markup()

@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Admin panel"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    admin_text = (
        f"👑 <b>Admin panel</b>\n\n"
        f"🆔 <b>Admin ID:</b> {message.from_user.id}\n"
        f"👤 <b>Admin:</b> {message.from_user.first_name}\n\n"
        f"👇 Quyidagi tugmalardan foydalaning:"
    )
    
    await message.answer(
        admin_text,
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery):
    """Admin panelni ko'rsatish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!")
        return
    
    await admin_panel(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Admin statistikasi"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!")
        return
    
    try:
        # Barcha foydalanuvchilar
        users = db.get_all_users()
        
        # To'lovlar
        payments = db.get_all_payments(limit=100)
        
        # Statistikani hisoblash
        total_users = len(users)
        total_payments = len(payments)
        active_users = sum(1 for user in users if user['balance_days'] > 0)
        
        # Jami to'lov summasini hisoblash
        total_amount = sum(p['amount'] for p in payments if p.get('status') == 'approved')
        
        stats_text = (
            f"📊 <b>Bot statistikasi</b>\n\n"
            f"👥 <b>Jami foydalanuvchilar:</b> {total_users} ta\n"
            f"✅ <b>Faol foydalanuvchilar:</b> {active_users} ta\n"
            f"💳 <b>Jami to'lovlar:</b> {total_payments} ta\n"
            f"💰 <b>Jami to'lov summa:</b> {total_amount} RUB\n\n"
            
            f"📅 <b>Oxirgi 10 foydalanuvchi:</b>\n"
        )
        
        # Oxirgi 10 foydalanuvchi
        for i, user in enumerate(users[:10], 1):
            stats_text += (
                f"{i}. {user['first_name']} (@{user.get('username', 'N/A')})\n"
                f"   🆔 {user['telegram_id']} | ⏰ {user['balance_days']} kun\n"
            )
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Admin stats error: {e}")
        await callback.answer("❌ Xatolik yuz berdi")
    finally:
        await callback.answer()

# Bu yerda boshqa admin funksiyalarni qo'shing...