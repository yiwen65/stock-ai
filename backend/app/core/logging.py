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
