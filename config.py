# import os
# from dotenv import load_dotenv

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# load_dotenv(os.path.join(BASE_DIR, ".env"))

# BOT_TOKEN = os.getenv("BOT_TOKEN")
# CHANNEL_ID = os.getenv("CHANNEL_ID")

# ADMIN_CODES = [
#     os.getenv("ADMIN_CODE_1"),
#     os.getenv("ADMIN_CODE_2")
# ]

# DB_USER = os.getenv("DB_USER", "postgres")
# DB_PASS = os.getenv("DB_PASS", "postgres")
# DB_NAME = os.getenv("DB_NAME", "dacha_bot")
# DB_HOST = os.getenv("DB_HOST", "localhost")
# DB_PORT = os.getenv("DB_PORT", "5432")

# # Construct AsyncPG URL for SQLAlchemy (SQLite)
# DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'dacha_bot.db')}"

########################################################################################

# config.py
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ .env ni aynan shu papkadan o‘qiymiz
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()  # "@test_uchun_2" yoki "-100123..."

# ✅ Admin codes: None bo‘lsa ham ro‘yxatga kirmasin
ADMIN_CODES = [
    code.strip()
    for code in [os.getenv("ADMIN_CODE_1"), os.getenv("ADMIN_CODE_2")]
    if code and code.strip()
]

DB_USER = os.getenv("DB_USER", "postgres").strip()
DB_PASS = os.getenv("DB_PASS", "postgres").strip()
DB_NAME = os.getenv("DB_NAME", "dacha_bot").strip()
DB_HOST = os.getenv("DB_HOST", "localhost").strip()
DB_PORT = os.getenv("DB_PORT", "5432").strip()

# ✅ SQLite DB path (senda shunday ekan)
# DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'dacha_bot.db')}"
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'villa_bot.db')}"

# ✅ Minimal tekshiruvlar (xatoni darrov ko‘rasan)
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi. .env ni tekshir: BOT_TOKEN=...")

# Kanalga darhol post qilishni yoqayotgan bo‘lsang, buni ham tekshirgan yaxshi:
# (Hozircha xohlasang commentda qoldir)
# if not CHANNEL_ID:
#     raise ValueError("CHANNEL_ID topilmadi. .env ni tekshir: CHANNEL_ID=@channel yoki -100...")
