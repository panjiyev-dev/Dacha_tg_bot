from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from bot.states import AuthStates
from database.setup import async_session
from database.models import User, ActivationCode, Admin
from config import ADMIN_CODES
from sqlalchemy import select
from datetime import datetime, timedelta

router = Router()

@router.message(AuthStates.entering_code)
async def process_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    user_id = message.from_user.id
    
    # Check Admin
    # Note: In production, better to verify ADMIN_CODES securely or via specific command
    if code in ADMIN_CODES:
        async with async_session() as session:
            # Upsert Admin
            res = await session.execute(select(Admin).where(Admin.user_id == user_id))
            if not res.scalar_one_or_none():
                session.add(Admin(user_id=user_id))
            
            # Also ensure Admin has a User record for Ad creation
            user_res = await session.execute(select(User).where(User.user_id == user_id))
            user = user_res.scalar_one_or_none()
            if not user:
                data = await state.get_data()
                lang = data.get('language', 'ru')
                user = User(user_id=user_id, language=lang)
                session.add(user)
            
            # Admin gets 100 years of subscription for testing
            user.subscription_end_date = datetime.utcnow() + timedelta(days=36500)
            await session.commit()
                
        from bot.utils.i18n import i18n
        data = await state.get_data()
        lang = data.get('language', 'ru')
        
        kb = [
            [types.KeyboardButton(text=i18n.get("create_ad", lang))],
            [types.KeyboardButton(text=i18n.get("my_ads", lang))]
        ]
        
        await message.answer("✅ Admin access granted!\nUsage: /settings, /generate_code, /user_ads", 
                             reply_markup=types.ReplyKeyboardMarkup(
                                 keyboard=kb,
                                 resize_keyboard=True
                             ))
        await state.clear()
        return

    # Check Activation Code
    async with async_session() as session:
        result = await session.execute(select(ActivationCode).where(ActivationCode.code == code, ActivationCode.is_used == False))
        activation_code = result.scalar_one_or_none()
        
        if activation_code:
            # Check if code is expired (must be used within 24 hours)
            if datetime.utcnow() > activation_code.created_at + timedelta(hours=24):
                await message.answer("Этот код активации истек (был годен 24 часа). Обратитесь к админу.")
                return

            # Grant Subscription
            activation_code.is_used = True
            activation_code.used_by = user_id
            activation_code.used_at = datetime.utcnow()
            
            # Upsert User
            user_res = await session.execute(select(User).where(User.user_id == user_id))
            user = user_res.scalar_one_or_none()
            if not user:
                # Get lang from state if possible, default ru
                data = await state.get_data()
                lang = data.get('language', 'ru')
                user = User(user_id=user_id, language=lang)
                session.add(user)
            
            # Grant 24 hours
            end_date = datetime.utcnow() + timedelta(hours=24)
            user.subscription_end_date = end_date
            
            await session.commit()
            
            from bot.utils.i18n import i18n
            data = await state.get_data()
            lang = data.get('language', 'ru')
            
            kb = [
                [types.KeyboardButton(text=i18n.get("create_ad", lang))],
                [types.KeyboardButton(text=i18n.get("my_ads", lang))]
            ]
            keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
            
            date_str = end_date.strftime("%d.%m.%Y %H:%M")
            await message.answer(i18n.get("sub_active", lang, date=date_str), reply_markup=keyboard, parse_mode="HTML")
            await state.clear()
        else:
            data = await state.get_data()
            lang = data.get('language', 'ru')
            from bot.utils.i18n import i18n
            await message.answer(i18n.get("invalid_code", lang), parse_mode="HTML")
