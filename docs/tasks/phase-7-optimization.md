# Phase 7: 缓存优化与性能调优

**优先级**: 🟢 低
**状态**: ⬜ 待开始
**预计工作量**: 中等
**依赖**: Phase 1C, Phase 2 完成

---

## 任务清单

### ⬜ Task 1: 多级缓存架构实现
**状态**: 待开始
**文件**:
- 创建: `backend/app/core/cache_manager.py`

**步骤**:

1. **实现多级缓存管理器**
   ```python
   # backend/app/core/cache_manager.py

   from typing import Optional, Any
   import json

   class CacheManager:
       """多级缓存管理器"""

       def __init__(self, redis_client, local_cache_size: int = 1000):
           self.redis = redis_client
           self.local_cache = {}  # 本地内存缓存
           self.local_cache_size = local_cache_size

       async def get(self, key: str) -> Optional[Any]:
           """获取缓存（先本地，后 Redis）"""
           # L1: 本地内存缓存
           if key in self.local_cache:
               return self.local_cache[key]

           # L2: Redis 缓存
           value = await self.redis.get(key)
           if value:
               data = json.loads(value)
               # 回填本地缓存
               self._set_local(key, data)
               return data

           return None

       async def set(
           self,
           key: str,
           value: Any,
           ttl: int = 3600,
           local_ttl: int = 60
       ):
           """设置缓存（同时写入本地和 Redis）"""
           # 写入 Redis
           await self.redis.setex(key, ttl, json.dumps(value))

           # 写入本地缓存
           self._set_local(key, value)

       def _set_local(self, key: str, value: Any):
           """设置本地缓存（LRU 淘汰）"""
           if len(self.local_cache) >= self.local_cache_size:
               # 删除最旧的项
               oldest_key = next(iter(self.local_cache))
               del self.local_cache[oldest_key]

           self.local_cache[key] = value

       async def delete(self, key: str):
           """删除缓存"""
           # 删除本地缓存
           if key in self.local_cache:
               del self.local_cache[key]

           # 删除 Redis 缓存
           await self.redis.delete(key)

       async def clear_local(self):
           """清空本地缓存"""
           self.local_cache.clear()
   ```

2. **应用到服务层**
   ```python
   # backend/app/services/stock_service.py

   from app.core.cache_manager import CacheManager

   class StockService:
       def __init__(self):
           self.cache = CacheManager(redis_client)

       async def get_stock_info(self, stock_code: str):
           cache_key = f"stock:info:{stock_code}"

           # 尝试从缓存获取
           cached = await self.cache.get(cache_key)
           if cached:
               return cached

           # 从数据库查询
           stock = await self._fetch_from_db(stock_code)

           # 写入缓存
           await self.cache.set(cache_key, stock, ttl=3600)

           return stock
   ```

3. **提交代码**
   ```bash
   git add backend/app/core/cache_manager.py
   git commit -m "feat: implement multi-level cache architecture"
   ```

---

### ⬜ Task 2: 缓存预热策略
**状态**: 待开始
**文件**:
- 创建: `backend/app/tasks/cache_warmup.py`

**步骤**:

1. **实现缓存预热任务**
   ```python
   # backend/app/tasks/cache_warmup.py

   from celery import shared_task
   from app.services.data_service import DataService
   from app.core.cache_manager import CacheManager

   @shared_task(name="warmup_hot_stocks")
   def warmup_hot_stocks():
       """预热热门股票数据"""
       asyncio.run(_warmup_hot_stocks())

   async def _warmup_hot_stocks():
       data_service = DataService()
       cache = CacheManager(redis_client)

       # 获取热门股票列表（成交量前 100）
       hot_stocks = await data_service.get_hot_stocks(limit=100)

       # 批量预热
       for stock in hot_stocks:
           # 预热实时行情
           realtime = await data_service.fetch_realtime_quote(stock['code'])
           await cache.set(
               f"stock:realtime:{stock['code']}",
               realtime,
               ttl=5
           )

           # 预热基础信息
           info = await data_service.fetch_stock_info(stock['code'])
           await cache.set(
               f"stock:info:{stock['code']}",
               info,
               ttl=3600
           )

       return len(hot_stocks)
   ```

2. **配置定时预热**
   ```python
   # backend/app/core/celery_app.py

   celery_app.conf.beat_schedule.update({
       'warmup-hot-stocks': {
           'task': 'warmup_hot_stocks',
           'schedule': crontab(minute='*/30'),  # 每 30 分钟
       }
   })
   ```

3. **提交代码**
   ```bash
   git add backend/app/tasks/cache_warmup.py
   git commit -m "feat: add cache warmup strategy"
   ```

---

### ⬜ Task 3: 数据库查询优化
**状态**: 待开始
**文件**:
- 修改: `backend/app/models/*.py`
- 创建: `backend/alembic/versions/xxx_add_indexes.py`

**步骤**:

1. **添加数据库索引**
   ```python
   # backend/alembic/versions/xxx_add_indexes.py

   def upgrade():
       # 股票表索引
       op.create_index('idx_stocks_industry', 'stocks', ['industry'])
       op.create_index('idx_stocks_market_cap', 'stocks', ['market_cap'])

       # 财务数据表索引
       op.create_index('idx_financials_roe', 'stock_financials', ['roe'])
       op.create_index('idx_financials_pe', 'stock_financials', ['pe_ttm'])

       # 策略执行历史索引
       op.create_index(
           'idx_executions_user_time',
           'strategy_executions',
           ['user_id', 'executed_at']
       )

   def downgrade():
       op.drop_index('idx_stocks_industry')
       op.drop_index('idx_stocks_market_cap')
       op.drop_index('idx_financials_roe')
       op.drop_index('idx_financials_pe')
       op.drop_index('idx_executions_user_time')
   ```

2. **优化查询语句**
   ```python
   # backend/app/services/stock_service.py

   # 优化前
   stocks = db.query(Stock).filter(Stock.pe < 15).all()

   # 优化后（使用索引 + 分页）
   stocks = db.query(Stock)\
       .filter(Stock.pe < 15)\
       .order_by(Stock.market_cap.desc())\
       .limit(100)\
       .all()
   ```

3. **使用查询缓存**
   ```python
   from sqlalchemy.orm import lazyload

   # 避免 N+1 查询
   stocks = db.query(Stock)\
       .options(lazyload(Stock.financials))\
       .filter(Stock.pe < 15)\
       .all()
   ```

4. **提交代码**
   ```bash
   alembic revision --autogenerate -m "add database indexes"
   alembic upgrade head
   git add backend/alembic/
   git commit -m "perf: add database indexes for query optimization"
   ```

---

### ⬜ Task 4: API 响应时间优化
**状态**: 待开始
**文件**:
- 修改: `backend/app/api/v1/*.py`

**步骤**:

1. **添加响应时间中间件**
   ```python
   # backend/main.py

   import time
   from fastapi import Request

   @app.middleware("http")
   async def add_process_time_header(request: Request, call_next):
       start_time = time.time()
       response = await call_next(request)
       process_time = time.time() - start_time
       response.headers["X-Process-Time"] = str(process_time)
       return response
   ```

2. **实现并发数据获取**
   ```python
   # backend/app/engines/analyzer.py

   import asyncio

   async def analyze(self, stock_code: str):
       # 并发获取数据
       realtime_task = self._get_realtime_data(stock_code)
       kline_task = self._get_kline_data(stock_code)
       financial_task = self._get_financial_data(stock_code)

       realtime, kline, financial = await asyncio.gather(
           realtime_task,
           kline_task,
           financial_task
       )

       # 并发执行分析
       fundamental_task = self._analyze_fundamental(financial)
       technical_task = self._analyze_technical(kline)

       fundamental, technical = await asyncio.gather(
           fundamental_task,
           technical_task
       )

       return self._generate_report(fundamental, technical)
   ```

3. **使用连接池**
   ```python
   # backend/app/core/database.py

   from sqlalchemy import create_engine
   from sqlalchemy.pool import QueuePool

   engine = create_engine(
       DATABASE_URL,
       poolclass=QueuePool,
       pool_size=20,  # 连接池大小
       max_overflow=10,  # 最大溢出连接数
       pool_pre_ping=True,  # 连接健康检查
       pool_recycle=3600  # 连接回收时间
   )
   ```

4. **提交代码**
   ```bash
   git add backend/
   git commit -m "perf: optimize API response time"
   ```

---

### ⬜ Task 5: 性能监控和分析
**状态**: 待开始
**文件**:
- 创建: `backend/app/core/profiler.py`

**步骤**:

1. **实现性能分析装饰器**
   ```python
   # backend/app/core/profiler.py

   import time
   import logging
   from functools import wraps

   logger = logging.getLogger(__name__)

   def profile(func):
       """性能分析装饰器"""
       @wraps(func)
       async def wrapper(*args, **kwargs):
           start_time = time.time()
           result = await func(*args, **kwargs)
           elapsed = time.time() - start_time

           if elapsed > 1.0:  # 超过 1 秒记录警告
               logger.warning(
                   f"Slow function: {func.__name__} took {elapsed:.2f}s"
               )

           return result
       return wrapper
   ```

2. **应用到关键函数**
   ```python
   # backend/app/engines/analyzer.py

   from app.core.profiler import profile

   class StockAnalyzer:
       @profile
       async def analyze(self, stock_code: str):
           # 分析逻辑
           pass
   ```

3. **添加性能指标收集**
   ```python
   # backend/app/core/metrics.py

   from prometheus_client import Counter, Histogram

   # 请求计数器
   request_count = Counter(
       'api_requests_total',
       'Total API requests',
       ['method', 'endpoint', 'status']
   )

   # 响应时间直方图
   request_duration = Histogram(
       'api_request_duration_seconds',
       'API request duration',
       ['method', 'endpoint']
   )
   ```

4. **提交代码**
   ```bash
   git add backend/app/core/profiler.py backend/app/core/metrics.py
   git commit -m "feat: add performance monitoring and profiling"
   ```

---

## 完成标准

Phase 7 完成后，系统性能应达到以下标准：

### 性能指标
- ✅ API 平均响应时间 < 500ms
- ✅ 缓存命中率 > 80%
- ✅ 数据库查询时间 < 100ms
- ✅ 并发支持 100+ 请求/秒

### 优化完成度
- ✅ 多级缓存架构实现
- ✅ 缓存预热策略
- ✅ 数据库索引优化
- ✅ 查询语句优化
- ✅ 并发处理优化
- ✅ 性能监控完善

---

## 下一步

完成 Phase 7 后，进入 **Phase 8: 监控、日志与部署**

参考文档: `docs/tasks/phase-8-devops.md`
