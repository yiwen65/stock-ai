# backend/app/services/data_service.py
import akshare as ak
import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta

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

    async def get_all_stock_codes(self) -> List[str]:
        """Get all stock codes"""
        try:
            df = ak.stock_info_a_code_name()
            return df["code"].tolist()
        except Exception as e:
            print(f"Error fetching stock codes: {e}")
            return []

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

    async def fetch_realtime_quotes_batch(self, stock_codes: List[str]) -> List[Dict]:
        """Fetch real-time quotes for multiple stocks"""
        try:
            df = ak.stock_zh_a_spot_em()
            quotes = []

            for code in stock_codes:
                stock_data = df[df["代码"] == code]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    quotes.append({
                        "stock_code": code,
                        "price": float(row["最新价"]),
                        "change": float(row["涨跌额"]),
                        "pct_change": float(row["涨跌幅"]),
                        "volume": int(row["成交量"]),
                        "amount": float(row["成交额"]),
                        "high": float(row["最高"]),
                        "low": float(row["最低"]),
                        "open": float(row["今开"]),
                        "pre_close": float(row["昨收"]),
                        "timestamp": datetime.now().isoformat()
                    })

            return quotes
        except Exception as e:
            print(f"Error fetching batch quotes: {e}")
            return []

    async def fetch_kline_data(
        self,
        stock_code: str,
        period: str = '1d',
        days: int = 500
    ) -> List[Dict]:
        """Fetch K-line data for a stock"""
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

            # Map period to AKShare period format
            period_map = {
                '1d': 'daily',
                '1w': 'weekly',
                '1M': 'monthly'
            }
            ak_period = period_map.get(period, 'daily')

            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period=ak_period,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )

            kline_data = []
            for _, row in df.iterrows():
                kline_data.append({
                    "date": row["日期"],
                    "open": float(row["开盘"]),
                    "high": float(row["最高"]),
                    "low": float(row["最低"]),
                    "close": float(row["收盘"]),
                    "volume": int(row["成交量"]),
                    "amount": float(row["成交额"])
                })

            return kline_data
        except Exception as e:
            print(f"Error fetching kline data: {e}")
            return []

    async def fetch_financial_data(self, stock_code: str, years: int = 5) -> List[Dict]:
        """Fetch financial data for a stock"""
        try:
            # Fetch financial indicators
            df = ak.stock_financial_analysis_indicator(symbol=stock_code)

            # Get recent years data
            df = df.head(years * 4)  # Quarterly data

            financials = []
            for _, row in df.iterrows():
                financials.append({
                    "stock_code": stock_code,
                    "report_date": row["日期"],
                    "eps": float(row.get("基本每股收益", 0)),
                    "roe": float(row.get("净资产收益率", 0)),
                    "revenue_growth": float(row.get("营业总收入同比增长", 0)),
                    "net_profit_growth": float(row.get("净利润同比增长", 0)),
                    "debt_ratio": float(row.get("资产负债率", 0)),
                    "current_ratio": float(row.get("流动比率", 0))
                })

            return financials
        except Exception as e:
            print(f"Error fetching financial data: {e}")
            return []
