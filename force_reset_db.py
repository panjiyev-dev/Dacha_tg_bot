import os
import asyncio
import logging
from database.setup import engine, Base

logging.basicConfig(level=logging.INFO)

async def force_reset():
    db_path = "dacha_bot.db"
    
    print(f"Force resetting database: {db_path}")
    
    # 1. Close connections (if any) and delete file
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("Successfully deleted old database file.")
        except Exception as e:
            print(f"Warning: Could not delete file: {e}. It might be in use.")

    # 2. Re-initialize
    from database.setup import init_db
    try:
        from database.models import User, Ad, Admin, ActivationCode, ChannelPost, GlobalSettings
        from config import CHANNEL_ID
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Initialize default settings
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.orm import sessionmaker
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        
        async with async_session() as session:
            settings = GlobalSettings(
                id=1, 
                target_channels=[CHANNEL_ID] if CHANNEL_ID else []
            )
            session.add(settings)
            await session.commit()
            
        print("Database schema recreated and settings initialized successfully!")
    except Exception as e:
        print(f"Error during schema creation: {e}")

if __name__ == "__main__":
    asyncio.run(force_reset())
