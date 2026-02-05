# bot/handlers/__init__.py
from aiogram import Router
from .start import router as start_router
from .payment import router as payment_router
from .admin import router as admin_router
from .keys import router as keys_router
from .help import router as help_router
from .referral import router as referral_router 
def setup_routers():
    """Barcha routerlarni birlashtirish"""
    router = Router()
    
    # Routerlarni qo'shish (payment.py bo'lishi kerak, paymentS.py emas)
    router.include_router(start_router)
    router.include_router(payment_router)  # fayl nomi payment.py
    router.include_router(admin_router)
    router.include_router(keys_router)
    
    router.include_router(help_router)
    router.include_router(referral_router)
    return router
