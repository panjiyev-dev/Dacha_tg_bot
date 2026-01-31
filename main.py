# import asyncio
# import logging
# from aiogram import Bot, Dispatcher, types, F
# from config import BOT_TOKEN
# from database.setup import init_db
# from bot.services.scheduler import setup_scheduler, shutdown_scheduler
# from bot.middlewares.core import I18nMiddleware, AuthCheckMiddleware
# from dotenv import load_dotenv
# import os
# load_dotenv()


# # Configure logging
# logging.basicConfig(level=logging.DEBUG)
# print("CHANNEL_ID =", os.getenv("CHANNEL_ID"))

# async def main():
#     # Initialize Database (SQLite)
#     await init_db()
    
#     # Initialize Bot and Dispatcher
#     bot = Bot(token=BOT_TOKEN)
#     dp = Dispatcher()
    
#     # Register Routers
#     from bot.handlers import common, auth, ad_creation, admin, automation_callbacks
#     dp.include_router(common.router)
#     dp.include_router(auth.router)
#     dp.include_router(ad_creation.router)
#     dp.include_router(admin.router)
#     dp.include_router(automation_callbacks.router)
    
#     # Register Middlewares
#     i18n_middleware = I18nMiddleware()
#     auth_middleware = AuthCheckMiddleware()
    
#     # Apply Middlewares to all events
#     dp.message.middleware(i18n_middleware)
#     dp.callback_query.middleware(i18n_middleware)
    
#     dp.message.middleware(auth_middleware)
#     dp.callback_query.middleware(auth_middleware)
    
#     # Global Error Handler
#     @dp.error()
#     async def global_error_handler(event: types.ErrorEvent):
#         logging.error(f"Update: {event.update.update_id} caused error: {event.exception}")
        
#         error_text = (
#             "⚠️ <b>Произошла ошибка / Error occurred / Xatolik yuz berdi</b>\n"
#             "───────────────────\n\n"
#             "Мы уже работаем над исправлением. Пожалуйста, попробуйте позже.\n"
#             "We are working on a fix. Please try again later.\n"
#             "Xatolikni tuzatish ustida ishlayapmiz. Keyinroq urinib ko'ring."
#         )
        
#         try:
#             if event.update.message:
#                 await event.update.message.answer(error_text, parse_mode="HTML")
#             elif event.update.callback_query:
#                 await event.update.callback_query.message.answer(error_text, parse_mode="HTML")
#         except Exception as e:
#             logging.error(f"Failed to send error notification: {e}")
    
#     # Setup Scheduler
#     await setup_scheduler(bot)
    
#     # Ensure no Webhook is set and drop pending updates for a clean start
#     await bot.delete_webhook(drop_pending_updates=True)
    
#     print("Bot started (aiogram) with SQLite!")
#     try:
#         await dp.start_polling(bot)
#     finally:
#         await shutdown_scheduler()

# if __name__ == "__main__":
#     asyncio.run(main())

# print("CHANNEL_ID =", os.getenv("CHANNEL_ID"))

############################ NEW CODE BELOW #######################################

# main.py
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, CHANNEL_ID
from database.setup import init_db
from bot.services.scheduler import setup_scheduler, shutdown_scheduler
from bot.middlewares.core import I18nMiddleware, AuthCheckMiddleware
from bot.handlers import common, auth, ad_creation, admin, automation_callbacks, my_ads

# Configure logging
logging.basicConfig(level=logging.DEBUG)


async def check_channel_access(bot: Bot):
    """
    CHANNEL_ID berilgan bo‘lsa:
    - bot kanalni ko‘ra oladimi
    - admin/muvofiq huquqlar bormi
    (Kanal post yozishga real test qilish shart emas, lekin getChat yordam beradi)
    """
    if not CHANNEL_ID:
        logging.warning("CHANNEL_ID is not set. Channel posting will be disabled.")
        return

    try:
        chat = await bot.get_chat(CHANNEL_ID)
        logging.info(f"Channel found: title={chat.title} id={chat.id} username={chat.username}")

        # Botning kanaldagi statusini tekshirish
        me = await bot.get_me()
        member = await bot.get_chat_member(CHANNEL_ID, me.id)

        # status: 'administrator', 'member', 'left', ...
        logging.info(f"Bot status in channel: {member.status}")

        if member.status != "administrator":
            logging.warning(
                "Bot is NOT an admin in the channel. Posting may fail. "
                "Make sure bot is added as ADMIN with 'Post messages' permission."
            )

    except Exception as e:
        logging.error(f"Failed to access CHANNEL_ID={CHANNEL_ID}. Error: {e}")


async def main():
    # Initialize Database (SQLite)
    await init_db()

    # Initialize Bot and Dispatcher
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # Register Routers
    from bot.handlers import common, auth, ad_creation, admin, automation_callbacks
    dp.include_router(common.router)
    dp.include_router(auth.router)
    dp.include_router(ad_creation.router)
    dp.include_router(admin.router)
    dp.include_router(automation_callbacks.router)
    dp.include_router(my_ads.router)

    # Register Middlewares
    i18n_middleware = I18nMiddleware()
    auth_middleware = AuthCheckMiddleware()

    dp.message.middleware(i18n_middleware)
    dp.callback_query.middleware(i18n_middleware)

    dp.message.middleware(auth_middleware)
    dp.callback_query.middleware(auth_middleware)

    # Global Error Handler
    @dp.error()
    async def global_error_handler(event: types.ErrorEvent):
        logging.error(f"Update: {event.update.update_id} caused error: {event.exception}")

        error_text = (
            "⚠️ <b>Произошла ошибка / Error occurred / Xatolik yuz berdi</b>\n"
            "───────────────────\n\n"
            "Мы уже работаем над исправлением. Пожалуйста, попробуйте позже.\n"
            "We are working on a fix. Please try again later.\n"
            "Xatolikni tuzatish ustida ishlayapmiz. Keyinroq urinib ko'ring."
        )

        try:
            if event.update.message:
                await event.update.message.answer(error_text)
            elif event.update.callback_query and event.update.callback_query.message:
                await event.update.callback_query.message.answer(error_text)
        except Exception as e:
            logging.error(f"Failed to send error notification: {e}")

    # Setup Scheduler
    await setup_scheduler(bot)

    # Ensure no Webhook is set and drop pending updates for a clean start
    await bot.delete_webhook(drop_pending_updates=True)

    # ✅ Kanalga ulanishni tekshirib qo‘yamiz (logda ko‘rinadi)
    await check_channel_access(bot)

    print("Bot started (aiogram)!")
    try:
        await dp.start_polling(bot)
    finally:
        await shutdown_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
