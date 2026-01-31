from aiogram import Bot, types
from aiogram.utils.media_group import MediaGroupBuilder
from database.setup import async_session
from database.models import Ad, ChannelPost
from sqlalchemy import select, delete, update
from datetime import datetime, timedelta
import config

async def post_ad_to_channel(bot: Bot, ad: Ad):
    """Posts an ad to the configured channels and records message IDs for deletion."""
    import html
    from bot.utils.i18n import i18n
    
    # Use the ad's stored language if available, fallback to ru
    lang = getattr(ad, 'language', 'ru') or 'ru'
    
    price_label = i18n.get("price_label", lang)
    contact_label = i18n.get("contact_label", lang)
    
    text = (
        f"🌟 <b>{html.escape(ad.title or '')}</b>\n"
        f"───────────────────\n\n"
        f"📝 {html.escape(ad.description or '')}\n\n"
        f"{price_label} {html.escape(ad.price or '')}\n"
        f"{contact_label} {html.escape(ad.phone or '')}\n\n"
        f"───────────────────\n"
        f"🏢 #DachaLive"
    )
    
    async with async_session() as session:
        # Get settings
        from database.models import GlobalSettings
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        
        target_channels = settings.target_channels if settings and settings.target_channels else [config.CHANNEL_ID]
        duration = settings.post_duration_hours if settings else 24
        
        for chat_id in target_channels:
            try:
                # aiogram 3.x media group
                if ad.photos:
                    media = MediaGroupBuilder(caption=text)
                    for file_id in ad.photos:
                        media.add_photo(media=file_id, parse_mode="HTML")
                    
                    messages = await bot.send_media_group(chat_id=chat_id, media=media.build())
                    for msg in messages:
                        post = ChannelPost(
                            ad_id=ad.id,
                            message_id=msg.message_id,
                            chat_id=chat_id,
                            delete_at=datetime.utcnow() + timedelta(hours=duration)
                        )
                        session.add(post)
                else:
                    msg = await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
                    post = ChannelPost(
                        ad_id=ad.id,
                        message_id=msg.message_id,
                        chat_id=chat_id,
                        delete_at=datetime.utcnow() + timedelta(hours=duration)
                    )
                    session.add(post)
                
                # Update last_posted_at
                await session.execute(update(Ad).where(Ad.id == ad.id).values(last_posted_at=datetime.utcnow()))
                
            except Exception as e:
                print(f"Failed to post to channel {chat_id}: {e}")
        
        await session.commit()

async def cleanup_expired_posts(bot: Bot):
    """Deletes posts from the channel that have exceeded the 24h limit."""
    async with async_session() as session:
        now = datetime.utcnow()
        res = await session.execute(select(ChannelPost).where(ChannelPost.delete_at <= now))
        posts = res.scalars().all()
        
        for post in posts:
            try:
                await bot.delete_message(chat_id=post.chat_id, message_id=post.message_id)
            except Exception as e:
                print(f"Failed to delete message {post.message_id}: {e}")
            
            await session.delete(post)
        
        await session.commit()
