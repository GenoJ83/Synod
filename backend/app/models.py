from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, UniqueConstraint
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    last_analysis_date = Column(String, default="")
    daily_analysis_count = Column(Integer, default=0)


class DocumentChatUsage(Base):
    __tablename__ = "document_chat_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    client_ip = Column(String(45), index=True)  # IPv4 or IPv6 address (no auth required)
    document_hash = Column(String(64), index=True)  # SHA256 hash of document content
    date = Column(Date, index=True)
    chat_count = Column(Integer, default=0)
    
    __table_args__ = (
        UniqueConstraint('client_ip', 'document_hash', 'date', name='uq_ip_document_date'),
    )
