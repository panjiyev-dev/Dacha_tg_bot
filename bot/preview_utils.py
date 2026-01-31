# villa_bot/bot/preview_utils.py
from __future__ import annotations

from typing import List, Optional
import json

from aiogram import Bot
from aiogram.types import (
    InputMediaPhoto,
    InlineKeyboardMarkup,
)

def make_caption(ad) -> str:
    """
    Postda faqat: title, description, phone bo'ladi deding.
    """
    title = (getattr(ad, "title", "") or "").strip()
    desc = (getattr(ad, "description", "") or "").strip()
    phone = (getattr(ad, "phone", "") or "").strip()

    parts = []
    if title:
        parts.append(f"🏠 <b>{title}</b>")
    if desc:
        parts.append(desc)
    if phone:
        parts.append(f"📞 <b>{phone}</b>")

    return "\n\n".join(parts).strip() or "—"

def _parse_photos(photos_field) -> List[str]:
    """
    ad.photos ba'zan list, ba'zan JSON string bo'lishi mumkin (logda JSON string ko'rinyapti).
    """
    if not photos_field:
        return []
    if isinstance(photos_field, list):
        return [p for p in photos_field if p]
    if isinstance(photos_field, str):
        s = photos_field.strip()
        if not s:
            return []
        try:
            data = json.loads(s)
            if isinstance(data, list):
                return [p for p in data if p]
        except Exception:
            # agar oddiy string bo'lsa (bitta photo id)
            return [s]
    return []

# async def send_ad_preview(
#     bot: Bot,
#     chat_id: int,
#     ad,
#     keyboard: Optional[InlineKeyboardMarkup] = None,
#     header_text: Optional[str] = None,
# ) -> None:
#     """
#     1) Agar photos bo'lsa -> album yuboradi (media group)
#     2) Keyin caption + tugmalarni alohida message qilib yuboradi (keyboard shu yerda chiqadi)
#     """
#     photos = _parse_photos(getattr(ad, "photos", None))
#     caption = make_caption(ad)

#     if photos:
#         media = []
#         for file_id in photos[:10]:  # Telegram album limit ~10
#             media.append(InputMediaPhoto(media=file_id))
#         await bot.send_media_group(chat_id=chat_id, media=media)

#     text_parts = []
#     if header_text:
#         text_parts.append(header_text)
#     text_parts.append(caption)
#     text = "\n\n".join(text_parts)

#     await bot.send_message(
#         chat_id=chat_id,
#         text=text,
#         reply_markup=keyboard,
#         parse_mode="HTML",
#     )

async def send_ad_preview(bot: Bot, chat_id: int, ad, keyboard):
    caption = (
        f"🏡 <b>{ad.title}</b>\n\n"
        f"{ad.description}\n\n"
        f"📞 {ad.phone}\n"
        f"🆔 ID: #ad{ad.id}"
    )

    if ad.photos and len(ad.photos) > 1:
        media = [
            InputMediaPhoto(media=p, caption=caption if i == 0 else None)
            for i, p in enumerate(ad.photos)
        ]
        await bot.send_media_group(chat_id, media)
        await bot.send_message(chat_id, "⬇️ Amal tanlang:", reply_markup=keyboard)

    elif ad.photos:
        await bot.send_photo(chat_id, ad.photos[0], caption=caption, reply_markup=keyboard)

    else:
        await bot.send_message(chat_id, caption, reply_markup=keyboard)