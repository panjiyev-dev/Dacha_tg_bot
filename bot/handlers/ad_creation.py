# ad_creation.py
from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from bot.states import AdCreationStates
from database.setup import async_session
from database.models import User, Ad, Admin
from sqlalchemy import select, update
from datetime import datetime, timedelta
import os

from bot.utils.i18n import i18n

from database.setup import async_session
from bot.utils.ad_limits import has_free_slot, MAX_ADS_PER_USER

router = Router()

async def is_admin(user_id: int) -> bool:
    async with async_session() as session:
        res = await session.execute(select(Admin).where(Admin.user_id == user_id))
        return res.scalar_one_or_none() is not None

def get_kb(buttons: list):
    return types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text=b) for b in row] for row in buttons], resize_keyboard=True)

async def get_user_lang(user_id: int) -> str:
    async with async_session() as session:
        res = await session.execute(select(User).where(User.user_id == user_id))
        user = res.scalar_one_or_none()
        return user.language if user else 'ru'

@router.message(StateFilter(None), Command("create_ad"))
@router.message(StateFilter(None), or_f(F.text == "📝 Создать объявление", F.text == "📝 E'lon yaratish", F.text == "📝 Create Ad"))
async def start_ad_creation(message: types.Message, state: FSMContext, lang: str):
    user_id = message.from_user.id
    
    async with async_session() as session:
        user_res = await session.execute(select(User).where(User.user_id == user_id))
        user = user_res.scalar_one_or_none()

        if not await has_free_slot(session, message.from_user.id):
            await message.answer(
                f"❌ Sizda hozir {MAX_ADS_PER_USER} ta e’lon tekshiruvda yoki faol.\n"
                "Limit bo‘shashi uchun admin e’londan birini rad etishi yoki o‘chirishi kerak."
            )
            return
        
        if await is_admin(user_id):
            if not user:
                user = User(user_id=user_id, language=lang, subscription_end_date=datetime.utcnow() + timedelta(days=36500))
                session.add(user)
                await session.flush()
        else:
            if not user or not user.subscription_end_date or user.subscription_end_date < datetime.utcnow():
                  await message.answer(i18n.get("sub_expired", lang), parse_mode="HTML")
                  return
            
        if not await has_free_slot(session, user_id):
            await message.answer(
                f"❌ Sizda hozir {MAX_ADS_PER_USER} ta e’lon tekshiruvda yoki faol.\n"
                "Limit bo‘shashi uchun admin e’londan birini rad etishi yoki o‘chirishi kerak."
            )
            return

        if user.draft_id:
             kb = [[i18n.get("btn_continue", lang), i18n.get("btn_start_over", lang)]]
             await message.answer(i18n.get("draft_prompt", lang), reply_markup=get_kb(kb))
             await state.set_state(AdCreationStates.managing_draft)
             return

        new_ad = Ad(user_id=user_id, status='draft', language=lang)
        session.add(new_ad)
        await session.flush()
        user.draft_id = new_ad.id
        await session.commit()
        await state.update_data(ad_id=new_ad.id)
        
    await message.answer(i18n.get("step_1_title", lang), reply_markup=types.ReplyKeyboardRemove(), parse_mode="HTML")
    await state.set_state(AdCreationStates.title)

@router.message(AdCreationStates.managing_draft)
async def handle_draft_choice(message: types.Message, state: FSMContext, lang: str):
    user_id = message.from_user.id
    choice = message.text
    
    async with async_session() as session:
        user_res = await session.execute(select(User).where(User.user_id == user_id))
        user = user_res.scalar_one()
        
        if choice == i18n.get("btn_continue", lang):
            ad_id = user.draft_id
            await state.update_data(ad_id=ad_id)
            ad_res = await session.execute(select(Ad).where(Ad.id == ad_id))
            ad = ad_res.scalar_one()
            
            if not ad.title:
                await message.answer(i18n.get("step_1_title", lang), reply_markup=types.ReplyKeyboardRemove(), parse_mode="HTML")
                await state.set_state(AdCreationStates.title)
            elif not ad.description:
                await message.answer(i18n.get("step_2_desc", lang), reply_markup=types.ReplyKeyboardRemove(), parse_mode="HTML")
                await state.set_state(AdCreationStates.description)
            elif not ad.price:
                await message.answer(i18n.get("step_3_price", lang), reply_markup=types.ReplyKeyboardRemove(), parse_mode="HTML")
                await state.set_state(AdCreationStates.price)
            elif not ad.photos or len(ad.photos) < 4:
                count = len(ad.photos or [])
                await message.answer(i18n.get("step_4_photos", lang) + f"\n\n📊 <i>{count}/6</i>", 
                                     reply_markup=get_kb([[i18n.get("btn_done", lang)]]), parse_mode="HTML")
                await state.set_state(AdCreationStates.photos)
            else:
                await message.answer(i18n.get("step_5_phone", lang), reply_markup=types.ReplyKeyboardRemove(), parse_mode="HTML")
                await state.set_state(AdCreationStates.phone)
                
        elif choice == i18n.get("btn_start_over", lang):
            user.draft_id = None
            await session.commit()
            await start_ad_creation(message, state, lang)

@router.message(AdCreationStates.title, F.text)
async def process_title(message: types.Message, state: FSMContext, lang: str):
    data = await state.get_data()
    ad_id = data.get('ad_id')
    async with async_session() as session:
        await session.execute(update(Ad).where(Ad.id == ad_id).values(title=message.text))
        await session.commit()
    await message.answer(i18n.get("step_2_desc", lang), parse_mode="HTML")
    await state.set_state(AdCreationStates.description)

@router.message(AdCreationStates.description, F.text)
async def process_desc(message: types.Message, state: FSMContext, lang: str):
    data = await state.get_data()
    ad_id = data.get('ad_id')
    async with async_session() as session:
        await session.execute(update(Ad).where(Ad.id == ad_id).values(description=message.text))
        await session.commit()
    await message.answer(i18n.get("step_3_price", lang), parse_mode="HTML")
    await state.set_state(AdCreationStates.price)

@router.message(AdCreationStates.price, F.text)
async def process_price(message: types.Message, state: FSMContext, lang: str):
    data = await state.get_data()
    ad_id = data.get('ad_id')
    async with async_session() as session:
        await session.execute(update(Ad).where(Ad.id == ad_id).values(price=message.text))
        await session.commit()
    
    photos = data.get('photos', [])
    await message.answer(i18n.get("step_4_photos", lang) + f"\n\n📊 <i>{len(photos)}/6</i>", 
                         reply_markup=get_kb([[i18n.get("btn_done", lang)]]), parse_mode="HTML")
    await state.set_state(AdCreationStates.photos)

@router.message(AdCreationStates.photos, F.photo)
async def process_photos(message: types.Message, state: FSMContext, lang: str):
    data = await state.get_data()
    photos = data.get('photos', [])
    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(photos=photos)

    count = len(photos)
    done_kb = get_kb([[i18n.get("btn_done", lang)]])

    if count < 4:
        await message.answer(
            i18n.get("photo_min_needed", lang, count=count, needed=4-count),
            reply_markup=done_kb
        )
    elif count < 6:
        await message.answer(
            i18n.get("photo_progress", lang, count=count),
            reply_markup=done_kb
        )
    else:
        await message.answer(
            i18n.get("photo_max", lang),
            reply_markup=done_kb
        )
@router.message(AdCreationStates.photos, or_f(F.text == i18n.get("btn_done", "ru"), F.text == i18n.get("btn_done", "uz"), F.text == i18n.get("btn_done", "en")))
@router.message(AdCreationStates.photos, Command("done"))
async def photos_done(message: types.Message, state: FSMContext, lang: str):
    data = await state.get_data()
    photos = data.get('photos', [])
    ad_id = data.get('ad_id')
    if len(photos) < 4:
         await message.answer("Min 4 📸")
         return
    async with async_session() as session:
        await session.execute(update(Ad).where(Ad.id == ad_id).values(photos=photos))
        await session.commit()
    await message.answer(i18n.get("step_5_phone", lang), reply_markup=types.ReplyKeyboardRemove(), parse_mode="HTML")
    await state.set_state(AdCreationStates.phone)

@router.message(AdCreationStates.phone, F.text)
async def process_phone(message: types.Message, state: FSMContext, lang: str):
    data = await state.get_data()
    ad_id = data.get('ad_id')
    user_id = message.from_user.id

    async with async_session() as session:
        # ✅ 1) Adni tekshirib olamiz
        ad_res = await session.execute(select(Ad).where(Ad.id == ad_id))
        ad = ad_res.scalar_one_or_none()
        if not ad:
            await message.answer("E’lon topilmadi.")
            return

        # ✅ 2) Limit tekshiruvi (faqat draft -> pending qilayotganda)
        # Agar bu ad allaqachon pending/active bo'lsa, qayta sanamaymiz
        if ad.status == "draft":
            if not await has_free_slot(session, user_id):
                await message.answer(
                    f"❌ Limit tugagan: {MAX_ADS_PER_USER} ta e’lon pending/active.\n"
                    "Admin rad etsa yoki o‘chirsa limit qaytadi."
                )
                return

        # ✅ 3) Endi draftni pendingga o'tkazamiz
        await session.execute(
            update(Ad).where(Ad.id == ad_id).values(
                phone=message.text,
                status='pending'
            )
        )

        await session.execute(
            update(User).where(User.user_id == user_id).values(draft_id=None)
        )
        await session.commit()

    # Notify admins
    try:
        from bot.handlers.admin import notify_admins_new_ad
        await notify_admins_new_ad(message.bot, ad_id)
    except Exception as e:
        print(f"DEBUG: Failed to notify admins: {e}")

    kb = [
        [types.KeyboardButton(text=i18n.get("create_ad", lang))],
        [types.KeyboardButton(text=i18n.get("my_ads", lang))]
    ]
    await message.answer(
        i18n.get("ad_submitted", lang),
        reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    await state.clear()

# async def process_phone(message: types.Message, state: FSMContext, lang: str):
#     data = await state.get_data()
#     ad_id = data.get('ad_id')
    
#     async with async_session() as session:
#         await session.execute(update(Ad).where(Ad.id == ad_id).values(phone=message.text, status='pending'))
#         await session.execute(update(User).where(User.user_id == message.from_user.id).values(draft_id=None))
#         await session.commit()
    
#     # Notify admins
#     try:
#         from bot.handlers.admin import notify_admins_new_ad
#         await notify_admins_new_ad(message.bot, ad_id)
#     except Exception as e:
#         print(f"DEBUG: Failed to notify admins: {e}")
    
#     # Main menu keyboard
#     kb = [
#         [types.KeyboardButton(text=i18n.get("create_ad", lang))],
#         [types.KeyboardButton(text=i18n.get("my_ads", lang))]
#     ]
#     await message.answer(i18n.get("ad_submitted", lang), 
#                          reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True), 
#                          parse_mode="HTML")
#     await state.clear()
    
# @router.message(or_f(F.text == "🗂️ Мои объявления", F.text == "🗂️ Mening e'lonlarim", F.text == "🗂️ My Ads"))
# async def cmd_my_ads(message: types.Message, lang: str):
#     user_id = message.from_user.id
    
#     async with async_session() as session:
#         res = await session.execute(select(Ad).where(Ad.user_id == user_id, Ad.status != 'deleted'))
#         ads = res.scalars().all()
        
#         if not ads:
#             await message.answer(i18n.get("no_ads", lang))
#             return
            
#         await message.answer(f"🗂️ <b>{i18n.get('my_ads', lang)}:</b>", parse_mode="HTML")
#         for ad in ads:
#             status_emoji = "⏳" if ad.status == "pending" else "✅" if ad.status == "active" else "❌"
#             card = i18n.get("ad_card", lang, 
#                               title=ad.title or "---", 
#                               status=f"{status_emoji} {ad.status.upper()}", 
#                               price=ad.price or "---",
#                               id=ad.id)
            
#             kb = types.InlineKeyboardMarkup(inline_keyboard=[
#                 [types.InlineKeyboardButton(text=i18n.get("delete_btn", lang), callback_data=f"user_delete_ad_{ad.id}")]
#             ])
#             await message.answer(card, reply_markup=kb, parse_mode="HTML")

@router.message(or_f(F.text == "🗂️ Мои объявления", F.text == "🗂️ Mening e'lonlarim", F.text == "🗂️ My Ads"))
async def cmd_my_ads(message: types.Message, lang: str):
    from bot.handlers.admin import is_admin as is_admin_check  # import ichida, circular bo‘lmasin
    user_id = message.from_user.id
    is_admin_user = await is_admin_check(user_id)

    async with async_session() as session:
        res = await session.execute(select(Ad).where(Ad.user_id == user_id, Ad.status != 'deleted'))
        ads = res.scalars().all()

        if not ads:
            await message.answer(i18n.get("no_ads", lang))
            return

        await message.answer(f"🗂️ <b>{i18n.get('my_ads', lang)}:</b>", parse_mode="HTML")

        for ad in ads:
            status_emoji = "⏳" if ad.status == "pending" else "✅" if ad.status == "active" else "❌"
            card = i18n.get(
                "ad_card",
                lang,
                title=ad.title or "---",
                status=f"{status_emoji} {ad.status.upper()}",
                price=ad.price or "---",
                id=ad.id
            )

            # ✅ ADMIN bo‘lsa — admin tugmalari
            if is_admin_user:
                rows = []

                # pending bo‘lsa approve/reject chiqsin, active bo‘lsa approve chiqmasin
                if ad.status != "active":
                    rows.append([types.InlineKeyboardButton(
                        text=i18n.get("btn_approve", lang),
                        callback_data=f"approve_{ad.id}"
                    )])

                rows.append([types.InlineKeyboardButton(
                    text=i18n.get("btn_reject", lang),
                    callback_data=f"reject_{ad.id}"
                )])

                rows.append([types.InlineKeyboardButton(
                    text=i18n.get("btn_delete", lang),
                    callback_data=f"delete_ad_{ad.id}"
                )])

                kb = types.InlineKeyboardMarkup(inline_keyboard=rows)
                await message.answer(card, reply_markup=kb, parse_mode="HTML")

            # ✅ Oddiy USER bo‘lsa — faqat o‘chirish
            else:
                kb = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text=i18n.get("delete_btn", lang),
                        callback_data=f"user_delete_ad_{ad.id}"
                    )]
                ])
                await message.answer(card, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("user_delete_ad_"))
async def user_delete_ad_confirm(callback: types.CallbackQuery, lang: str):
    ad_id = int(callback.data.split("_")[-1])
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text=i18n.get("delete_yes", lang), callback_data=f"confirm_delete_{ad_id}"),
            types.InlineKeyboardButton(text=i18n.get("delete_no", lang), callback_data="cancel_delete")
        ]
    ])
    await callback.message.edit_text(i18n.get("confirm_delete", lang), reply_markup=kb)

@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_ad(callback: types.CallbackQuery, lang: str):
    ad_id = int(callback.data.split("_")[-1])
    
    async with async_session() as session:
        await session.execute(update(Ad).where(Ad.id == ad_id).values(status='deleted'))
        await session.commit()
    
    await callback.message.edit_text(i18n.get("ad_deleted", lang))
    await callback.answer()

@router.callback_query(F.data == "cancel_delete")
async def cancel_delete_ad(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer()
