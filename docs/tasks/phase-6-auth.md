# Phase 6: 用户认证与权限

**优先级**: 🟡 中
**状态**: ✅ 已完成
**预计工作量**: 中等
**依赖**: Phase 1C 完成

---

## 任务清单

### ✅ Task 1: JWT 认证系统
**状态**: 已完成
**文件**:
- 创建: `backend/app/core/security.py`
- 修改: `backend/requirements.txt`

**步骤**:

1. **添加依赖**
   ```python
   # backend/requirements.txt
   python-jose[cryptography]==3.3.0
   passlib[bcrypt]==1.7.4
   python-multipart==0.0.9
   ```

2. **实现 JWT 工具函数**
   ```python
   # backend/app/core/security.py

   from datetime import datetime, timedelta
   from jose import JWTError, jwt
   from passlib.context import CryptContext
   from app.core.config import settings

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
   ```

3. **添加配置**
   ```python
   # backend/app/core/config.py

   class Settings(BaseSettings):
       # JWT 配置
       SECRET_KEY: str = "your-secret-key-here"  # 生产环境使用环境变量
       ALGORITHM: str = "HS256"
       ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
   ```

4. **提交代码**
   ```bash
   git add backend/app/core/security.py backend/requirements.txt
   git commit -m "feat: add JWT authentication system"
   ```

---

### ✅ Task 2: 用户注册/登录 API
**状态**: 已完成
**文件**:
- 创建: `backend/app/api/v1/auth.py`
- 创建: `backend/app/schemas/user.py`
- 修改: `backend/main.py`

**步骤**:

1. **创建用户 Schema**
   ```python
   # backend/app/schemas/user.py

   from pydantic import BaseModel, EmailStr, Field

   class UserRegister(BaseModel):
       username: str = Field(..., min_length=3, max_length=50)
       email: EmailStr
       password: str = Field(..., min_length=8)

   class UserLogin(BaseModel):
       email: EmailStr
       password: str

   class UserResponse(BaseModel):
       id: int
       username: str
       email: str
       created_at: datetime

   class Token(BaseModel):
       access_token: str
       token_type: str = "bearer"
   ```

2. **实现认证 API**
   ```python
   # backend/app/api/v1/auth.py

   from fastapi import APIRouter, HTTPException, Depends
   from sqlalchemy.orm import Session
   from app.core.database import get_db
   from app.core.security import (
       verify_password, get_password_hash, create_access_token
   )
   from app.models.user import User
   from app.schemas.user import UserRegister, UserLogin, Token, UserResponse

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
       access_token = create_access_token(
           data={"sub": str(db_user.id), "email": db_user.email}
       )

       # 更新最后登录时间
       db_user.last_login_at = datetime.utcnow()
       db.commit()

       return {"access_token": access_token, "token_type": "bearer"}
   ```

3. **注册路由**
   ```python
   # backend/main.py
   from app.api.v1 import auth

   app.include_router(
       auth.router,
       prefix=f"{settings.API_V1_STR}/auth",
       tags=["auth"]
   )
   ```

4. **测试 API**
   ```bash
   # 注册
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username": "test", "email": "test@example.com", "password": "password123"}'

   # 登录
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "password123"}'
   ```

5. **提交代码**
   ```bash
   git add backend/app/api/v1/auth.py backend/app/schemas/user.py
   git commit -m "feat: add user registration and login API"
   ```

---

### ✅ Task 3: 认证中间件
**状态**: 已完成
**文件**:
- 创建: `backend/app/core/dependencies.py`

**步骤**:

1. **实现认证依赖**
   ```python
   # backend/app/core/dependencies.py

   from fastapi import Depends, HTTPException, status
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   from sqlalchemy.orm import Session
   from app.core.database import get_db
   from app.core.security import decode_access_token
   from app.models.user import User

   security = HTTPBearer()

   async def get_current_user(
       credentials: HTTPAuthorizationCredentials = Depends(security),
       db: Session = Depends(get_db)
   ) -> User:
       """获取当前登录用户"""
       token = credentials.credentials
       payload = decode_access_token(token)

       if payload is None:
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Invalid authentication credentials"
           )

       user_id = payload.get("sub")
       if user_id is None:
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Invalid token payload"
           )

       user = db.query(User).filter(User.id == int(user_id)).first()
       if user is None:
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="User not found"
           )

       return user

   async def get_current_active_user(
       current_user: User = Depends(get_current_user)
   ) -> User:
       """获取当前活跃用户"""
       if not current_user.is_active:
           raise HTTPException(status_code=400, detail="Inactive user")
       return current_user
   ```

2. **应用到受保护的端点**
   ```python
   # backend/app/api/v1/strategy.py

   from app.core.dependencies import get_current_active_user
   from app.models.user import User

   @router.post("/execute")
   async def execute_strategy(
       request: StrategyExecuteRequest,
       current_user: User = Depends(get_current_active_user)
   ):
       """执行选股策略（需要认证）"""
       # 现在可以访问 current_user
       pass
   ```

3. **提交代码**
   ```bash
   git add backend/app/core/dependencies.py
   git commit -m "feat: add authentication middleware"
   ```

---

### ✅ Task 4: 会话管理（Redis）
**状态**: 已完成
**文件**:
- 修改: `backend/app/core/security.py`

**步骤**:

1. **实现 Redis 会话存储**
   ```python
   # backend/app/core/security.py

   from app.core.cache import get_redis

   async def store_session(user_id: int, token: str, expires_in: int = 1800):
       """存储会话到 Redis"""
       redis = get_redis()
       session_key = f"user:session:{user_id}"

       session_data = {
           "user_id": user_id,
           "token": token,
           "created_at": datetime.utcnow().isoformat()
       }

       await redis.setex(session_key, expires_in, json.dumps(session_data))

   async def get_session(user_id: int) -> dict:
       """从 Redis 获取会话"""
       redis = get_redis()
       session_key = f"user:session:{user_id}"

       session_data = await redis.get(session_key)
       if session_data:
           return json.loads(session_data)
       return None

   async def delete_session(user_id: int):
       """删除会话"""
       redis = get_redis()
       session_key = f"user:session:{user_id}"
       await redis.delete(session_key)
   ```

2. **更新登录逻辑**
   ```python
   # backend/app/api/v1/auth.py

   @router.post("/login", response_model=Token)
   async def login(user: UserLogin, db: Session = Depends(get_db)):
       # ... 验证用户 ...

       # 生成 Token
       access_token = create_access_token(
           data={"sub": str(db_user.id), "email": db_user.email}
       )

       # 存储会话
       await store_session(db_user.id, access_token)

       return {"access_token": access_token, "token_type": "bearer"}

   @router.post("/logout")
   async def logout(current_user: User = Depends(get_current_active_user)):
       """用户登出"""
       await delete_session(current_user.id)
       return {"message": "Logged out successfully"}
   ```

3. **提交代码**
   ```bash
   git add backend/app/core/security.py backend/app/api/v1/auth.py
   git commit -m "feat: add Redis session management"
   ```

---

### ✅ Task 5: API 限流
**状态**: 已完成
**文件**:
- 创建: `backend/app/core/rate_limit.py`

**步骤**:

1. **实现限流中间件**
   ```python
   # backend/app/core/rate_limit.py

   from fastapi import Request, HTTPException
   from app.core.cache import get_redis
   import time

   class RateLimiter:
       def __init__(self, requests: int = 100, window: int = 60):
           """
           Args:
               requests: 时间窗口内允许的请求数
               window: 时间窗口（秒）
           """
           self.requests = requests
           self.window = window

       async def check_rate_limit(self, key: str) -> bool:
           """检查是否超过限流"""
           redis = get_redis()
           current = int(time.time())
           window_start = current - self.window

           # 使用 Redis Sorted Set 存储请求时间戳
           pipe = redis.pipeline()
           pipe.zremrangebyscore(key, 0, window_start)  # 删除过期记录
           pipe.zadd(key, {str(current): current})  # 添加当前请求
           pipe.zcount(key, window_start, current)  # 统计窗口内请求数
           pipe.expire(key, self.window)  # 设置过期时间

           results = await pipe.execute()
           request_count = results[2]

           return request_count <= self.requests

   # 创建限流器实例
   rate_limiter = RateLimiter(requests=100, window=60)

   async def rate_limit_dependency(request: Request):
       """限流依赖"""
       # 使用 IP 地址作为限流 Key
       client_ip = request.client.host
       key = f"rate_limit:{client_ip}"

       if not await rate_limiter.check_rate_limit(key):
           raise HTTPException(
               status_code=429,
               detail="Too many requests. Please try again later."
           )
   ```

2. **应用限流到 API**
   ```python
   # backend/app/api/v1/strategy.py

   from app.core.rate_limit import rate_limit_dependency

   @router.post("/execute", dependencies=[Depends(rate_limit_dependency)])
   async def execute_strategy(request: StrategyExecuteRequest):
       """执行选股策略（带限流）"""
       pass
   ```

3. **全局限流中间件**
   ```python
   # backend/main.py

   from fastapi import Request
   from app.core.rate_limit import rate_limiter

   @app.middleware("http")
   async def rate_limit_middleware(request: Request, call_next):
       client_ip = request.client.host
       key = f"rate_limit:global:{client_ip}"

       if not await rate_limiter.check_rate_limit(key):
           return JSONResponse(
               status_code=429,
               content={"detail": "Too many requests"}
           )

       response = await call_next(request)
       return response
   ```

4. **提交代码**
   ```bash
   git add backend/app/core/rate_limit.py
   git commit -m "feat: add API rate limiting"
   ```

---

## 完成标准

Phase 6 完成后，认证系统应具备以下能力：

### 功能完整性
- ✅ JWT 认证系统
- ✅ 用户注册/登录 API
- ✅ 认证中间件
- ✅ Redis 会话管理
- ✅ API 限流

### 安全标准
- ✅ 密码使用 bcrypt 加密
- ✅ JWT Token 有效期控制
- ✅ 会话管理完善
- ✅ API 限流防止滥用

### 质量标准
- ✅ 认证流程测试通过
- ✅ 错误处理完善
- ✅ 日志记录完整

---

## 下一步

完成 Phase 6 后，进入 **Phase 7: 缓存优化与性能调优**

参考文档: `docs/tasks/phase-7-optimization.md`
