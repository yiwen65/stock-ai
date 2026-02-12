# backend/app/schemas/strategy.py
from enum import Enum
from typing import List, Optional, Literal

from pydantic import BaseModel, Field, field_validator

class ConditionOperator(str, Enum):
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "=="
    BETWEEN = "between"

class FilterCondition(BaseModel):
    field: str = Field(..., description="Field name (e.g., 'pe', 'roe', 'market_cap')")
    operator: ConditionOperator
    value: float | List[float]

    @field_validator('value')
    @classmethod
    def validate_value_for_operator(cls, v, info):
        operator = info.data.get('operator')
        if operator == ConditionOperator.BETWEEN:
            if not isinstance(v, list) or len(v) != 2:
                raise ValueError('BETWEEN operator requires exactly 2 values')
            if not all(isinstance(x, (int, float)) for x in v):
                raise ValueError('BETWEEN values must be numbers')
        else:
            if isinstance(v, list):
                raise ValueError(f'{operator.value} operator requires a single value, not a list')
        return v

    @field_validator('field')
    @classmethod
    def validate_field_name(cls, v):
        allowed_fields = {'pe', 'pb', 'roe', 'market_cap', 'debt_ratio', 'volume', 'price', 'pct_change'}
        if v not in allowed_fields:
            raise ValueError(f'Invalid field name: {v}. Allowed: {allowed_fields}')
        return v

class StrategyConditions(BaseModel):
    conditions: List[FilterCondition]
    logic: Literal["AND", "OR"] = "AND"

class StrategyExecuteRequest(BaseModel):
    strategy_type: Literal["custom", "graham", "buffett", "peg"]
    conditions: Optional[StrategyConditions] = None
    limit: int = Field(default=50, ge=1, le=500)
    sort_by: Optional[str] = "market_cap"
    sort_order: Literal["asc", "desc"] = "desc"

    @field_validator('conditions')
    @classmethod
    def validate_conditions_for_custom(cls, v, info):
        strategy_type = info.data.get('strategy_type')
        if strategy_type == 'custom' and v is None:
            raise ValueError('Custom strategy requires conditions')
        return v

class StockPickResult(BaseModel):
    stock_code: str
    stock_name: str
    market_cap: float
    pe: Optional[float]
    pb: Optional[float]
    roe: Optional[float]
    score: Optional[float]
