# backend/app/api/v1/watchlist.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.watchlist import WatchlistItem

router = APIRouter()


class WatchlistAddRequest(BaseModel):
    stock_code: str = Field(..., min_length=1, max_length=10)
    stock_name: str = Field("", max_length=50)
    note: str = Field(None, max_length=200)


class WatchlistResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: str
    note: str | None
    created_at: str | None


@router.get("", response_model=List[WatchlistResponse])
async def list_watchlist(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """获取用户自选股列表"""
    items = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user.id)
        .order_by(WatchlistItem.created_at.desc())
        .all()
    )
    return [
        WatchlistResponse(
            id=i.id,
            stock_code=i.stock_code,
            stock_name=i.stock_name,
            note=i.note,
            created_at=str(i.created_at) if i.created_at else None,
        )
        for i in items
    ]


@router.post("", response_model=WatchlistResponse, status_code=201)
async def add_to_watchlist(
    body: WatchlistAddRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """添加自选股"""
    exists = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user.id, WatchlistItem.stock_code == body.stock_code)
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="该股票已在自选股中")

    item = WatchlistItem(
        user_id=user.id,
        stock_code=body.stock_code,
        stock_name=body.stock_name,
        note=body.note,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return WatchlistResponse(
        id=item.id,
        stock_code=item.stock_code,
        stock_name=item.stock_name,
        note=item.note,
        created_at=str(item.created_at) if item.created_at else None,
    )


@router.delete("/{stock_code}")
async def remove_from_watchlist(
    stock_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """删除自选股"""
    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user.id, WatchlistItem.stock_code == stock_code)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="未找到该自选股")
    db.delete(item)
    db.commit()
    return {"detail": "已删除"}


@router.get("/check/{stock_code}")
async def check_in_watchlist(
    stock_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """检查股票是否在自选股中"""
    exists = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user.id, WatchlistItem.stock_code == stock_code)
        .first()
    )
    return {"in_watchlist": exists is not None}
