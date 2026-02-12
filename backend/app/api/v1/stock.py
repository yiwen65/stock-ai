# backend/app/api/v1/stock.py
from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.stock import StockResponse, QuoteResponse
from app.services.data_service import DataService

router = APIRouter()
data_service = DataService()

@router.get("/stocks", response_model=List[StockResponse])
async def get_stocks():
    """Get list of all A-share stocks"""
    stocks = await data_service.fetch_stock_list()
    if not stocks:
        raise HTTPException(status_code=503, detail="Failed to fetch stock list")
    return stocks

@router.get("/stocks/{stock_code}/quote", response_model=QuoteResponse)
async def get_stock_quote(stock_code: str):
    """Get real-time quote for a specific stock"""
    quote = await data_service.fetch_realtime_quote(stock_code)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Stock {stock_code} not found")
    return quote
