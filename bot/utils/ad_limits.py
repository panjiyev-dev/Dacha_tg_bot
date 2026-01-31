# bot/utils/ad_limits.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Ad

MAX_ADS_PER_USER = 2
SLOT_STATUSES = ("pending", "active")  # limit yeydigan statuslar

async def get_used_slots(session: AsyncSession, user_id: int) -> int:
    """
    User uchun hozir nechta 'slot' band ekanini qaytaradi.
    Slot band = status pending yoki active bo'lgan e'lonlar.
    """
    res = await session.execute(
        select(func.count(Ad.id)).where(
            Ad.user_id == user_id,
            Ad.status.in_(SLOT_STATUSES)
        )
    )
    return int(res.scalar() or 0)

async def has_free_slot(session: AsyncSession, user_id: int) -> bool:
    used = await get_used_slots(session, user_id)
    return used < MAX_ADS_PER_USER
