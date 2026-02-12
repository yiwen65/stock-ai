# backend/app/services/data_service.py
import akshare as ak
import pandas as pd
from typing import List, Dict

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
