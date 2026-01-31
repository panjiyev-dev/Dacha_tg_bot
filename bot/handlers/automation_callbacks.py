from aiogram import Router, types, F
from database.setup import async_session
from database.models import Ad
from sqlalchemy import update

router = Router()

@router.callback_query(F.data == "villa_free_yes")
async def villa_confirmed_free(callback: types.CallbackQuery):
    from bot.handlers.ad_creation import get_user_lang
    from bot.utils.i18n import i18n
    lang = await get_user_lang(callback.from_user.id)
    
    async with async_session() as session:
        from datetime import datetime
        await session.execute(
            update(Ad).where(Ad.user_id == callback.from_user.id, Ad.status == 'active')
            .values(last_confirmed_free=datetime.utcnow())
        )
        await session.commit()
    
    await callback.message.edit_text(i18n.get("check_confirm_yes", lang), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "villa_free_no")
async def villa_confirmed_busy(callback: types.CallbackQuery):
    from bot.handlers.ad_creation import get_user_lang
    from bot.utils.i18n import i18n
    lang = await get_user_lang(callback.from_user.id)
    
    await callback.message.edit_text(i18n.get("check_confirm_no", lang), parse_mode="HTML")
    await callback.answer()
