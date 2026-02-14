# backend/app/models/watchlist.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint('user_id', 'stock_code', name='uq_user_stock'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False, default="")
    note = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
