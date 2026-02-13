# backend/app/core/metrics.py

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# Request metrics
request_count = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Cache metrics
cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

cache_size = Gauge(
    'cache_size_bytes',
    'Current cache size in bytes',
    ['cache_type']
)

# Database metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
)

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Current database connection pool size'
)

db_connection_pool_overflow = Gauge(
    'db_connection_pool_overflow',
    'Current database connection pool overflow'
)

# Stock picker metrics
stock_picker_executions = Counter(
    'stock_picker_executions_total',
    'Total stock picker executions',
    ['strategy_type']
)

stock_picker_duration = Histogram(
    'stock_picker_duration_seconds',
    'Stock picker execution duration',
    ['strategy_type'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

stock_picker_results = Histogram(
    'stock_picker_results_count',
    'Number of stocks returned by picker',
    ['strategy_type'],
    buckets=(0, 10, 50, 100, 500, 1000, 5000)
)

# Analysis metrics
analysis_executions = Counter(
    'analysis_executions_total',
    'Total stock analysis executions',
    ['analysis_type']
)

analysis_duration = Histogram(
    'analysis_duration_seconds',
    'Stock analysis duration',
    ['analysis_type'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

# Data sync metrics
data_sync_executions = Counter(
    'data_sync_executions_total',
    'Total data sync executions',
    ['sync_type']
)

data_sync_duration = Histogram(
    'data_sync_duration_seconds',
    'Data sync duration',
    ['sync_type'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0)
)

data_sync_records = Counter(
    'data_sync_records_total',
    'Total records synced',
    ['sync_type']
)


def metrics_endpoint():
    """Prometheus metrics endpoint handler"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


class MetricsMiddleware:
    """Middleware to collect request metrics"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]

        # Skip metrics endpoint itself
        if path == "/metrics":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration = time.time() - start_time

                # Record metrics
                request_count.labels(
                    method=method,
                    endpoint=path,
                    status=status_code
                ).inc()

                request_duration.labels(
                    method=method,
                    endpoint=path
                ).observe(duration)

            await send(message)

        await self.app(scope, receive, send_wrapper)
