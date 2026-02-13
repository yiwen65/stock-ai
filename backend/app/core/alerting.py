# backend/app/core/alerting.py

import logging
from typing import Dict, Any
from enum import Enum
from datetime import datetime

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
