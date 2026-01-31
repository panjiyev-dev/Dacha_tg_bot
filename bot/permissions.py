# villa_bot/bot/permissions.py
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession

# from villa_bot.db.models import Admin  # <-- senda model nomi admins bo'lishi mumkin: Admin / Admins

# async def is_admin(session: AsyncSession, user_id: int) -> bool:
#     q = await session.execute(select(Admin.user_id).where(Admin.user_id == user_id))
#     return q.scalar_one_or_none() is not None

# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from database.models import Admin

# async def is_admin(session: AsyncSession, user_id: int) -> bool:
#     res = await session.execute(select(Admin.user_id).where(Admin.user_id == user_id))
#     return res.scalar_one_or_none() is not None

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Admin

async def is_admin(session: AsyncSession, user_id: int) -> bool:
    q = await session.execute(select(Admin.user_id).where(Admin.user_id == user_id))
    return q.scalar_one_or_none() is not None
