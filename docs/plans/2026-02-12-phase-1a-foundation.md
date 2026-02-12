# Phase 1A: Foundation Setup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish project foundation with Docker environment, databases, and basic FastAPI skeleton

**Architecture:** Layered architecture with FastAPI backend, PostgreSQL for relational data, InfluxDB for time-series, Redis for caching

**Tech Stack:** Python 3.11, FastAPI, PostgreSQL 15, InfluxDB 2.7, Redis 7.2, Docker Compose

**Duration:** Week 1-2 of MVP (12-week timeline)

---

## Task 1: Project Structure & Environment

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`

**Step 1: Create project directories**

```bash
mkdir -p backend/app/{api/v1,core,models,schemas,services,utils,tasks}
mkdir -p backend/tests/{unit,integration}
mkdir -p frontend/src
mkdir -p docs/plans
```

**Step 2: Create requirements.txt**

```python
# backend/requirements.txt
fastapi==0.110.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
redis==5.0.1
influxdb-client==1.40.0
pydantic==2.6.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
celery==5.3.6
pandas==2.2.0
numpy==1.26.3
akshare==1.13.0
pytest==8.0.0
pytest-asyncio==0.23.4
httpx==0.26.0
```

**Step 3: Create docker-compose.yml**

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: stock_ai
      POSTGRES_USER: stock_user
      POSTGRES_PASSWORD: stock_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  influxdb:
    image: influxdb:2.7
    environment:
      DOCKER_INFLUXDB_INIT_MODE: setup
      DOCKER_INFLUXDB_INIT_USERNAME: admin
      DOCKER_INFLUXDB_INIT_PASSWORD: adminpass
      DOCKER_INFLUXDB_INIT_ORG: stock-ai
      DOCKER_INFLUXDB_INIT_BUCKET: stock_data
      DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: my-super-secret-token
    ports:
      - "8086:8086"
    volumes:
      - influxdb_data:/var/lib/influxdb2

volumes:
  postgres_data:
  redis_data:
  influxdb_data:
```

**Step 4: Create .env.example**

```bash
# .env.example
DATABASE_URL=postgresql://stock_user:stock_pass@localhost:5432/stock_ai
REDIS_URL=redis://localhost:6379/0
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=my-super-secret-token
INFLUXDB_ORG=stock-ai
INFLUXDB_BUCKET=stock_data
SECRET_KEY=your-secret-key-here
```

**Step 5: Create .gitignore**

```
# .gitignore
__pycache__/
*.py[cod]
*$py.class
.env
.venv/
venv/
*.log
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.DS_Store
```

**Step 6: Start Docker services**

```bash
docker-compose up -d
```

Expected: All 3 services (postgres, redis, influxdb) running

**Step 7: Commit**

```bash
git init
git add .
git commit -m "chore: initialize project structure and Docker environment"
```

---

## Task 2: FastAPI Core Configuration

**Files:**
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`
- Create: `backend/app/core/cache.py`
- Create: `backend/main.py`

**Step 1: Write config.py**

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Stock AI"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str
    REDIS_URL: str
    INFLUXDB_URL: str
    INFLUXDB_TOKEN: str
    INFLUXDB_ORG: str
    INFLUXDB_BUCKET: str

    SECRET_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Step 2: Write database.py**

```python
# backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 3: Write cache.py**

```python
# backend/app/core/cache.py
import redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_cache():
    return redis_client
```

**Step 4: Write main.py**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Stock AI API", "version": settings.VERSION}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

**Step 5: Test FastAPI server**

```bash
cd backend
python -m uvicorn main:app --reload
```

Expected: Server starts on http://127.0.0.1:8000, visit /docs to see Swagger UI

**Step 6: Commit**

```bash
git add backend/
git commit -m "feat: add FastAPI core configuration and health endpoints"
```

---

## Task 3: Database Models Foundation

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/stock.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`

**Step 1: Write user model**

```python
# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Step 2: Write stock model**

```python
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
```

**Step 3: Install Alembic**

```bash
pip install alembic==1.13.1
alembic init alembic
```

**Step 4: Configure Alembic env.py**

```python
# backend/alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.core.config import settings
from app.core.database import Base
from app.models import user, stock  # Import all models

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

**Step 5: Create initial migration**

```bash
alembic revision --autogenerate -m "Initial tables"
alembic upgrade head
```

Expected: Tables created in PostgreSQL

**Step 6: Commit**

```bash
git add backend/
git commit -m "feat: add database models and Alembic migrations"
```

---

## Task 4: AKShare Data Service Integration

**Files:**
- Create: `backend/app/services/data_service.py`
- Create: `backend/tests/unit/test_data_service.py`

**Step 1: Write failing test**

```python
# backend/tests/unit/test_data_service.py
import pytest
from app.services.data_service import DataService

@pytest.mark.asyncio
async def test_fetch_stock_list():
    service = DataService()
    stocks = await service.fetch_stock_list()
    assert isinstance(stocks, list)
    assert len(stocks) > 0
    assert "stock_code" in stocks[0]
    assert "stock_name" in stocks[0]
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/unit/test_data_service.py::test_fetch_stock_list -v
```

Expected: FAIL with "No module named 'app.services.data_service'"

**Step 3: Write minimal implementation**

```python
# backend/app/services/data_service.py
import akshare as ak
import pandas as pd
from typing import List, Dict

class DataService:
    async def fetch_stock_list(self) -> List[Dict]:
        """Fetch A-share stock list from AKShare"""
        try:
            # Get stock list
            df = ak.stock_info_a_code_name()

            # Convert to list of dicts
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    "stock_code": row["code"],
                    "stock_name": row["name"]
                })

            return stocks
        except Exception as e:
            print(f"Error fetching stock list: {e}")
            return []
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_data_service.py::test_fetch_stock_list -v
```

Expected: PASS

**Step 5: Add real-time quote test**

```python
# backend/tests/unit/test_data_service.py
@pytest.mark.asyncio
async def test_fetch_realtime_quote():
    service = DataService()
    quote = await service.fetch_realtime_quote("600519")
    assert quote is not None
    assert "price" in quote
    assert "pct_change" in quote
```

**Step 6: Implement realtime quote**

```python
# backend/app/services/data_service.py (add method)
    async def fetch_realtime_quote(self, stock_code: str) -> Dict:
        """Fetch real-time quote for a stock"""
        try:
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df["代码"] == stock_code]

            if stock_data.empty:
                return None

            row = stock_data.iloc[0]
            return {
                "stock_code": stock_code,
                "price": float(row["最新价"]),
                "change": float(row["涨跌额"]),
                "pct_change": float(row["涨跌幅"]),
                "volume": int(row["成交量"]),
                "amount": float(row["成交额"]),
                "high": float(row["最高"]),
                "low": float(row["最低"]),
                "open": float(row["今开"]),
                "pre_close": float(row["昨收"])
            }
        except Exception as e:
            print(f"Error fetching realtime quote: {e}")
            return None
```

**Step 7: Run all tests**

```bash
pytest tests/unit/test_data_service.py -v
```

Expected: All tests PASS

**Step 8: Commit**

```bash
git add backend/
git commit -m "feat: add AKShare data service with stock list and realtime quotes"
```

---

## Task 5: Basic API Endpoints

**Files:**
- Create: `backend/app/api/v1/stock.py`
- Create: `backend/app/schemas/stock.py`
- Modify: `backend/main.py`

**Step 1: Write stock schemas**

```python
# backend/app/schemas/stock.py
from pydantic import BaseModel
from typing import Optional

class StockBase(BaseModel):
    stock_code: str
    stock_name: str

class StockList(StockBase):
    market: Optional[str] = None

class RealtimeQuote(BaseModel):
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
```

**Step 2: Write stock API endpoints**

```python
# backend/app/api/v1/stock.py
from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.stock import StockList, RealtimeQuote
from app.services.data_service import DataService

router = APIRouter()
data_service = DataService()

@router.get("/stocks", response_model=List[StockList])
async def get_stocks():
    """Get list of all A-share stocks"""
    stocks = await data_service.fetch_stock_list()
    return stocks

@router.get("/stocks/{stock_code}/realtime", response_model=RealtimeQuote)
async def get_realtime_quote(stock_code: str):
    """Get real-time quote for a stock"""
    quote = await data_service.fetch_realtime_quote(stock_code)
    if not quote:
        raise HTTPException(status_code=404, detail="Stock not found")
    return quote
```

**Step 3: Register router in main.py**

```python
# backend/main.py (add after app creation)
from app.api.v1 import stock

app.include_router(stock.router, prefix=settings.API_V1_STR, tags=["stocks"])
```

**Step 4: Test endpoints**

```bash
# Start server
uvicorn main:app --reload

# In another terminal, test endpoints
curl http://localhost:8000/api/v1/stocks | jq '.[0:3]'
curl http://localhost:8000/api/v1/stocks/600519/realtime | jq
```

Expected: JSON responses with stock data

**Step 5: Commit**

```bash
git add backend/
git commit -m "feat: add stock API endpoints for list and realtime quotes"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-02-12-phase-1a-foundation.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
