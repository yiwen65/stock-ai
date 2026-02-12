# backend/app/engines/stock_filter.py
import pandas as pd
from typing import List, Dict
from app.schemas.strategy import FilterCondition, ConditionOperator
from app.services.data_service import DataService

class StockFilter:
    def __init__(self):
        self.data_service = DataService()

    async def apply_filter(self, conditions: List[FilterCondition]) -> List[Dict]:
        """Apply filter conditions to stock universe"""
        # Get all stocks
        stocks = await self.data_service.fetch_stock_list()

        # Convert to DataFrame for filtering
        df = pd.DataFrame(stocks)

        # Apply each condition
        for condition in conditions:
            df = self._apply_condition(df, condition)

        return df.to_dict('records')

    def _apply_condition(self, df: pd.DataFrame, condition: FilterCondition) -> pd.DataFrame:
        """Apply single condition to DataFrame"""
        field = condition.field
        operator = condition.operator
        value = condition.value

        if field not in df.columns:
            return df

        if operator == ConditionOperator.GT:
            return df[df[field] > value]
        elif operator == ConditionOperator.LT:
            return df[df[field] < value]
        elif operator == ConditionOperator.GTE:
            return df[df[field] >= value]
        elif operator == ConditionOperator.LTE:
            return df[df[field] <= value]
        elif operator == ConditionOperator.EQ:
            return df[df[field] == value]
        elif operator == ConditionOperator.BETWEEN:
            return df[(df[field] >= value[0]) & (df[field] <= value[1])]

        return df
