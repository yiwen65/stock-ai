# backend/app/engines/stock_filter.py
import pandas as pd
from typing import List, Dict
from app.schemas.strategy import FilterCondition, ConditionOperator
from app.services.data_service import DataService
from app.engines.risk_filter import RiskFilter

class StockFilter:
    def __init__(self):
        self.data_service = DataService()
        self.risk_filter = RiskFilter()

    async def apply_filter(
        self,
        conditions: List[FilterCondition],
        apply_risk_filters: bool = True
    ) -> List[Dict]:
        """Apply filter conditions to stock universe"""
        # Get all stocks
        stocks = await self.data_service.fetch_stock_list()

        # Apply risk filters first
        if apply_risk_filters:
            stocks = await self.risk_filter.apply_all_filters(stocks)

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
            raise ValueError(f"Invalid field: {field}. Field does not exist in stock data.")

        # Filter out NaN values before comparison
        valid_mask = pd.notna(df[field])
        df_valid = df[valid_mask]

        if operator == ConditionOperator.GT:
            return df_valid[df_valid[field] > value]
        elif operator == ConditionOperator.LT:
            return df_valid[df_valid[field] < value]
        elif operator == ConditionOperator.GTE:
            return df_valid[df_valid[field] >= value]
        elif operator == ConditionOperator.LTE:
            return df_valid[df_valid[field] <= value]
        elif operator == ConditionOperator.EQ:
            return df_valid[df_valid[field] == value]
        elif operator == ConditionOperator.BETWEEN:
            return df_valid[(df_valid[field] >= value[0]) & (df_valid[field] <= value[1])]

        return df_valid
