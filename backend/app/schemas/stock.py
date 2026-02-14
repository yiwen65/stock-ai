# backend/app/schemas/stock.py
from pydantic import BaseModel
from typing import Optional

class StockResponse(BaseModel):
    stock_code: str
    stock_name: str

class QuoteResponse(BaseModel):
    stock_code: str
    stock_name: Optional[str] = None
    price: float
    change: float
    pct_change: float
    volume: int
    amount: float
    amplitude: Optional[float] = None
    high: float
    low: float
    open: float
    pre_close: float
    volume_ratio: Optional[float] = None
    turnover_rate: Optional[float] = None
    pe: Optional[float] = None
    pb: Optional[float] = None
    market_cap: Optional[float] = None
    circulating_market_cap: Optional[float] = None
    change_speed: Optional[float] = None
    change_5min: Optional[float] = None
    change_60d: Optional[float] = None
    change_ytd: Optional[float] = None
    timestamp: Optional[str] = None

class KLineItem(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
