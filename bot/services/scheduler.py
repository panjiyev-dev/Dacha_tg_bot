# services/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from config import DATABASE_URL

# Using standard SQLite for job store if needed, or just memory for now
# As per TZ, we need reliability, but memory is fine for development
scheduler = AsyncIOScheduler()

async def setup_scheduler(bot):
    # Initialize implementation-specific jobs
    from bot.logic.automation import start_jobs
    start_jobs(bot)
    
    if not scheduler.running:
        scheduler.start()
        print("Scheduler started.")

async def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler shut down.")
