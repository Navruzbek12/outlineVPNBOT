# bot/handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.database import Database
from bot.utils.admin import admin_only, is_admin
import logging

router = Router()
db = Database()
logger = logging.getLogger(__name__)

class BroadcastState(StatesGroup):
    """Broadcast uchun state"""
    waiting_for_message = State()
    
@router.message(Command("admin"), IsAdminFilter())
async def admin_command(message: types.Message):
    await message.answer("Admin paneliga xush kelibsiz!")
    
@router.message(Command("admin"), IsAdminFilter())
@admin_only
async def admin_panel(message: Message):
    """Admin panel"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📋 To'lovlar ro'yxati", callback_data="admin_payments")],
            [InlineKeyboardButton(text="👤 Foydalanuvchilar", callback_data="admin_users")],
            [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="🔄 VPN Kalit yaratish", callback_data="admin_create_key")],
            [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin_settings")],
        ]
    )
    
    await message.answer("👑 *Admin Panel*", reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "admin_stats")
@admin_only
async def admin_stats(callback: CallbackQuery):
    """Umumiy statistika"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Foydalanuvchilar soni
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            # Aktiv foydalanuvchilar (oxirgi 7 kun)
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM payments WHERE created_at >= DATE("now", "-7 days")')
            active_users = cursor.fetchone()[0]
            
            # Umumiy balans
            cursor.execute('SELECT SUM(balance_rub) FROM users')
            total_balance = cursor.fetchone()[0] or 0
            
            # Aktiv VPN kalitlar
            cursor.execute('SELECT COUNT(*) FROM vpn_keys WHERE is_active = 1')
            active_keys = cursor.fetchone()[0]
            
            # Tasdiqlanmagan to'lovlar
            cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "pending"')
            pending_payments = cursor.fetchone()[0]
            
            # Kunlik to'lovlar (bugun)
            cursor.execute('SELECT COALESCE(SUM(amount_rub), 0) FROM daily_fees WHERE payment_date = DATE("now")')
            daily_fees = cursor.fetchone()[0]
            
            stats_text = f"""
📊 *Admin Statistika*

👥 *Foydalanuvchilar:*
• Jami: {total_users}
• Faol (7 kun): {active_users}

💰 *Moliya:*
• Umumiy balans: {total_balance} RUB
• Kunlik to'lovlar: {daily_fees} RUB

🔑 *VPN Kalitlar:*
• Aktiv: {active_keys}

⏳ *Kutilayotgan:*
• To'lovlar: {pending_payments}

📈 *O'rtacha kunlik:*
• Yangi foydalanuvchilar: ...
• To'lovlar: ...
            """
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_stats"),
                     InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
                ]
            )
            
            await callback.message.edit_text(stats_text, reply_markup=keyboard, parse_mode="Markdown")
            await callback.answer()
            
    except Exception as e:
        logger.error(f"❌ Admin stats error: {e}")
        await callback.answer("❌ Statistika olishda xatolik!", show_alert=True)

@router.callback_query(F.data == "admin_payments")
@admin_only
async def admin_payments_list(callback: CallbackQuery):
    """Tasdiqlanmagan to'lovlar ro'yxati"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT p.id, p.user_id, u.username, u.first_name, 
                   p.amount_rub, p.payment_type, p.created_at, p.screenshot_id
            FROM payments p
            JOIN users u ON p.user_id = u.telegram_id
            WHERE p.status = 'pending'
            ORDER BY p.created_at DESC
            LIMIT 20
            ''')
            
            payments = cursor.fetchall()
            
            if not payments:
                await callback.message.edit_text(
                    "📭 *Tasdiqlanmagan to'lovlar yo'q*",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
                        ]
                    ),
                    parse_mode="Markdown"
                )
                await callback.answer()
                return
            
            response = "⏳ *Tasdiqlanmagan to'lovlar:*\n\n"
            
            for payment in payments[:10]:  # Faqat 10 tasini ko'rsatish
                response += f"""
🔢 *ID:* `{payment[0]}`
👤 *Foydalanuvchi:* {payment[3]} (@{payment[2] or 'nousername'})
💰 *Summa:* {payment[4]} RUB
📦 *Tur:* {payment[5]}
📅 *Vaqt:* {payment[6].split()[0]}
                """
                response += "➖➖➖➖➖➖➖\n"
            
            # Inline keyboard
            keyboard_buttons = []
            row = []
            for payment in payments[:6]:  # Faqat 6 tasi uchun tugma
                row.append(
                    InlineKeyboardButton(
                        text=f"✅ {payment[0]}",
                        callback_data=f"approve_{payment[0]}"
                    )
                )
                if len(row) == 2:  # Har qatorda 2 ta tugma
                    keyboard_buttons.append(row)
                    row = []
            
            if row:
                keyboard_buttons.append(row)
            
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_payments"),
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            
            await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")
            await callback.answer()
            
    except Exception as e:
        logger.error(f"❌ Admin payments error: {e}")
        await callback.answer("❌ To'lovlarni olishda xatolik!", show_alert=True)

@router.callback_query(F.data.startswith("approve_"))
@admin_only
async def approve_payment_callback(callback: CallbackQuery):
    """To'lovni tasdiqlash"""
    try:
        payment_id = int(callback.data.split("_")[1])
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT user_id, amount_rub, payment_type 
            FROM payments 
            WHERE id = ? AND status = 'pending'
            ''', (payment_id,))
            
            payment = cursor.fetchone()
            
            if not payment:
                await callback.answer("❌ To'lov topilmadi yoki allaqachon tasdiqlangan", show_alert=True)
                return
            
            user_id = payment[0]
            amount = payment[1]
            payment_type = payment[2]
            
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
            
            # Foydalanuvchiga xabar
            try:
                await callback.bot.send_message(
                    user_id,
                    f"""
✅ *To'lovingiz tasdiqlandi!*

💰 *Summa:* {amount} RUB
📊 *Status:* ✅ Tasdiqlandi
⏰ *Vaqt:* {datetime.now().strftime('%Y-%m-%d %H:%M')}

💎 Endi VPN kalit yaratishingiz mumkin!
                    """,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"❌ Notification error: {e}")
            
            await callback.answer(f"✅ To'lov tasdiqlandi! ID: {payment_id}")
            
            # Yangilangan ro'yxatni ko'rsatish
            await admin_payments_list(callback)
            
    except Exception as e:
        logger.error(f"❌ Approve payment error: {e}")
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)

@router.message(Command("approve"))
@admin_only
async def approve_payment_command(message: Message):
    """Komanda orqali to'lovni tasdiqlash"""
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Format: /approve <payment_id>")
            return
        
        payment_id = int(args[1])
        
        # Yuqoridagi approve funksiyasini chaqirish
        from aiogram.types import CallbackQuery
        
        # Mock callback object yaratish
        class MockCallback:
            def __init__(self, bot, message):
                self.bot = bot
                self.message = message
                self.from_user = message.from_user
                self.data = f"approve_{payment_id}"
        
        mock_callback = MockCallback(message.bot, message)
        await approve_payment_callback(mock_callback)
        
    except ValueError:
        await message.answer("❌ Noto'g'ri ID! ID raqam bo'lishi kerak.")
    except Exception as e:
        logger.error(f"❌ Approve command error: {e}")
        await message.answer(f"❌ Xatolik: {str(e)}")

@router.callback_query(F.data == "admin_users")
@admin_only
async def admin_users_list(callback: CallbackQuery):
    """Foydalanuvchilar ro'yxati"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT telegram_id, username, first_name, balance_rub, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 20
            ''')
            
            users = cursor.fetchall()
            
            response = "👥 *Foydalanuvchilar ro'yxati:*\n\n"
            
            for i, user in enumerate(users, 1):
                response += f"""
{i}. *{user[2]}* (@{user[1] or 'nousername'})
   💰 Balans: {user[3]} RUB
   🆔 ID: `{user[0]}`
   📅 {user[4].split()[0]}
                """
                response += "➖➖➖➖➖➖➖\n"
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_users"),
                     InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
                ]
            )
            
            await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")
            await callback.answer()
            
    except Exception as e:
        logger.error(f"❌ Admin users error: {e}")
        await callback.answer("❌ Foydalanuvchilarni olishda xatolik!", show_alert=True)

@router.callback_query(F.data == "admin_broadcast")
@admin_only
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Broadcast boshlash"""
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.message.edit_text(
        "📢 *Broadcast xabarini yuboring:*\n\n"
        "Xabar matnini yuboring yoki /cancel buyrug'i bilan bekor qiling.",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(BroadcastState.waiting_for_message)
@admin_only
async def broadcast_process(message: Message, state: FSMContext):
    """Broadcast xabarini qayta ishlash"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Broadcast bekor qilindi.")
        return
    
    broadcast_text = message.text
    
    try:
        await message.answer("⏳ Xabar foydalanuvchilarga yuborilmoqda...")
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT telegram_id FROM users')
            users = cursor.fetchall()
        
        success_count = 0
        fail_count = 0
        
        for user in users:
            try:
                await message.bot.send_message(
                    user[0],
                    f"📢 *Xabar admin dan:*\n\n{broadcast_text}",
                    parse_mode="Markdown"
                )
                success_count += 1
                # 100 ms kutish, rate limit uchun
                import asyncio
                await asyncio.sleep(0.1)
            except Exception as e:
                fail_count += 1
                logger.error(f"❌ Send to {user[0]} failed: {e}")
        
        await state.clear()
        await message.answer(
            f"""
✅ *Broadcast yakunlandi!*

📊 *Natijalar:*
• Muvaffaqiyatli: {success_count}
• Xatolik: {fail_count}
• Jami: {success_count + fail_count}
            """,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"❌ Broadcast error: {e}")
        await state.clear()
        await message.answer("❌ Broadcast xabarida xatolik!")

@router.callback_query(F.data == "admin_create_key")
@admin_only
async def admin_create_key_menu(callback: CallbackQuery):
    """Admin uchun VPN kalit yaratish menyusi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔑 Kalit yaratish", callback_data="create_key_direct")],
            [InlineKeyboardButton(text="📋 Kalitlar ro'yxati", callback_data="list_keys_admin")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
        ]
    )
    
    await callback.message.edit_text(
        "🔑 *VPN Kalit boshqaruv*\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_back")
@admin_only
async def back_to_admin_panel(callback: CallbackQuery):
    """Admin paneliga qaytish"""
    await admin_panel(callback.message)

@router.message(Command("stats"))
@admin_only
async def quick_stats(message: Message):
    """Tezkor statistika"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(balance_rub) FROM users')
            total_balance = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "pending"')
            pending = cursor.fetchone()[0]
            
            response = f"""
📊 *Tezkor Statistika*

👥 Foydalanuvchilar: {total_users}
💰 Umumiy balans: {total_balance} RUB
⏳ Kutilayotgan: {pending}
            """
            
            await message.answer(response, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"❌ Quick stats error: {e}")
        await message.answer("❌ Statistika olishda xatolik!")

@router.message(Command("users"))
@admin_only
async def quick_users(message: Message):
    """Tezkor foydalanuvchilar"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT telegram_id, username, first_name, balance_rub
            FROM users
            ORDER BY created_at DESC
            LIMIT 10
            ''')
            
            users = cursor.fetchall()
            
            response = "👥 *So'nggi 10 foydalanuvchi:*\n\n"
            
            for user in users:
                response += f"• {user[2]} (@{user[1] or 'nousername'}) - {user[3]} RUB\n"
            
            await message.answer(response, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"❌ Quick users error: {e}")
        await message.answer("❌ Foydalanuvchilarni olishda xatolik!")
