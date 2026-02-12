# backend/app/models/stock.py
from sqlalchemy import Column, Integer, String, Boolean, Date, BigInteger, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), unique=True, nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    market = Column(String(10), nullable=False)
    industry = Column(String(50), index=True)
    sector = Column(String(50))
    list_date = Column(Date)
    is_st = Column(Boolean, default=False, index=True)
    is_suspended = Column(Boolean, default=False)
    total_shares = Column(BigInteger)
    float_shares = Column(BigInteger)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
