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

必需的环境变量：

```env
# PostgreSQL
POSTGRES_USER=stock_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=stock_ai

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# InfluxDB
INFLUXDB_USER=admin
INFLUXDB_PASSWORD=your_secure_password
INFLUXDB_ORG=stock-ai
INFLUXDB_BUCKET=stock_data
INFLUXDB_TOKEN=your_secure_token

# JWT
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM API
OPENAI_API_KEY=your_openai_api_key
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

预期响应：
```json
{
  "status": "healthy"
}
```

## 监控

### Prometheus 指标

访问 Prometheus 指标端点：
```bash
curl http://localhost:8000/metrics
```

可用指标：
- `api_requests_total` - API 请求总数
- `api_request_duration_seconds` - API 请求延迟
- `cache_hits_total` - 缓存命中次数
- `cache_misses_total` - 缓存未命中次数
- `db_query_duration_seconds` - 数据库查询延迟
- `stock_picker_executions_total` - 选股执行次数
- `analysis_executions_total` - 分析执行次数
- `data_sync_executions_total` - 数据同步执行次数

### Celery 监控

访问 Flower 监控界面：
```
http://localhost:5555
```

## 日志

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

### 日志格式

应用使用结构化 JSON 日志格式：

```json
{
  "timestamp": "2026-02-14T10:30:00.000Z",
  "level": "INFO",
  "logger": "app",
  "message": "Request completed",
  "module": "main",
  "function": "log_requests",
  "line": 45,
  "request_id": "abc-123-def",
  "status_code": 200,
  "process_time": 0.123
}
```

## 备份

### 数据库备份

#### PostgreSQL 备份

```bash
# 备份
docker-compose exec postgres pg_dump -U stock_user stock_ai > backup_$(date +%Y%m%d).sql

# 恢复
docker-compose exec -T postgres psql -U stock_user stock_ai < backup_20260214.sql
```

#### InfluxDB 备份

```bash
# 备份
docker-compose exec influxdb influx backup /tmp/backup
docker-compose cp influxdb:/tmp/backup ./influxdb_backup_$(date +%Y%m%d)

# 恢复
docker-compose cp ./influxdb_backup_20260214 influxdb:/tmp/backup
docker-compose exec influxdb influx restore /tmp/backup
```

### 自动备份脚本

创建 `scripts/backup.sh`：

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/stock-ai"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份 PostgreSQL
docker-compose exec -T postgres pg_dump -U stock_user stock_ai > $BACKUP_DIR/postgres_$DATE.sql

# 备份 InfluxDB
docker-compose exec influxdb influx backup /tmp/backup
docker-compose cp influxdb:/tmp/backup $BACKUP_DIR/influxdb_$DATE

# 压缩备份
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/postgres_$DATE.sql $BACKUP_DIR/influxdb_$DATE

# 删除 7 天前的备份
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/backup_$DATE.tar.gz"
```

添加到 crontab（每天凌晨 2 点执行）：
```bash
0 2 * * * /opt/stock-ai/scripts/backup.sh
```

## 扩展

### 水平扩展

#### 扩展 Backend 服务

```bash
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

#### 扩展 Celery Worker

```bash
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=5
```

### 负载均衡

Nginx 配置已包含负载均衡支持。修改 `nginx/nginx.conf`：

```nginx
upstream backend {
    server backend_1:8000;
    server backend_2:8000;
    server backend_3:8000;
}
```

## 故障排查

### 服务无法启动

1. 检查端口占用：
```bash
netstat -tulpn | grep -E '80|8000|5432|6379|8086'
```

2. 检查 Docker 日志：
```bash
docker-compose logs backend
```

3. 检查磁盘空间：
```bash
df -h
```

### 数据库连接失败

1. 检查 PostgreSQL 状态：
```bash
docker-compose exec postgres pg_isready
```

2. 检查连接配置：
```bash
docker-compose exec backend env | grep DATABASE_URL
```

### Redis 连接失败

1. 检查 Redis 状态：
```bash
docker-compose exec redis redis-cli ping
```

2. 检查连接配置：
```bash
docker-compose exec backend env | grep REDIS
```

### Celery 任务不执行

1. 检查 Celery Worker 状态：
```bash
docker-compose exec celery_worker celery -A app.core.celery_app inspect active
```

2. 检查 Celery Beat 状态：
```bash
docker-compose logs celery_beat
```

## 安全建议

1. **修改默认密码**：确保所有数据库和服务使用强密码
2. **启用 HTTPS**：在生产环境中使用 SSL/TLS 证书
3. **限制网络访问**：使用防火墙限制对数据库端口的访问
4. **定期更新**：保持 Docker 镜像和依赖包更新
5. **备份加密**：对备份文件进行加密存储
6. **日志审计**：定期审查日志文件，检测异常活动

## 性能优化

1. **数据库连接池**：调整 PostgreSQL 连接池大小
2. **Redis 内存**：根据缓存需求调整 Redis 最大内存
3. **Celery 并发**：根据 CPU 核心数调整 Worker 并发数
4. **Nginx 缓存**：启用静态资源缓存
5. **数据库索引**：为常用查询字段添加索引

## 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动服务
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# 运行数据库迁移
docker-compose exec backend alembic upgrade head
```

## 回滚

```bash
# 回滚到指定版本
git checkout <commit-hash>
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# 回滚数据库迁移
docker-compose exec backend alembic downgrade -1
```
