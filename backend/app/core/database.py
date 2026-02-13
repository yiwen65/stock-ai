# backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from typing import List, Dict
from datetime import datetime
import pandas as pd
from app.core.config import settings

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Connection pool size
    max_overflow=10,  # Maximum overflow connections
    pool_pre_ping=True,  # Connection health check
    pool_recycle=3600,  # Connection recycle time (1 hour)
    echo=False  # Disable SQL logging in production
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class InfluxDBManager:
    """InfluxDB manager for time-series data"""

    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.bucket = settings.INFLUXDB_BUCKET

    async def write_realtime_quotes(self, quotes: List[Dict]):
        """Write real-time quotes to InfluxDB"""
        points = []
        for quote in quotes:
            point = Point("realtime_quote") \
                .tag("stock_code", quote["stock_code"]) \
                .field("price", quote["price"]) \
                .field("change", quote["change"]) \
                .field("pct_change", quote["pct_change"]) \
                .field("volume", quote["volume"]) \
                .field("amount", quote["amount"]) \
                .field("high", quote["high"]) \
                .field("low", quote["low"]) \
                .field("open", quote["open"]) \
                .field("pre_close", quote["pre_close"]) \
                .time(datetime.now())
            points.append(point)

        self.write_api.write(bucket=self.bucket, record=points)

    async def write_kline_data(self, stock_code: str, period: str, kline_data: List[Dict]):
        """Write K-line data to InfluxDB"""
        points = []
        for data in kline_data:
            point = Point("kline") \
                .tag("stock_code", stock_code) \
                .tag("period", period) \
                .field("open", data["open"]) \
                .field("high", data["high"]) \
                .field("low", data["low"]) \
                .field("close", data["close"]) \
                .field("volume", data["volume"]) \
                .field("amount", data["amount"]) \
                .time(data["date"])
            points.append(point)

        self.write_api.write(bucket=self.bucket, record=points)

    async def write_indicators(self, stock_code: str, indicators: Dict):
        """Write technical indicators to InfluxDB"""
        points = []
        for indicator_name, values in indicators.items():
            if hasattr(values, 'items'):  # Series
                for timestamp, value in values.items():
                    if value is not None and not pd.isna(value):
                        point = Point("indicator") \
                            .tag("stock_code", stock_code) \
                            .tag("indicator", indicator_name) \
                            .field("value", float(value)) \
                            .time(timestamp)
                        points.append(point)

        if points:
            self.write_api.write(bucket=self.bucket, record=points)

    async def read_kline_data(self, stock_code: str, period: str = '1d', days: int = 120) -> List[Dict]:
        """Read K-line data from InfluxDB"""
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -{days}d)
            |> filter(fn: (r) => r["_measurement"] == "kline")
            |> filter(fn: (r) => r["stock_code"] == "{stock_code}")
            |> filter(fn: (r) => r["period"] == "{period}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

        result = self.query_api.query(query)
        kline_data = []

        for table in result:
            for record in table.records:
                kline_data.append({
                    "date": record.get_time(),
                    "open": record.values.get("open"),
                    "high": record.values.get("high"),
                    "low": record.values.get("low"),
                    "close": record.values.get("close"),
                    "volume": record.values.get("volume"),
                    "amount": record.values.get("amount")
                })

        return kline_data

    def close(self):
        """Close InfluxDB client"""
        self.client.close()


# Global InfluxDB manager instance
influxdb_manager = InfluxDBManager()

def get_influxdb():
    """Get InfluxDB manager instance"""
    return influxdb_manager
