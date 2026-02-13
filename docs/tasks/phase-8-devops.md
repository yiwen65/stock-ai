# Phase 8: 监控、日志与部署

**优先级**: 🟢 低
**状态**: ⬜ 待开始
**预计工作量**: 中等
**依赖**: 所有核心功能完成

---

## 任务清单

### ⬜ Task 1: 结构化日志系统
**状态**: 待开始
**文件**:
- 创建: `backend/app/core/logging.py`
- 修改: `backend/main.py`

**步骤**:

1. **配置结构化日志**
   ```python
   # backend/app/core/logging.py

   import logging
   import json
   from datetime import datetime

   class JSONFormatter(logging.Formatter):
       """JSON 格式日志"""

       def format(self, record):
           log_data = {
               'timestamp': datetime.utcnow().isoformat(),
               'level': record.levelname,
               'logger': record.name,
               'message': record.getMessage(),
               'module': record.module,
               'function': record.funcName,
               'line': record.lineno
           }

           if record.exc_info:
               log_data['exception'] = self.formatException(record.exc_info)

           if hasattr(record, 'user_id'):
               log_data['user_id'] = record.user_id

           if hasattr(record, 'request_id'):
               log_data['request_id'] = record.request_id

           return json.dumps(log_data)

   def setup_logging():
       """配置日志系统"""
       # 创建日志处理器
       handler = logging.StreamHandler()
       handler.setFormatter(JSONFormatter())

       # 配置根日志器
       root_logger = logging.getLogger()
       root_logger.setLevel(logging.INFO)
       root_logger.addHandler(handler)

       # 配置应用日志器
       app_logger = logging.getLogger('app')
       app_logger.setLevel(logging.DEBUG)

       return app_logger
   ```

2. **添加请求日志中间件**
   ```python
   # backend/main.py

   import uuid
   from app.core.logging import setup_logging

   logger = setup_logging()

   @app.middleware("http")
   async def log_requests(request: Request, call_next):
       request_id = str(uuid.uuid4())
       request.state.request_id = request_id

       logger.info(
           "Request started",
           extra={
               'request_id': request_id,
               'method': request.method,
               'path': request.url.path,
               'client_ip': request.client.host
           }
       )

       start_time = time.time()
       response = await call_next(request)
       process_time = time.time() - start_time

       logger.info(
           "Request completed",
           extra={
               'request_id': request_id,
               'status_code': response.status_code,
               'process_time': process_time
           }
       )

       return response
   ```

3. **提交代码**
   ```bash
   git add backend/app/core/logging.py backend/main.py
   git commit -m "feat: add structured logging system"
   ```

---

### ⬜ Task 2: Prometheus 监控指标
**状态**: 待开始
**文件**:
- 创建: `backend/app/core/metrics.py`
- 修改: `backend/requirements.txt`
- 修改: `backend/main.py`

**步骤**:

1. **添加依赖**
   ```python
   # backend/requirements.txt
   prometheus-client==0.19.0
   ```

2. **定义监控指标**
   ```python
   # backend/app/core/metrics.py

   from prometheus_client import Counter, Histogram, Gauge, generate_latest

   # 请求计数器
   http_requests_total = Counter(
       'http_requests_total',
       'Total HTTP requests',
       ['method', 'endpoint', 'status']
   )

   # 请求延迟直方图
   http_request_duration_seconds = Histogram(
       'http_request_duration_seconds',
       'HTTP request duration',
       ['method', 'endpoint']
   )

   # 活跃连接数
   active_connections = Gauge(
       'active_connections',
       'Number of active connections'
   )

   # 缓存命中率
   cache_hits_total = Counter(
       'cache_hits_total',
       'Total cache hits',
       ['cache_type']
   )

   cache_misses_total = Counter(
       'cache_misses_total',
       'Total cache misses',
       ['cache_type']
   )

   # 数据库查询
   db_query_duration_seconds = Histogram(
       'db_query_duration_seconds',
       'Database query duration',
       ['query_type']
   )

   # Celery 任务
   celery_task_duration_seconds = Histogram(
       'celery_task_duration_seconds',
       'Celery task duration',
       ['task_name']
   )

   celery_task_total = Counter(
       'celery_task_total',
       'Total Celery tasks',
       ['task_name', 'status']
   )
   ```

3. **添加指标收集中间件**
   ```python
   # backend/main.py

   from app.core.metrics import (
       http_requests_total,
       http_request_duration_seconds,
       active_connections
   )

   @app.middleware("http")
   async def metrics_middleware(request: Request, call_next):
       active_connections.inc()

       start_time = time.time()
       response = await call_next(request)
       duration = time.time() - start_time

       # 记录指标
       http_requests_total.labels(
           method=request.method,
           endpoint=request.url.path,
           status=response.status_code
       ).inc()

       http_request_duration_seconds.labels(
           method=request.method,
           endpoint=request.url.path
       ).observe(duration)

       active_connections.dec()

       return response
   ```

4. **暴露指标端点**
   ```python
   # backend/main.py

   from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

   @app.get("/metrics")
   async def metrics():
       """Prometheus 指标端点"""
       return Response(
           content=generate_latest(),
           media_type=CONTENT_TYPE_LATEST
       )
   ```

5. **提交代码**
   ```bash
   git add backend/app/core/metrics.py backend/main.py
   git commit -m "feat: add Prometheus monitoring metrics"
   ```

---

### ⬜ Task 3: 告警机制
**状态**: 待开始
**文件**:
- 创建: `backend/app/core/alerting.py`

**步骤**:

1. **实现告警系统**
   ```python
   # backend/app/core/alerting.py

   import logging
   from typing import Dict, Any
   from enum import Enum

   logger = logging.getLogger(__name__)

   class AlertLevel(str, Enum):
       INFO = "info"
       WARNING = "warning"
       ERROR = "error"
       CRITICAL = "critical"

   class AlertManager:
       """告警管理器"""

       def __init__(self):
           self.alert_handlers = []

       def add_handler(self, handler):
           """添加告警处理器"""
           self.alert_handlers.append(handler)

       async def send_alert(
           self,
           level: AlertLevel,
           title: str,
           message: str,
           metadata: Dict[str, Any] = None
       ):
           """发送告警"""
           alert = {
               'level': level,
               'title': title,
               'message': message,
               'metadata': metadata or {},
               'timestamp': datetime.utcnow().isoformat()
           }

           logger.warning(f"Alert: {title} - {message}")

           # 调用所有处理器
           for handler in self.alert_handlers:
               try:
                   await handler.handle(alert)
               except Exception as e:
                   logger.error(f"Alert handler failed: {e}")

   class LogAlertHandler:
       """日志告警处理器"""

       async def handle(self, alert: Dict):
           logger.log(
               self._get_log_level(alert['level']),
               f"ALERT: {alert['title']} - {alert['message']}",
               extra=alert['metadata']
           )

       def _get_log_level(self, alert_level: AlertLevel):
           mapping = {
               AlertLevel.INFO: logging.INFO,
               AlertLevel.WARNING: logging.WARNING,
               AlertLevel.ERROR: logging.ERROR,
               AlertLevel.CRITICAL: logging.CRITICAL
           }
           return mapping.get(alert_level, logging.WARNING)

   # 全局告警管理器
   alert_manager = AlertManager()
   alert_manager.add_handler(LogAlertHandler())
   ```

2. **应用告警**
   ```python
   # backend/app/tasks/data_sync.py

   from app.core.alerting import alert_manager, AlertLevel

   @shared_task(name="sync_realtime_quotes")
   def sync_realtime_quotes():
       try:
           result = asyncio.run(_sync_realtime_quotes())
           return result
       except Exception as e:
           # 发送告警
           asyncio.run(alert_manager.send_alert(
               level=AlertLevel.ERROR,
               title="Data Sync Failed",
               message=f"Failed to sync realtime quotes: {str(e)}",
               metadata={'task': 'sync_realtime_quotes'}
           ))
           raise
   ```

3. **提交代码**
   ```bash
   git add backend/app/core/alerting.py
   git commit -m "feat: add alerting mechanism"
   ```

---

### ⬜ Task 4: 生产环境 Docker 配置
**状态**: 待开始
**文件**:
- 创建: `docker-compose.prod.yml`
- 创建: `backend/Dockerfile.prod`
- 创建: `frontend/Dockerfile.prod`
- 创建: `nginx/nginx.conf`

**步骤**:

1. **创建生产环境 Dockerfile**
   ```dockerfile
   # backend/Dockerfile.prod
   FROM python:3.11-slim

   WORKDIR /app

   # 安装依赖
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # 复制代码
   COPY . .

   # 创建非 root 用户
   RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
   USER appuser

   # 启动应用
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
   ```

   ```dockerfile
   # frontend/Dockerfile.prod
   FROM node:18-alpine AS builder

   WORKDIR /app
   COPY package*.json ./
   RUN npm ci
   COPY . .
   RUN npm run build

   FROM nginx:alpine
   COPY --from=builder /app/dist /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/conf.d/default.conf
   EXPOSE 80
   CMD ["nginx", "-g", "daemon off;"]
   ```

2. **创建 Nginx 配置**
   ```nginx
   # nginx/nginx.conf
   upstream backend {
       server backend:8000;
   }

   server {
       listen 80;
       server_name _;

       # 前端静态文件
       location / {
           root /usr/share/nginx/html;
           try_files $uri $uri/ /index.html;
       }

       # API 代理
       location /api {
           proxy_pass http://backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       # WebSocket 支持
       location /ws {
           proxy_pass http://backend;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

3. **创建生产环境 Docker Compose**
   ```yaml
   # docker-compose.prod.yml
   version: '3.8'

   services:
     postgres:
       image: postgres:15
       environment:
         POSTGRES_DB: stock_ai
         POSTGRES_USER: ${POSTGRES_USER}
         POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
       volumes:
         - postgres_data:/var/lib/postgresql/data
       restart: always

     redis:
       image: redis:7
       volumes:
         - redis_data:/data
       restart: always

     influxdb:
       image: influxdb:2.7
       environment:
         DOCKER_INFLUXDB_INIT_MODE: setup
         DOCKER_INFLUXDB_INIT_USERNAME: ${INFLUXDB_USER}
         DOCKER_INFLUXDB_INIT_PASSWORD: ${INFLUXDB_PASSWORD}
         DOCKER_INFLUXDB_INIT_ORG: stock-ai
         DOCKER_INFLUXDB_INIT_BUCKET: stock_data
         DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: ${INFLUXDB_TOKEN}
       volumes:
         - influxdb_data:/var/lib/influxdb2
       restart: always

     backend:
       build:
         context: ./backend
         dockerfile: Dockerfile.prod
       environment:
         - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/stock_ai
         - REDIS_HOST=redis
         - INFLUXDB_URL=http://influxdb:8086
       depends_on:
         - postgres
         - redis
         - influxdb
       restart: always

     celery_worker:
       build:
         context: ./backend
         dockerfile: Dockerfile.prod
       command: celery -A app.core.celery_app worker --loglevel=info
       environment:
         - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/stock_ai
         - REDIS_HOST=redis
       depends_on:
         - redis
         - postgres
       restart: always

     celery_beat:
       build:
         context: ./backend
         dockerfile: Dockerfile.prod
       command: celery -A app.core.celery_app beat --loglevel=info
       environment:
         - REDIS_HOST=redis
       depends_on:
         - redis
       restart: always

     frontend:
       build:
         context: ./frontend
         dockerfile: Dockerfile.prod
       ports:
         - "80:80"
       depends_on:
         - backend
       restart: always

   volumes:
     postgres_data:
     redis_data:
     influxdb_data:
   ```

4. **提交代码**
   ```bash
   git add docker-compose.prod.yml backend/Dockerfile.prod frontend/Dockerfile.prod nginx/
   git commit -m "feat: add production Docker configuration"
   ```

---

### ⬜ Task 5: CI/CD 流程
**状态**: 待开始
**文件**:
- 创建: `.github/workflows/ci.yml`
- 创建: `.github/workflows/deploy.yml`

**步骤**:

1. **创建 CI 工作流**
   ```yaml
   # .github/workflows/ci.yml
   name: CI

   on:
     push:
       branches: [ main, develop ]
     pull_request:
       branches: [ main ]

   jobs:
     test-backend:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3

         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'

         - name: Install dependencies
           run: |
             cd backend
             pip install -r requirements.txt

         - name: Run tests
           run: |
             cd backend
             pytest tests/ --cov=app --cov-report=xml

         - name: Upload coverage
           uses: codecov/codecov-action@v3
           with:
             file: ./backend/coverage.xml

     test-frontend:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3

         - name: Set up Node.js
           uses: actions/setup-node@v3
           with:
             node-version: '18'

         - name: Install dependencies
           run: |
             cd frontend
             npm ci

         - name: Run tests
           run: |
             cd frontend
             npm test

         - name: Build
           run: |
             cd frontend
             npm run build

     lint:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3

         - name: Lint backend
           run: |
             cd backend
             pip install ruff
             ruff check .

         - name: Lint frontend
           run: |
             cd frontend
             npm ci
             npm run lint
   ```

2. **创建部署工作流**
   ```yaml
   # .github/workflows/deploy.yml
   name: Deploy

   on:
     push:
       branches: [ main ]

   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3

         - name: Deploy to server
           uses: appleboy/ssh-action@master
           with:
             host: ${{ secrets.SERVER_HOST }}
             username: ${{ secrets.SERVER_USER }}
             key: ${{ secrets.SSH_PRIVATE_KEY }}
             script: |
               cd /opt/stock-ai
               git pull origin main
               docker-compose -f docker-compose.prod.yml down
               docker-compose -f docker-compose.prod.yml up -d --build
   ```

3. **提交代码**
   ```bash
   git add .github/workflows/
   git commit -m "feat: add CI/CD workflows"
   ```

---

### ⬜ Task 6: 部署文档
**状态**: 待开始
**文件**:
- 创建: `docs/DEPLOYMENT.md`

**步骤**:

1. **编写部署文档**
   ```markdown
   # 部署指南

   ## 环境要求

   - Docker 24+
   - Docker Compose 2.0+
   - 2 核 CPU, 4GB RAM（最低）
   - 50GB 磁盘空间

   ## 部署步骤

   ### 1. 克隆代码
   ```bash
   git clone https://github.com/your-org/stock-ai.git
   cd stock-ai
   ```

   ### 2. 配置环境变量
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，设置数据库密码、API 密钥等
   ```

   ### 3. 启动服务
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

   ### 4. 初始化数据库
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

   ### 5. 验证部署
   ```bash
   curl http://localhost/api/v1/health
   ```

   ## 监控

   - Prometheus 指标: http://localhost:8000/metrics
   - Celery 监控: http://localhost:5555

   ## 备份

   ### 数据库备份
   ```bash
   docker-compose exec postgres pg_dump -U stock_user stock_ai > backup.sql
   ```

   ### 恢复
   ```bash
   docker-compose exec -T postgres psql -U stock_user stock_ai < backup.sql
   ```
   ```

2. **提交代码**
   ```bash
   git add docs/DEPLOYMENT.md
   git commit -m "docs: add deployment guide"
   ```

---

## 完成标准

Phase 8 完成后，系统应具备以下能力：

### 监控完整性
- ✅ 结构化日志系统
- ✅ Prometheus 监控指标
- ✅ 告警机制
- ✅ 性能监控

### 部署就绪
- ✅ 生产环境 Docker 配置
- ✅ Nginx 反向代理
- ✅ CI/CD 流程
- ✅ 部署文档

### 运维能力
- ✅ 日志查询和分析
- ✅ 指标监控和告警
- ✅ 自动化部署
- ✅ 备份和恢复

---

## 项目完成

完成 Phase 8 后，整个项目开发完成！

所有核心功能已实现：
- ✅ 选股引擎
- ✅ 个股分析
- ✅ AI 智能分析
- ✅ 数据同步
- ✅ 前端应用
- ✅ 用户认证
- ✅ 性能优化
- ✅ 监控部署

项目可以投入生产使用。
