# bot/handlers/help.py - YORDAM BO'LIMI
from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

router = Router()

def get_help_keyboard() -> InlineKeyboardMarkup:
    """Yordam menyusi tugmalari"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="❓ Ko'p beriladigan savollar", callback_data="faq_menu"),
        InlineKeyboardButton(text="📋 Buyruqlar ro'yxati", callback_data="commands_list")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔧 Texnik yordam", callback_data="tech_support"),
        InlineKeyboardButton(text="💰 To'lov tizimi", callback_data="payment_info")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔐 VPN qo'llanma", callback_data="vpn_guide"),
        InlineKeyboardButton(text="📱 Ilova o'rnatish", callback_data="app_install")
    )
    
    builder.row(
        InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")
    )
    
    return builder.as_markup()

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Yordam komandasi"""
    help_text = (
        "🆘 <b>Yordam markazi</b>\n\n"
        "Bu yerda siz botdan foydalanish bo'yicha barcha ma'lumotlarni topasiz. "
        "Quyidagi bo'limlardan birini tanlang:\n\n"
        
        "• <b>❓ Ko'p beriladigan savollar</b> - Eng ko'p so'raladigan savollarga javoblar\n"
        "• <b>📋 Buyruqlar ro'yxati</b> - Botning barcha buyruqlari\n"
        "• <b>🔧 Texnik yordam</b> - Muammolarni hal qilish yo'llari\n"
        "• <b>💰 To'lov tizimi</b> - Balans to'ldirish va to'lovlar haqida\n"
        "• <b>🔐 VPN qo'llanma</b> - VPN dan foydalanish bo'yicha qo'llanma\n"
        "• <b>📱 Ilova o'rnatish</b> - Outline ilovasini o'rnatish\n"
    )
    
    await message.answer(
        help_text,
        reply_markup=get_help_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(lambda c: c.data == "help_menu")
async def show_help_menu(callback: CallbackQuery):
    """Yordam menyusini ko'rsatish"""
    help_text = (
        "🆘 <b>Yordam markazi</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    
    await callback.message.edit_text(
        help_text,
        reply_markup=get_help_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "faq_menu")
async def show_faq(callback: CallbackQuery):
    """Ko'p beriladigan savollar"""
    faq_text = (
        "❓ <b>Ko'p beriladigan savollar (FAQ)</b>\n\n"
        
        "1. <b>VPN nima?</b>\n"
        "VPN (Virtual Private Network) - bu internet trafigingizni shifrlash va xavfsiz kanal orqali uzatish tizimi.\n\n"
        
        "2. <b>Nega VPN kerak?</b>\n"
        "• Internetda anonim qolish\n"
        "• Bloklangan saytlarga kirish\n"
        "• Jamoat Wi-Fi tarmoqlarida xavfsizlik\n"
        "• Geografik cheklovlarni chetlab o'tish\n\n"
        
        "3. <b>Qanday to'lov usullari mavjud?</b>\n"
        "• Bank kartasi orqali (Sberbank)\n"
        "• Balansingizni to'ldirib, kunlik avtomatik to'lov\n\n"
        
        "4. <b>Kunlik to'lov qancha?</b>\n"
        "Har kuni 00:00 da 5 RUB avtomatik yechiladi. Balans 5 RUB dan kam bo'lsa, VPN o'chiriladi.\n\n"
        
        "5. <b>VPN kalit qancha muddatga beriladi?</b>\n"
        "Har bir to'lov uchun 30 kun muddatda 1 ta VPN kalit beriladi.\n\n"
        
        "6. <b>Bir nechta qurilmada ishlata olamanmi?</b>\n"
        "Ha, bir xil kalit bilan bir nechta qurilmada foydalanish mumkin.\n\n"
        
        "7. <b>Tezlik cheklovlari bormi?</b>\n"
        "Yo'q, cheklovlar yo'q. Faqat oylik trafik limiti: 10GB.\n\n"
        
        "8. <b>Qanday ilova kerak?</b>\n"
        "Outline Client ilovasi (Google Play yoki App Store)."
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="help_menu"),
        InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        faq_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "commands_list")
async def show_commands(callback: CallbackQuery):
    """Buyruqlar ro'yxati"""
    commands_text = (
        "📋 <b>Bot buyruqlari ro'yxati</b>\n\n"
        
        "<b>Asosiy buyruqlar:</b>\n"
        "• /start - Botni ishga tushirish\n"
        "• /help - Yordam olish\n"
        "• /menu - Asosiy menyuni ochish\n\n"
        
        "<b>Profil va balans:</b>\n"
        "• /profile - Profil ma'lumotlari\n"
        "• /balance - Balansni ko'rish\n"
        "• /ref - Referal tizimi\n"
        "• /stats - Statistikani ko'rish\n\n"
        
        "<b>VPN va kalitlar:</b>\n"
        "• /vpn - VPN bo'limi\n"
        "• /mykeys - Mening kalitlarim\n"
        "• /getkey - Yangi kalit olish\n\n"
        
        "<b>To'lov va tariflar:</b>\n"
        "• /tariffs - Tariflar narxlari\n"
        "• /payment - To'lov qilish\n"
        "• /history - To'lovlar tarixi\n\n"
        
        "<b>Admin buyruqlari (faqat adminlar uchun):</b>\n"
        "• /admin - Admin paneli\n"
        "• /users - Foydalanuvchilar ro'yxati\n"
        "• /stats_full - To'liq statistika\n"
        "• /broadcast - Xabar yuborish"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="help_menu"),
        InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        commands_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "tech_support")
async def show_tech_support(callback: CallbackQuery):
    """Texnik yordam"""
    tech_text = (
        "🔧 <b>Texnik yordam</b>\n\n"
        
        "<b>Muammolarni hal qilish:</b>\n\n"
        
        "1. <b>VPN ulanmayapti:</b>\n"
        "• Internet aloqangizni tekshiring\n"
        "• Outline ilovasini qayta ishga tushiring\n"
        "• Kalitni qayta qo'shing\n"
        "• Ilovani yangilang\n\n"
        
        "2. <b>Kalit ishlamayapti:</b>\n"
        "• Kalit muddati tugagan bo'lishi mumkin\n"
        "• Balansingiz 5 RUB dan kam bo'lishi mumkin\n"
        "• Yangi kalit olishingiz kerak\n"
        "• Balansingizni to'ldiring\n\n"
        
        "3. <b>Bot javob bermayapti:</b>\n"
        "• Internet aloqangizni tekshiring\n"
        "• Botni /start qiling\n"
        "• Agar muammo davom etsa, admin bilan bog'laning\n\n"
        
        "4. <b>To'lov qabul qilinmadi:</b>\n"
        "• Karta ma'lumotlarini tekshiring\n"
        "• Bank to'lovni qayta ishlashda\n"
        "• Screenshot bilan admin bilan bog'laning\n\n"
        
        "<b>Admin bilan bog'lanish:</b>\n"
        "Muammo davom etsa, @navruzbek12 ga murojaat qiling.\n"
        "To'lov cheklarini va muammo tasvirini yuboring."
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="help_menu"),
        InlineKeyboardButton(text="📞 Admin", url="https://t.me/navruzbek12")
    )
    
    await callback.message.edit_text(
        tech_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "payment_info")
async def show_payment_info(callback: CallbackQuery):
    """To'lov tizimi haqida"""
    payment_text = (
        "💰 <b>To'lov tizimi</b>\n\n"
        
        "<b>To'lov usullari:</b>\n"
        "• Bank kartasi orqali (Sberbank)\n"
        "• Kartaga to'lov qilib, chekni yuborish\n"
        "• Admin to'lovni tasdiqlaydi\n"
        "• Balansingizga pul qo'shiladi\n\n"
        
        "<b>Karta ma'lumotlari:</b>\n"
        "• Bank: Sberbank\n"
        "• Karta raqami: 2202 2080 2246 0399\n"
        "• Karta egasi: Navruzbek Bobobekov\n\n"
        
        "<b>To'lov tartibi:</b>\n"
        "1. Yuqoridagi karta raqamiga to'lov qiling\n"
        "2. To'lov chekini (screenshot) yuboring\n"
        "3. To'lov miqdorini va tarifni yozing\n"
        "4. Admin 5-15 daqiqa ichida javob beradi\n"
        "5. Balansingizga pul qo'shiladi\n\n"
        
        "<b>Tarif narxlari:</b>\n"
        "• 1 oy: 150 RUB (30 kun)\n"
        "• 3 oy: 400 RUB (90 kun)\n"
        "• 1 yil: 1200 RUB (365 kun)\n\n"
        
        "<b>Kunlik to'lov:</b>\n"
        "• Har kuni 00:00 da 5 RUB yechiladi\n"
        "• Balans 5 RUB dan kam bo'lsa, VPN o'chiriladi\n"
        "• Yangi to'lov qilganingizda, VPN qayta yoqiladi"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 To'lov qilish", callback_data="payment_menu"),
        InlineKeyboardButton(text="📋 Tariflar", callback_data="tariffs_menu")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="help_menu"),
        InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        payment_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "vpn_guide")
async def show_vpn_guide(callback: CallbackQuery):
    """VPN qo'llanma"""
    guide_text = (
        "🔐 <b>VPN dan foydalanish qo'llanmasi</b>\n\n"
        
        "<b>1. Kalit olish:</b>\n"
        "• Balansingizni to'ldiring (kamida 5 RUB)\n"
        "• To'lov qiling\n"
        "• 'VPN Kalit olish' tugmasini bosing\n"
        "• Kalit avtomatik yaratiladi\n\n"
        
        "<b>2. Ilova o'rnatish:</b>\n"
        "• Google Play yoki App Store dan\n"
        "• 'Outline Client' ilovasini yuklang\n"
        "• Ilovani oching\n\n"
        
        "<b>3. Kalitni qo'shish:</b>\n"
        "• Ilovada '+' belgisini bosing\n"
        "• Bot bergan linkni joylang\n"
        "• 'Add' tugmasini bosing\n\n"
        
        "<b>4. VPN ni yoqish:</b>\n"
        "• Qo'shilgan kalitni tanlang\n"
        "• O'ngdagi tugmani yoqing\n"
        "• VPN faollashadi\n\n"
        
        "<b>5. Sozlamalar:</b>\n"
        "• Avtomatik ulanish: Yoqish tavsiya etiladi\n"
        "• Split tunneling: Kerakli dasturlarni tanlash\n"
        "• DNS: Avtomatik qoldiring\n\n"
        
        "<b>6. Tekshirish:</b>\n"
        "• VPN yoqilganda, yuqori panelda ikonka paydo bo'ladi\n"
        "• whatismyip.com saytida IP manzilingiz o'zgarganligini tekshiring\n"
        "• Bloklangan saytlarga kirishni sinab ko'ring"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📱 Ilova o'rnatish", callback_data="app_install"),
        InlineKeyboardButton(text="🗝 Kalit olish", callback_data="get_key")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="help_menu"),
        InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        guide_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "app_install")
async def show_app_install(callback: CallbackQuery):
    """Ilova o'rnatish"""
    app_text = (
        "📱 <b>Outline ilovasini o'rnatish</b>\n\n"
        
        "<b>Android (Google Play):</b>\n"
        "1. Google Play do'konini oching\n"
        "2. 'Outline Client' qidiring\n"
        "3. Jigsaw iconli ilovani tanlang\n"
        "4. 'O'rnatish' tugmasini bosing\n"
        "5. Ruxsat berish so'rovlarini qabul qiling\n\n"
        
        "<b>iOS (App Store):</b>\n"
        "1. App Store ni oching\n"
        "2. 'Outline' qidiring\n"
        "3. Jigsaw iconli ilovani tanlang\n"
        "4. 'O'rnatish' tugmasini bosing\n"
        "5. Ruxsat berish so'rovlarini qabul qiling\n\n"
        
        "<b>Windows:</b>\n"
        "1. outline.com saytiga o'ting\n"
        "2. 'Download' bo'limiga o'ting\n"
        "3. Windows uchun ilovani yuklab oling\n"
        "4. Faylni ochib o'rnating\n\n"
        
        "<b>macOS:</b>\n"
        "1. outline.com saytiga o'ting\n"
        "2. 'Download' bo'limiga o'ting\n"
        "3. Mac uchun ilovani yuklab oling\n"
        "4. .dmg faylini ochib o'rnating\n\n"
        
        "<b>Ilova haqida:</b>\n"
        "• Bepul va ochiq manbali\n"
        "• Shifrlangan aloqa\n"
        "• Tezkor va ishonchli\n"
        "• Bir nechta qurilmada ishlatish mumkin\n\n"
        
        "<b>Havolalar:</b>\n"
        "• Google Play: https://play.google.com/store/apps/details?id=org.outline.android.client\n"
        "• App Store: https://apps.apple.com/app/outline-app/id1356177741\n"
        "• Rasmiy sayt: https://getoutline.org/"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📲 Google Play", url="https://play.google.com/store/apps/details?id=org.outline.android.client"),
        InlineKeyboardButton(text="🍎 App Store", url="https://apps.apple.com/app/outline-app/id1356177741")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="help_menu"),
        InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        app_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

# Bu faylni saqlang va router ni asosiy faylga ulang
