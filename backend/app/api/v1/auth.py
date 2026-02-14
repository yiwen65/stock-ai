# backend/app/api/v1/auth.py

from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_access_token,
    store_session, delete_session
)
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, Token, UserResponse, RefreshRequest

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户是否已存在
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 生成 Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.id), "email": db_user.email},
        expires_delta=access_token_expires
    )

    # 更新最后登录时间
    from datetime import datetime
    db_user.last_login_at = datetime.utcnow()
    db.commit()

    # Create refresh token
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": str(db_user.id), "email": db_user.email},
        expires_delta=refresh_token_expires
    )

    # 存储会话
    await store_session(db_user.id, access_token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    """使用 Refresh Token 获取新的 Access Token"""
    payload = decode_access_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Issue new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )

    # Issue new refresh token (rotation)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=refresh_token_expires
    )

    await store_session(user.id, new_access_token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """用户登出"""
    await delete_session(current_user.id)
    return {"message": "Logged out successfully"}
