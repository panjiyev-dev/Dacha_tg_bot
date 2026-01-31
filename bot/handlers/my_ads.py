# villa_bot/handlers/my_ads.py

# import types
# from aiogram import Router, F
# from aiogram.types import Message, CallbackQuery
# from aiogram.utils.keyboard import InlineKeyboardBuilder
# from sqlalchemy import select, update
# from sqlalchemy.ext.asyncio import AsyncSession
# from database.models import Ad
# from database.setup import async_session
# from bot.utils.permissions import is_admin
# from bot.utils.preview_utils import send_ad_preview
# from bot.utils.channel_utils import post_ad_to_channel

# from villa_bot.bot.permissions import is_admin
# from villa_bot.bot.preview_utils import send_ad_preview
# from villa_bot.bot.channel_utils import post_ad_to_channel

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Ad
from database.setup import async_session

from bot.permissions import is_admin
from bot.preview_utils import send_ad_preview
from bot.channel_utils import post_ad_to_channel

# Agar session olish boshqa joyda bo'lsa, shu importni o'zgartir:
# from villa_bot.db.session import get_session  # <-- SENDA qanday bo'lsa shunga mosla

router = Router()

# --------- Keyboard builders ---------

def kb_user_ad(ad_id: int):
    kb = InlineKeyboardBuilder()
    # kb.button(text="👁 Ko‘rish", callback_data=f"ad:view:{ad_id}")
    kb.button(text="🗑 O‘chirish", callback_data=f"ad:delete:{ad_id}")
    kb.adjust(2)
    return kb.as_markup()

def kb_admin_ad(ad_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="👁 Ko‘rish", callback_data=f"ad:view:{ad_id}")
    kb.button(text="✅ Tasdiqlash", callback_data=f"ad:approve:{ad_id}")
    kb.button(text="❌ Rad etish", callback_data=f"ad:reject:{ad_id}")
    kb.button(text="🗑 O‘chirish", callback_data=f"ad:delete:{ad_id}")
    kb.adjust(2, 2)
    return kb.as_markup()

def kb_preview_only_user(ad_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 O‘chirish", callback_data=f"ad:delete:{ad_id}")
    return kb.as_markup()

def kb_preview_only_admin(ad_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tasdiqlash", callback_data=f"ad:approve:{ad_id}")
    kb.button(text="❌ Rad etish", callback_data=f"ad:reject:{ad_id}")
    kb.button(text="🗑 O‘chirish", callback_data=f"ad:delete:{ad_id}")
    kb.adjust(2, 1)
    return kb.as_markup()

# --------- Helpers ---------

async def _get_ad(session: AsyncSession, ad_id: int) -> Ad | None:
    res = await session.execute(select(Ad).where(Ad.id == ad_id))
    return res.scalar_one_or_none()

# --------- Handlers ---------
# 1) "Mening e'lonlarim" (matn bo'yicha ham, button bo'yicha ham ishlashi uchun)
@router.message(F.text.in_(["📁 Mening e'lonlarim", "📁 Mening e’lonlarim", "Mening e'lonlarim", "Mening e’lonlarim"]))
# async def my_ads(message: Message):
#     async with get_session() as session:
#         admin = await is_admin(session, message.from_user.id)

#         # user o'z e'lonlari (deleted bo'lmagan)
#         res = await session.execute(
#             select(Ad).where(Ad.user_id == message.from_user.id, Ad.status != "deleted").order_by(Ad.id.desc())
#         )
#         ads = res.scalars().all()

#         if not ads:
#             await message.answer("Senda hozircha e’lon yo‘q.")
#             return

#         await message.answer(f"📁 Mening e’lonlarim: {len(ads)} ta\nQuyidan tanla:")

#         for ad in ads[:20]:
#             status = (getattr(ad, "status", "") or "").upper()
#             price = getattr(ad, "price", None)

#             text = f"🧾 ID: <b>#{ad.id}</b>\nHolati: <b>{status}</b>"
#             if price is not None:
#                 text += f"\nNarxi: <b>{price}</b>"

#             kb = kb_admin_ad(ad.id) if admin else kb_user_ad(ad.id)
#             await message.answer(text, reply_markup=kb, parse_mode="HTML")

# async def my_ads(message: types.Message):
#     async with async_session() as session:
#         res = await session.execute(
#             select(Ad).where(Ad.user_id == message.from_user.id)
#         )
#         ads = res.scalars().all()

#     if not ads:
#         await message.answer("📭 Sizda e'lonlar yo‘q")
#         return

#     for ad in ads:
#         status = "⏳ PENDING" if ad.status == "pending" else "✅ ACTIVE"

#         text = (
#             f"🏡 <b>{ad.title}</b>\n\n"
#             f"{ad.description}\n\n"
#             f"📞 {ad.phone}\n"
#             f"📌 Holati: <b>{status}</b>\n"
#             f"🆔 ID: #ad{ad.id}"
#         )

#         kb = types.InlineKeyboardMarkup(
#             inline_keyboard=[
#                 [types.InlineKeyboardButton(
#                     text="🗑 O‘chirish",
#                     callback_data=f"user_delete_{ad.id}"
#                 )]
#             ]
#         )

#         if ad.photos:
#             await message.answer_photo(ad.photos[0], caption=text, reply_markup=kb)
#         else:
#             await message.answer(text, reply_markup=kb)

async def my_ads(message: Message):
    async with async_session() as session:
        admin = await is_admin(session, message.from_user.id)

        res = await session.execute(
            select(Ad).where(Ad.user_id == message.from_user.id, Ad.status != "deleted").order_by(Ad.id.desc())
        )
        ads = res.scalars().all()

    await message.answer(f"DEBUG: admin={admin}, user_id={message.from_user.id}")
    
    if not ads:
        await message.answer("📭 Sizda e'lonlar yo‘q")
        return

    await message.answer(f"📁 Mening e'lonlarim: {len(ads)} ta")

    for ad in ads[:20]:
        kb = kb_admin_ad(ad.id) if admin else kb_user_ad(ad.id)
        
        status = (ad.status or "").upper()
        text = f"🧾 ID: <b>#{ad.id}</b>\nHolati: <b>{status}</b>"

        # Previewni ko‘rish uchun “Ko‘rish” button bo‘ladi, shuning uchun bu yerda rasm shart emas
        await message.answer(text, reply_markup=kb)

# 2) Ko‘rish (preview)
@router.callback_query(F.data.startswith("ad:view:"))
# async def ad_view(call: CallbackQuery):
#     ad_id = int(call.data.split(":")[-1])

#     async with get_session() as session:
#         ad = await _get_ad(session, ad_id)
#         if not ad:
#             await call.answer("E’lon topilmadi.", show_alert=True)
#             return

#         admin = await is_admin(session, call.from_user.id)

#         # User faqat o'z e'lonini ko'rsin, admin hammasini ko'rsin
#         if not admin and ad.user_id != call.from_user.id:
#             await call.answer("Bu e’lon senga tegishli emas.", show_alert=True)
#             return

#         kb = kb_preview_only_admin(ad_id) if admin else kb_preview_only_user(ad_id)

#         header = "👮 Admin ko‘rishi (preview)" if admin else "👁 E’lon ko‘rinishi (preview)"
#         await send_ad_preview(
#             bot=call.bot,
#             chat_id=call.message.chat.id,
#             ad=ad,
#             keyboard=kb,
#             header_text=header,
#         )
#         await call.answer()

async def ad_view(call: CallbackQuery):
    ad_id = int(call.data.split(":")[-1])

    async with async_session() as session:
        res = await session.execute(select(Ad).where(Ad.id == ad_id))
        ad = res.scalar_one_or_none()
        if not ad:
            await call.answer("E’lon topilmadi.", show_alert=True)
            return

        admin = await is_admin(session, call.from_user.id)

        if not admin and ad.user_id != call.from_user.id:
            await call.answer("Bu e’lon senga tegishli emas.", show_alert=True)
            return

    kb = kb_preview_only_admin(ad_id) if admin else kb_preview_only_user(ad_id)
    header = "👮 Admin ko‘rishi (preview)" if admin else "👁 E’lon ko‘rinishi (preview)"

    await send_ad_preview(
        bot=call.bot,
        chat_id=call.message.chat.id,
        ad=ad,
        keyboard=kb,
        header_text=header,
    )
    await call.answer()

# 3) O‘chirish
@router.callback_query(F.data.startswith("ad:delete:"))
# async def ad_delete(call: CallbackQuery):
#     ad_id = int(call.data.split(":")[-1])

#     async with get_session() as session:
#         ad = await _get_ad(session, ad_id)
#         if not ad:
#             await call.answer("E’lon topilmadi.", show_alert=True)
#             return

#         admin = await is_admin(session, call.from_user.id)
#         if not admin and ad.user_id != call.from_user.id:
#             await call.answer("Bu e’lonni o‘chira olmaysan.", show_alert=True)
#             return

#         # soft delete
#         await session.execute(update(Ad).where(Ad.id == ad_id).values(status="deleted"))
#         await session.commit()

#     await call.answer("🗑 O‘chirildi.", show_alert=True)
#     # ixtiyoriy: message ni ham o'chirish yoki edit qilish
#     try:
#         await call.message.edit_text("🗑 Bu e’lon o‘chirildi.")
#     except Exception:
#         pass

async def ad_delete(call: CallbackQuery):
    ad_id = int(call.data.split(":")[-1])

    async with async_session() as session:
        ad = await _get_ad(session, ad_id)
        if not ad:
            await call.answer("E’lon topilmadi.", show_alert=True)
            return

        admin = await is_admin(session, call.from_user.id)
        if not admin and ad.user_id != call.from_user.id:
            await call.answer("Bu e’lonni o‘chira olmaysan.", show_alert=True)
            return

        await session.execute(update(Ad).where(Ad.id == ad_id).values(status="deleted"))
        await session.commit()

    await call.answer("🗑 O‘chirildi.", show_alert=True)
    try:
        await call.message.edit_text("🗑 Bu e’lon o‘chirildi.")
    except Exception:
        pass


# 4) Tasdiqlash (FAqat admin)
@router.callback_query(F.data.startswith("ad:approve:"))
# async def ad_approve(call: CallbackQuery):
#     ad_id = int(call.data.split(":")[-1])

#     async with get_session() as session:
#         if not await is_admin(session, call.from_user.id):
#             await call.answer("Faqat admin tasdiqlay oladi.", show_alert=True)
#             return

#         ad = await _get_ad(session, ad_id)
#         if not ad:
#             await call.answer("E’lon topilmadi.", show_alert=True)
#             return

#         # status active
#         await session.execute(update(Ad).where(Ad.id == ad_id).values(status="active"))
#         await session.commit()

#         # kanalga yuborish
#         try:
#             await post_ad_to_channel(ad)  # channel_utils ichidagi funksiya
#         except Exception as e:
#             await call.answer(f"Kanalga yuborilmadi: {e}", show_alert=True)
#             return

#     await call.answer("✅ Tasdiqlandi va kanalga joylandi!", show_alert=True)
#     try:
#         await call.message.edit_text("✅ Tasdiqlandi va kanalga joylandi.")
#     except Exception:
#         pass

async def ad_approve(call: CallbackQuery):
    ad_id = int(call.data.split(":")[-1])

    async with async_session() as session:
        if not await is_admin(session, call.from_user.id):
            await call.answer("Faqat admin tasdiqlay oladi.", show_alert=True)
            return

        ad = await _get_ad(session, ad_id)
        if not ad:
            await call.answer("E’lon topilmadi.", show_alert=True)
            return

        await session.execute(update(Ad).where(Ad.id == ad_id).values(status="active"))
        await session.commit()

        try:
            # ⚠️ post_ad_to_channel sening utilingga qarab bot/session so‘rashi mumkin
            await post_ad_to_channel(call.bot, ad)  # agar funksiya (bot, ad) kutsa
            # yoki: await post_ad_to_channel(ad)  # agar faqat ad kutsa
        except Exception as e:
            await call.answer(f"Kanalga yuborilmadi: {e}", show_alert=True)
            return

    await call.answer("✅ Tasdiqlandi va kanalga joylandi!", show_alert=True)



# 5) Rad etish (FAqat admin)
@router.callback_query(F.data.startswith("ad:reject:"))
# async def ad_reject(call: CallbackQuery):
#     ad_id = int(call.data.split(":")[-1])

#     async with get_session() as session:
#         if not await is_admin(session, call.from_user.id):
#             await call.answer("Faqat admin rad eta oladi.", show_alert=True)
#             return

#         ad = await _get_ad(session, ad_id)
#         if not ad:
#             await call.answer("E’lon topilmadi.", show_alert=True)
#             return

#         await session.execute(update(Ad).where(Ad.id == ad_id).values(status="rejected"))
#         await session.commit()

#     await call.answer("❌ Rad etildi.", show_alert=True)
#     try:
#         await call.message.edit_text("❌ Rad etildi.")
#     except Exception:
#         pass

async def ad_reject(call: CallbackQuery):
    ad_id = int(call.data.split(":")[-1])

    async with async_session() as session:
        if not await is_admin(session, call.from_user.id):
            await call.answer("Faqat admin rad eta oladi.", show_alert=True)
            return

        ad = await _get_ad(session, ad_id)
        if not ad:
            await call.answer("E’lon topilmadi.", show_alert=True)
            return

        await session.execute(update(Ad).where(Ad.id == ad_id).values(status="rejected"))
        await session.commit()

    await call.answer("❌ Rad etildi.", show_alert=True)
