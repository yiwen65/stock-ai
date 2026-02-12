# backend/app/schemas/stock.py
from pydantic import BaseModel
from typing import Optional

class StockResponse(BaseModel):
    stock_code: str
    stock_name: str

class QuoteResponse(BaseModel):
    stock_code: str
    price: float
    change: float
    pct_change: float
    volume: int
    amount: float
    high: float
    low: float
    open: float
    pre_close: float
