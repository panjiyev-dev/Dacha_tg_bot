# middlewares/core.py
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from database.setup import async_session
from database.models import User
from sqlalchemy import select
import json
import os

import logging

class I18nMiddleware(BaseMiddleware):
    def __init__(self):
        self.locales = {}
        locales_path = os.path.join(os.path.dirname(__file__), '..', '..', 'locales')
        for lang in ['ru', 'uz', 'en']:
            try:
                with open(os.path.join(locales_path, f'{lang}.json'), 'r', encoding='utf-8') as f:
                    self.locales[lang] = json.load(f)
            except Exception as e:
                logging.error(f"Error loading locale {lang}: {e}")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get('event_from_user')
        lang = 'ru'
        
        if user:
            try:
                async with async_session() as session:
                    res = await session.execute(select(User).where(User.user_id == user.id))
                    db_user = res.scalar_one_or_none()
                    if db_user:
                        lang = db_user.language or 'ru'
            except Exception as e:
                logging.error(f"DB Error in I18nMiddleware: {e}")
        
        data['lang'] = lang
        data['texts'] = self.locales.get(lang, self.locales.get('ru', {}))
        return await handler(event, data)

class AuthCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, (Message, CallbackQuery)) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        try:
            async with async_session() as session:
                res = await session.execute(select(User).where(User.user_id == user_id))
                db_user = res.scalar_one_or_none()
                
                if db_user and db_user.is_blocked:
                    if isinstance(event, Message):
                        from bot.utils.i18n import i18n
                        lang = db_user.language or 'ru'
                        msg = (
                            "🚫 <b>Доступ ограничен</b>\n"
                            "───────────────────\n\n"
                            "Ваш аккаунт был заблокирован администратором.\n"
                            "Для выяснения причин обратитесь в поддержку." if lang == 'ru' else \
                            "Sizning hisobingiz administrator tomonidan bloklangan." if lang == 'uz' else \
                            "Your account has been blocked by the administrator."
                        )
                        await event.answer(msg, parse_mode="HTML")
                    return
        except Exception as e:
            logging.error(f"DB Error in AuthCheckMiddleware: {e}")

        return await handler(event, data)
