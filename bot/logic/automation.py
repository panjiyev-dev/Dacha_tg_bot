# logic/automation.py
from aiogram import Bot, types
from database.setup import async_session
from database.models import Ad, User, ChannelPost
from bot.utils.channel import post_ad_to_channel, cleanup_expired_posts
from sqlalchemy import select, update
from datetime import datetime
from bot.services.scheduler import scheduler

async def daily_availability_check(bot: Bot):
    """Asks users if their villas are free today."""
    async with async_session() as session:
        # Find users with active, approved ads
        res = await session.execute(
            select(User).join(Ad).where(Ad.status == 'active', User.is_blocked == False)
        )
        users = res.scalars().unique().all()
        
        for user in users:
            from bot.utils.i18n import i18n
            lang = user.language or 'ru'
            
            text = i18n.get("check_text", lang)
            btn_yes = i18n.get("check_btn_yes", lang)
            btn_no = i18n.get("check_btn_no", lang)
            
            kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text=btn_yes, callback_data="villa_free_yes")],
                [types.InlineKeyboardButton(text=btn_no, callback_data="villa_free_no")]
            ])
            
            try:
                await bot.send_message(user.user_id, text, reply_markup=kb, parse_mode="HTML")
            except Exception as e:
                import logging
                logging.error(f"Failed to send daily check to {user.user_id}: {e}")

async def auto_post_scheduler_task(bot: Bot):
    """Logic to post confirmed active ads based on global frequency."""
    async with async_session() as session:
        from database.models import GlobalSettings
        from datetime import timedelta
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get frequency
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        freq = settings.post_frequency_hours if settings else 4
        
        # Only post ads marked as 'active' AND confirmed today
        # AND (last_posted_at is None OR last_posted_at + freq <= now)
        # AND user is NOT blocked
        res = await session.execute(
            select(Ad).join(User).where(
                Ad.status == 'active', 
                Ad.last_confirmed_free >= today_start,
                User.is_blocked == False
            )
        )
        ads = res.scalars().all()
        
        print(f"DEBUG: Processing {len(ads)} potential ads for posting (freq={freq}h)")
        for ad in ads:
            should_post = False
            if not ad.last_posted_at:
                should_post = True
            elif ad.last_posted_at + timedelta(hours=freq) <= now:
                should_post = True
                
            if should_post:
                print(f"DEBUG: Posting ad {ad.id} (Last posted: {ad.last_posted_at})")
                await post_ad_to_channel(bot, ad)

async def subscription_expiry_monitor(bot: Bot):
    """Notifies users when their subscription is about to end or has ended."""
    async with async_session() as session:
        now = datetime.utcnow()
        # Find users whose sub ended in the last hour to notify them once
        res = await session.execute(
            select(User).where(User.subscription_end_date <= now, User.subscription_end_date >= now - timedelta(hours=1))
        )
        users = res.scalars().all()
        for user in users:
            try:
                from bot.utils.i18n import i18n
                lang = user.language or 'ru'
                await bot.send_message(user.user_id, i18n.get("sub_expired", lang), parse_mode="HTML")
            except: pass

def start_jobs(bot: Bot):
    # Cleanup task every 10 minutes
    scheduler.add_job(cleanup_expired_posts, 'interval', minutes=10, args=[bot])
    
    # Expiry monitor every hour
    scheduler.add_job(subscription_expiry_monitor, 'interval', hours=1, args=[bot])
    
    # Daily check at 9 AM (configurable)
    scheduler.add_job(daily_availability_check, 'cron', hour=9, minute=0, args=[bot])
    
    # Auto-post check every 30 minutes
    scheduler.add_job(auto_post_scheduler_task, 'interval', minutes=30, args=[bot])
