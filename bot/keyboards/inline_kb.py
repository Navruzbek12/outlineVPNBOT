def get_main_menu():
    """Asosiy menyu klaviaturasi"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🗝 VPN Kalit olish", callback_data="get_key")
    )
    
    builder.row(
        InlineKeyboardButton(text="💳 To'lov qilish", callback_data="payment_menu"),
        InlineKeyboardButton(text="📊 Statistikam", callback_data="my_stats")
    )
    
    builder.row(
        InlineKeyboardButton(text="👥 Referal", callback_data="referral"),
        InlineKeyboardButton(text="ℹ️ Qo'llanma", callback_data="tutorial")
    )
    
    return builder.as_markup()