# backend/app/models/strategy.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class UserStrategy(Base):
    __tablename__ = "user_strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    strategy_type = Column(String(20), nullable=False)
    conditions = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StrategyExecution(Base):
    __tablename__ = "strategy_executions"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("user_strategies.id", ondelete='CASCADE'), nullable=False, index=True)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    result_count = Column(Integer, nullable=False, default=0)
    result_snapshot = Column(JSON, nullable=True)
