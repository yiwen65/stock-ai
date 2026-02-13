# Phase 4: 数据同步系统

**优先级**: 🟡 中
**状态**: ⬜ 待开始
**预计工作量**: 中等
**依赖**: Phase 1C 完成

---

## 任务清单

### ⬜ Task 1: Celery 任务队列配置
**状态**: 待开始
**文件**:
- 创建: `backend/app/core/celery_app.py`
- 修改: `backend/requirements.txt`
- 修改: `docker-compose.yml`

**步骤**:

1. **添加 Celery 依赖**
   ```python
   # backend/requirements.txt
   celery==5.3.6
   redis==5.0.1
   flower==2.0.1  # Celery 监控工具
   ```

2. **配置 Celery 应用**
   ```python
   # backend/app/core/celery_app.py

   from celery import Celery
   from app.core.config import settings

   celery_app = Celery(
       "stock_ai",
       broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
       backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
   )

   celery_app.conf.update(
       task_serializer='json',
       accept_content=['json'],
       result_serializer='json',
       timezone='Asia/Shanghai',
       enable_utc=True,
       task_track_started=True,
       task_time_limit=300,  # 5 分钟超时
       worker_prefetch_multiplier=1,
       worker_max_tasks_per_child=1000
   )

   # 自动发现任务
   celery_app.autodiscover_tasks(['app.tasks'])
   ```

3. **添加 Celery Worker 到 Docker Compose**
   ```yaml
   # docker-compose.yml

   celery_worker:
     build: ./backend
     command: celery -A app.core.celery_app worker --loglevel=info
     volumes:
       - ./backend:/app
     depends_on:
       - redis
       - postgres
     environment:
       - REDIS_HOST=redis
       - POSTGRES_HOST=postgres

   celery_beat:
     build: ./backend
     command: celery -A app.core.celery_app beat --loglevel=info
     volumes:
       - ./backend:/app
     depends_on:
       - redis
     environment:
       - REDIS_HOST=redis

   flower:
     build: ./backend
     command: celery -A app.core.celery_app flower --port=5555
     ports:
       - "5555:5555"
     depends_on:
       - redis
       - celery_worker
   ```

4. **启动 Celery**
   ```bash
   docker-compose up -d celery_worker celery_beat flower
   ```

5. **提交代码**
   ```bash
   git add backend/app/core/celery_app.py docker-compose.yml
   git commit -m "feat: add Celery task queue configuration"
   ```

---

### ⬜ Task 2: 实时行情同步任务
**状态**: 待开始
**文件**:
- 创建: `backend/app/tasks/data_sync.py`
- 创建: `backend/tests/unit/test_data_sync.py`

**步骤**:

1. **实现实时行情同步任务**
   ```python
   # backend/app/tasks/data_sync.py

   from celery import shared_task
   from app.services.data_service import DataService
   from app.core.cache import get_redis
   from app.core.database import get_influxdb
   import asyncio

   @shared_task(name="sync_realtime_quotes")
   def sync_realtime_quotes():
       """同步实时行情（交易时间每 3 秒执行）"""
       asyncio.run(_sync_realtime_quotes())

   async def _sync_realtime_quotes():
       data_service = DataService()
       redis = get_redis()
       influxdb = get_influxdb()

       # 1. 获取所有股票代码
       stock_codes = await data_service.get_all_stock_codes()

       # 2. 批量获取实时行情
       quotes = await data_service.fetch_realtime_quotes_batch(stock_codes)

       # 3. 写入 Redis（TTL: 5秒）
       for quote in quotes:
           cache_key = f"stock:realtime:{quote['stock_code']}"
           await redis.setex(cache_key, 5, json.dumps(quote))

       # 4. 写入 InfluxDB
       await influxdb.write_realtime_quotes(quotes)

       return len(quotes)
   ```

2. **配置定时任务**
   ```python
   # backend/app/core/celery_app.py

   from celery.schedules import crontab

   celery_app.conf.beat_schedule = {
       'sync-realtime-quotes': {
           'task': 'sync_realtime_quotes',
           'schedule': 3.0,  # 每 3 秒
           'options': {
               'expires': 2.0  # 2 秒后过期
           }
       }
   }
   ```

3. **添加交易时间判断**
   ```python
   def is_trading_time() -> bool:
       """判断是否在交易时间"""
       now = datetime.now()
       weekday = now.weekday()

       # 周末不交易
       if weekday >= 5:
           return False

       # 交易时间: 9:30-11:30, 13:00-15:00
       time_now = now.time()
       morning_start = time(9, 30)
       morning_end = time(11, 30)
       afternoon_start = time(13, 0)
       afternoon_end = time(15, 0)

       return (morning_start <= time_now <= morning_end) or \
              (afternoon_start <= time_now <= afternoon_end)

   @shared_task(name="sync_realtime_quotes")
   def sync_realtime_quotes():
       if not is_trading_time():
           return "Not trading time"

       asyncio.run(_sync_realtime_quotes())
   ```

4. **提交代码**
   ```bash
   git add backend/app/tasks/data_sync.py
   git commit -m "feat: add realtime quotes sync task"
   ```

---

### ⬜ Task 3: 历史数据同步任务
**状态**: 待开始
**文件**:
- 修改: `backend/app/tasks/data_sync.py`

**步骤**:

1. **实现 K 线数据同步**
   ```python
   @shared_task(name="sync_kline_data")
   def sync_kline_data(stock_code: str, period: str = '1d'):
       """同步 K 线数据"""
       asyncio.run(_sync_kline_data(stock_code, period))

   async def _sync_kline_data(stock_code: str, period: str):
       data_service = DataService()
       influxdb = get_influxdb()

       # 获取 K 线数据（最近 500 天）
       kline_data = await data_service.fetch_kline_data(
           stock_code, period=period, days=500
       )

       # 写入 InfluxDB
       await influxdb.write_kline_data(stock_code, period, kline_data)

       return len(kline_data)
   ```

2. **实现财务数据同步**
   ```python
   @shared_task(name="sync_financial_data")
   def sync_financial_data(stock_code: str):
       """同步财务数据"""
       asyncio.run(_sync_financial_data(stock_code))

   async def _sync_financial_data(stock_code: str):
       data_service = DataService()
       db = get_db()

       # 获取财务数据（最近 5 年）
       financials = await data_service.fetch_financial_data(stock_code, years=5)

       # 写入 PostgreSQL
       for financial in financials:
           db.merge(StockFinancial(**financial))
       db.commit()

       return len(financials)
   ```

3. **实现批量同步任务**
   ```python
   @shared_task(name="sync_all_stocks_data")
   def sync_all_stocks_data():
       """批量同步所有股票数据"""
       asyncio.run(_sync_all_stocks_data())

   async def _sync_all_stocks_data():
       data_service = DataService()
       stock_codes = await data_service.get_all_stock_codes()

       # 使用 Celery group 并行执行
       from celery import group
       job = group(
           sync_kline_data.s(code) for code in stock_codes
       )
       result = job.apply_async()

       return f"Syncing {len(stock_codes)} stocks"
   ```

4. **配置每日同步任务**
   ```python
   # backend/app/core/celery_app.py

   celery_app.conf.beat_schedule.update({
       'sync-all-stocks-daily': {
           'task': 'sync_all_stocks_data',
           'schedule': crontab(hour=16, minute=0),  # 每天 16:00
       }
   })
   ```

5. **提交代码**
   ```bash
   git add backend/app/tasks/data_sync.py backend/app/core/celery_app.py
   git commit -m "feat: add historical data sync tasks"
   ```

---

### ⬜ Task 4: 技术指标计算任务
**状态**: 待开始
**文件**:
- 创建: `backend/app/tasks/indicator_calc.py`

**步骤**:

1. **实现技术指标计算任务**
   ```python
   # backend/app/tasks/indicator_calc.py

   @shared_task(name="calculate_indicators")
   def calculate_indicators(stock_code: str):
       """计算技术指标"""
       asyncio.run(_calculate_indicators(stock_code))

   async def _calculate_indicators(stock_code: str):
       from app.utils.indicators import (
           calculate_ma, calculate_macd, calculate_rsi, calculate_kdj
       )

       influxdb = get_influxdb()

       # 1. 获取 K 线数据
       kline_data = await influxdb.read_kline_data(stock_code, period='1d', days=120)

       if len(kline_data) < 60:
           return "Insufficient data"

       df = pd.DataFrame(kline_data)

       # 2. 计算各类指标
       ma_data = calculate_ma(df['close'], [5, 10, 20, 60])
       macd_data = calculate_macd(df['close'])
       rsi_data = calculate_rsi(df['close'], [6, 12, 24])
       kdj_data = calculate_kdj(df['high'], df['low'], df['close'])

       # 3. 写入 InfluxDB
       indicators = {
           **ma_data,
           **macd_data,
           **rsi_data,
           **kdj_data
       }

       await influxdb.write_indicators(stock_code, indicators)

       return "Indicators calculated"
   ```

2. **配置指标计算任务**
   ```python
   # backend/app/core/celery_app.py

   celery_app.conf.beat_schedule.update({
       'calculate-indicators-daily': {
           'task': 'calculate_all_indicators',
           'schedule': crontab(hour=16, minute=30),  # 每天 16:30
       }
   })
   ```

3. **提交代码**
   ```bash
   git add backend/app/tasks/indicator_calc.py
   git commit -m "feat: add technical indicator calculation tasks"
   ```

---

### ⬜ Task 5: 容错和重试机制
**状态**: 待开始
**文件**:
- 修改: `backend/app/tasks/data_sync.py`
- 创建: `backend/app/utils/retry.py`

**步骤**:

1. **实现重试装饰器**
   ```python
   # backend/app/utils/retry.py

   from functools import wraps
   import time

   def retry_on_failure(max_retries=3, delay=1, backoff=2):
       """重试装饰器"""
       def decorator(func):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               retries = 0
               current_delay = delay

               while retries < max_retries:
                   try:
                       return await func(*args, **kwargs)
                   except Exception as e:
                       retries += 1
                       if retries >= max_retries:
                           raise

                       print(f"Retry {retries}/{max_retries} after {current_delay}s: {e}")
                       time.sleep(current_delay)
                       current_delay *= backoff

               return None
           return wrapper
       return decorator
   ```

2. **添加任务重试配置**
   ```python
   # backend/app/tasks/data_sync.py

   @shared_task(
       name="sync_realtime_quotes",
       bind=True,
       max_retries=3,
       default_retry_delay=60
   )
   def sync_realtime_quotes(self):
       try:
           if not is_trading_time():
               return "Not trading time"

           asyncio.run(_sync_realtime_quotes())
       except Exception as exc:
           # 重试任务
           raise self.retry(exc=exc, countdown=60)
   ```

3. **添加错误日志**
   ```python
   import logging

   logger = logging.getLogger(__name__)

   @shared_task(name="sync_realtime_quotes")
   def sync_realtime_quotes():
       try:
           asyncio.run(_sync_realtime_quotes())
       except Exception as e:
           logger.error(f"Failed to sync realtime quotes: {e}", exc_info=True)
           raise
   ```

4. **提交代码**
   ```bash
   git add backend/app/tasks/ backend/app/utils/retry.py
   git commit -m "feat: add retry mechanism and error handling for tasks"
   ```

---

## 完成标准

Phase 4 完成后，数据同步系统应具备以下能力：

### 功能完整性
- ✅ Celery 任务队列配置
- ✅ 实时行情同步（交易时间每 3 秒）
- ✅ 历史 K 线数据同步
- ✅ 财务数据同步
- ✅ 技术指标计算
- ✅ 定时任务调度

### 质量标准
- ✅ 任务执行成功率 > 95%
- ✅ 错误重试机制完善
- ✅ 日志记录完整

### 性能标准
- ✅ 实时行情同步延迟 < 5s
- ✅ 批量同步支持并发
- ✅ 任务队列不积压

---

## 下一步

完成 Phase 4 后，进入 **Phase 5: 前端应用开发**

参考文档: `docs/tasks/phase-5-frontend.md`
