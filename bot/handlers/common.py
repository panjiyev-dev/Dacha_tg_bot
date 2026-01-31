# common.py
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.states import AuthStates
import json
import os
from database.setup import async_session
from database.models import User
from sqlalchemy import select, update

router = Router()

# Simple locale loader (can be improved with middleware)
def load_locale(lang_code):
    try:
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'locales', f'{lang_code}.json')
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

from bot.utils.i18n import i18n

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    # Language Selection Keyboard
    kb = [
        [types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [types.InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [types.InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    
    welcome_text = (
        "🌟 <b>Welcome to Dacha Live!</b>\n"
        "───────────────────\n\n"
        "Пожалуйста, выберите язык:\n"
        "Iltimos, tilni tanlang:\n"
        "Please choose your language:"
    )
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(AuthStates.choosing_lang)

@router.message(Command("language"))
async def cmd_language(message: types.Message, state: FSMContext):
    await state.clear()
    kb = [
        [types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [types.InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [types.InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer("🌐 <b>Select Language / Выберите язык / Tilni tanlang:</b>", reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(AuthStates.choosing_lang)
    await state.update_data(updating_lang=True)

@router.callback_query(AuthStates.choosing_lang, F.data.startswith("lang_"))
async def language_chosen(callback: types.CallbackQuery, state: FSMContext):
    lang_code = callback.data.split("_")[1]
    data = await state.get_data()
    is_updating = data.get('updating_lang', False)
    
    async with async_session() as session:
        await session.execute(update(User).where(User.user_id == callback.from_user.id).values(language=lang_code))
        await session.commit()
    
    if is_updating:
        kb = [
            [types.KeyboardButton(text=i18n.get("create_ad", lang_code))],
            [types.KeyboardButton(text=i18n.get("my_ads", lang_code))]
        ]
        await callback.message.answer(i18n.get("lang_updated", lang_code), 
                                     reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
        await callback.message.delete()
        await state.clear()
    else:
        await state.update_data(language=lang_code)
        await callback.message.answer(i18n.get("enter_code", lang_code), parse_mode="HTML")
        await callback.message.delete()
        await state.set_state(AuthStates.entering_code)

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    from bot.handlers.ad_creation import get_user_lang, is_admin
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    text = i18n.get("help_user", lang)
    if await is_admin(user_id):
        text += f"\n\n{i18n.get('help_admin', lang)}"
    
    await message.answer(text, parse_mode="HTML")
