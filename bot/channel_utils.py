# # bot/channel_utils.py
# from telegram import InputMediaPhoto
# from telegram.ext import ContextTypes
# from config import CHANNEL_ID
# from database import Ad, get_user, update_ad_posted_time
# from datetime import datetime
# import logging

# logger = logging.getLogger(__name__)

# async def post_ad_to_channel(context: ContextTypes.DEFAULT_TYPE, ad: Ad):
#     """Post an ad to the configured channel."""
#     try:
#         user = get_user(ad.owner_id)
#         contact_info = f"@{user.username}" if user and user.username else "N/A"
        
#         caption = f"🏡 *{ad.title}*\n\n{ad.description}\n\n💰 Price: {ad.price}\n📍 Location: {ad.location}\n\n📞 Contact: {contact_info}"
        
#         media = []
#         if ad.video:
#              from telegram import InputMediaVideo
#              media.append(InputMediaVideo(media=ad.video, caption=caption, parse_mode='Markdown'))
             
#         if ad.photos:
#             for p in ad.photos:
#                  # If video exists, it took the caption.
#                  # If no video, first photo takes caption.
#                  has_caption = len(media) > 0
#                  media.append(InputMediaPhoto(media=p, caption=caption if not has_caption else None, parse_mode='Markdown'))
        
#         if media:
#              if len(media) == 1:
#                   # Single item (video or photo)
#                   if ad.video:
#                       await context.bot.send_video(chat_id=CHANNEL_ID, video=ad.video, caption=caption, parse_mode='Markdown')
#                   else:
#                       await context.bot.send_photo(chat_id=CHANNEL_ID, photo=ad.photos[0], caption=caption, parse_mode='Markdown')
#              else:
#                   await context.bot.send_media_group(chat_id=CHANNEL_ID, media=media)

#         else:
#             await context.bot.send_message(chat_id=CHANNEL_ID, text=caption, parse_mode='Markdown')
            
#         update_ad_posted_time(ad.id, datetime.now().isoformat())
#         logger.info(f"Immediately posted ad {ad.id}")
#         return True
#     except Exception as e:
#         logger.error(f"Failed to post ad {ad.id}: {e}")
#         return False

############################ NEW CODE BELOW ####################################### 

# bot/channel_utils.py
import json
import logging
from typing import List, Optional

from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo

from config import CHANNEL_ID
from database.models import Ad

logger = logging.getLogger(__name__)


def _normalize_photos(photos) -> List[str]:
    """
    ad.photos:
      - list bo'lishi mumkin
      - yoki JSON string bo'lishi mumkin: '["fileid1","fileid2"]'
    """
    if not photos:
        return []

    if isinstance(photos, list):
        return photos

    if isinstance(photos, str):
        try:
            data = json.loads(photos)
            if isinstance(data, list):
                return data
        except Exception:
            pass

    return []


# def _make_caption(ad) -> str:
#     title = (getattr(ad, "title", "") or "").strip()
#     description = (getattr(ad, "description", "") or "").strip()
#     phone = (getattr(ad, "phone", "") or "").strip()

#     parts = []
#     if title:
#         parts.append(f"🏠 {title}")
#     if description:
#         parts.append(f"\n{description}")
#     if phone:
#         parts.append(f"\n📞 {phone}")

#     return "\n".join(parts).strip()

def _make_caption(ad) -> str:
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

async def post_ad_to_channel(bot: Bot, ad: Ad) -> bool:
    """
    E'lonni kanalga darhol yuboradi (aiogram).
    DB ga posted_time yozmaydi (hozir test uchun).
    """
    if not CHANNEL_ID:
        logger.warning("CHANNEL_ID is empty. Check .env")
        return False

    try:
        photos = _normalize_photos(ad.photos)
        video: Optional[str] = getattr(ad, "video", None)
        caption = _make_caption(ad)

        media = []

        # Video bo'lsa caption video'ga tushadi
        if video:
            media.append(InputMediaVideo(media=video, caption=caption, parse_mode="HTML"))

        # Rasmlar: max 10 ta (Telegram limit)
        if photos:
            for idx, p in enumerate(photos[:10]):
                # Agar video bo'lmasa, caption birinchi photo'ga tushadi
                if not media and idx == 0:
                    media.append(InputMediaPhoto(media=p, caption=caption, parse_mode="HTML"))
                else:
                    media.append(InputMediaPhoto(media=p))

        if media:
            if len(media) == 1:
                # Single media
                if video:
                    await bot.send_video(chat_id=CHANNEL_ID, video=video, caption=caption, parse_mode="HTML")
                else:
                    await bot.send_photo(chat_id=CHANNEL_ID, photo=photos[0], caption=caption, parse_mode="HTML")
            else:
                await bot.send_media_group(chat_id=CHANNEL_ID, media=media)
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=caption, parse_mode="HTML")

        logger.info("✅ Posted ad %s to channel", ad.id)
        return True

    except Exception as e:
        logger.exception("❌ Failed to post ad %s to channel: %s", getattr(ad, "id", "?"), e)
        return False
