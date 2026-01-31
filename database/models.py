from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from datetime import datetime

Base = declarative_base()

class User(AsyncAttrs, Base):
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    language = Column(String, default='ru')
    subscription_end_date = Column(DateTime, nullable=True)
    is_blocked = Column(Boolean, default=False)
    draft_id = Column(Integer, nullable=True)
    
    ads = relationship("Ad", back_populates="owner", foreign_keys="Ad.user_id")

class Admin(AsyncAttrs, Base):
    __tablename__ = 'admins'
    
    user_id = Column(BigInteger, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ActivationCode(AsyncAttrs, Base):
    __tablename__ = 'activation_codes'
    
    code = Column(String, primary_key=True)
    created_by = Column(BigInteger, nullable=True)
    is_used = Column(Boolean, default=False)
    used_by = Column(BigInteger, ForeignKey('users.user_id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)

class Ad(AsyncAttrs, Base):
    __tablename__ = 'ads'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'))
    
    title = Column(String, nullable=True)
    photos = Column(JSON, default=[]) 
    description = Column(String, nullable=True)
    price = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    language = Column(String, default='ru')
    
    status = Column(String, default='draft')
    last_confirmed_free = Column(DateTime, nullable=True)
    last_posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="ads", foreign_keys=[user_id])

class ChannelPost(AsyncAttrs, Base):
    __tablename__ = 'channel_posts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ad_id = Column(Integer, ForeignKey('ads.id'))
    message_id = Column(BigInteger) # Message ID in channel
    chat_id = Column(BigInteger)    # Channel ID
    delete_at = Column(DateTime)    # When to delete (now + 24h)
    created_at = Column(DateTime, default=datetime.utcnow)

class GlobalSettings(AsyncAttrs, Base):
    __tablename__ = 'global_settings'
    
    id = Column(Integer, primary_key=True, default=1)
    post_duration_hours = Column(Integer, default=24)
    post_frequency_hours = Column(Integer, default=4)
    target_channels = Column(JSON, default=[]) # List of channel IDs as strings or ints
