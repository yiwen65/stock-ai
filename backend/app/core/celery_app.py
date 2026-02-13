# backend/app/core/celery_app.py

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Parse Redis URL to get host and port
redis_url = settings.REDIS_URL

celery_app = Celery(
    "stock_ai",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes timeout
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'sync-realtime-quotes': {
        'task': 'sync_realtime_quotes',
        'schedule': 3.0,  # Every 3 seconds
        'options': {
            'expires': 2.0  # Expire after 2 seconds
        }
    },
    'sync-all-stocks-daily': {
        'task': 'sync_all_stocks_data',
        'schedule': crontab(hour=16, minute=0),  # Daily at 16:00
    },
    'calculate-indicators-daily': {
        'task': 'calculate_all_indicators',
        'schedule': crontab(hour=16, minute=30),  # Daily at 16:30
    },
    'warmup-hot-stocks': {
        'task': 'warmup_hot_stocks',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'warmup-market-overview': {
        'task': 'warmup_market_overview',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    }
}

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])
