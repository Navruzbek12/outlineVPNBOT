# bot/handlers/admin.py - YANGILANGAN (bot.utils ga muhtoj emas)
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.database import Database
import os
import logging

router = Router()
db = Database()
logger = logging.getLogger(__name__)

class BroadcastState(StatesGroup):
    waiting_for_message = State()

# Admin tekshiruvi funksiyasi - O'Z ICHIDA
def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    admin_ids_str = os.getenv("ADMIN_IDS", "7813148656")
    admin_ids = []
    
    for admin_id in admin_ids_str.split(","):
        admin_id = admin_id.strip()
        if admin_id.isdigit():
            admin_ids.append(int(admin_id))
    
    return user_id in admin_ids

async def admin_check(message: Message = None, callback: CallbackQuery = None) -> bool:
    """Admin tekshiruvi"""
    user_id = None
    
    if message:
        user_id = message.from_user.id
    elif callback:
        user_id = callback.from_user.id
    
    if not user_id:
        return False
    
    return is_admin(user_id)

# ========== ADMIN HANDLERLARI ==========

@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Admin panel"""
    if not await admin_check(message=message):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📋 To'lovlar", callback_data="admin_payments")],
            [InlineKeyboardButton(text="👤 Foydalanuvchilar", callback_data="admin_users")],
            [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")],
        ]
    )
    
    await message.answer("👑 *Admin Panel*", reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Umumiy statistika"""
    if not await admin_check(callback=callback):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(balance_rub) FROM users')
            total_balance = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM vpn_keys WHERE is_active = 1')
            active_keys = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "pending"')
            pending_payments = cursor.fetchone()[0]
            
            stats_text = f"""
📊 *Admin Statistika*

👥 Foydalanuvchilar: {total_users}
💰 Umumiy balans: {total_balance} RUB
🔑 Aktiv VPN kalitlar: {active_keys}
⏳ Kutilayotgan to'lovlar: {pending_payments}
            """
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_stats"),
                     InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
                ]
            )
            
            await callback.message.edit_text(stats_text, reply_markup=keyboard, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"❌ Admin stats error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)

@router.callback_query(F.data == "admin_payments")
async def admin_payments_list(callback: CallbackQuery):
    """Tasdiqlanmagan to'lovlar"""
    if not await admin_check(callback=callback):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT p.id, p.user_id, u.first_name, p.amount_rub, p.payment_type
            FROM payments p
            JOIN users u ON p.user_id = u.telegram_id
            WHERE p.status = 'pending'
            LIMIT 10
            ''')
            
            payments = cursor.fetchall()
            
            if not payments:
                await callback.message.edit_text("📭 Tasdiqlanmagan to'lov yo'q")
                return
            
            response = "⏳ *Kutilayotgan to'lovlar:*\n\n"
            for p in payments:
                response += f"ID: {p[0]}\nUser: {p[2]} ({p[1]})\nSumma: {p[3]} RUB\nTur: {p[4]}\n\n"
            
            await callback.message.edit_text(response, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"❌ Payments error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)

@router.message(Command("approve"))
async def approve_payment(message: Message):
    """To'lovni tasdiqlash"""
    if not await admin_check(message=message):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Format: /approve <payment_id>")
            return
        
        payment_id = int(args[1])
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT user_id, amount_rub FROM payments 
            WHERE id = ? AND status = 'pending'
            ''', (payment_id,))
            
            payment = cursor.fetchone()
            
            if not payment:
                await message.answer("❌ To'lov topilmadi!")
                return
            
            user_id = payment[0]
            amount = payment[1]
            
            # To'lovni tasdiqlash
            cursor.execute('''
            UPDATE payments 
            SET status = 'approved', approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (payment_id,))
            
            # Balansni yangilash
            cursor.execute('''
            UPDATE users 
            SET balance_rub = balance_rub + ? 
            WHERE telegram_id = ?
            ''', (amount, user_id))
            
            conn.commit()
            
            await message.answer(f"✅ To'lov {payment_id} tasdiqlandi!")
            
    except Exception as e:
        logger.error(f"❌ Approve error: {e}")
        await message.answer(f"❌ Xatolik: {e}")

@router.message(Command("stats"))
async def quick_stats(message: Message):
    """Tezkor statistika"""
    if not await admin_check(message=message):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(balance_rub) FROM users')
            balance = cursor.fetchone()[0] or 0
            
            await message.answer(f"📊 Stat: {total} user, {balance} RUB")
            
    except Exception as e:
        await message.answer("❌ Xatolik!")

@router.callback_query(F.data == "admin_back")
async def back_to_admin(callback: CallbackQuery):
    """Orqaga"""
    if not await admin_check(callback=callback):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    await admin_panel(callback.message)
