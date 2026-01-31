import asyncio
from database.setup import init_db
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    try:
        print("Initializing database...")
        await init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        # Hint for user
        if "does not exist" in str(e):
             print("\n!!! HINT: You might need to create the database manually using 'createdb dacha_bot' or via pgAdmin.")

if __name__ == "__main__":
    asyncio.run(main())
