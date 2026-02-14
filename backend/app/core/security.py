# backend/app/core/security.py

import json
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.core.cache import get_redis

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta = None) -> str:
    """创建 Refresh Token (longer-lived)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> dict:
    """解码 JWT Token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None

async def store_session(user_id: int, token: str, expires_in: int = 1800):
    """存储会话到 Redis"""
    redis = get_redis()
    session_key = f"user:session:{user_id}"

    session_data = {
        "user_id": user_id,
        "token": token,
        "created_at": datetime.utcnow().isoformat()
    }

    redis.setex(session_key, expires_in, json.dumps(session_data))

async def get_session(user_id: int) -> dict:
    """从 Redis 获取会话"""
    redis = get_redis()
    session_key = f"user:session:{user_id}"

    session_data = redis.get(session_key)
    if session_data:
        return json.loads(session_data)
    return None

async def delete_session(user_id: int):
    """删除会话"""
    redis = get_redis()
    session_key = f"user:session:{user_id}"
    redis.delete(session_key)
