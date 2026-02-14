# backend/app/schemas/strategy.py
from enum import Enum
from typing import Dict, List, Optional, Literal

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
        allowed_fields = {
            # Real-time market data
            'pe', 'pb', 'market_cap', 'circulating_market_cap',
            'price', 'pct_change', 'volume', 'amount', 'amplitude',
            'volume_ratio', 'turnover_rate', 'change_60d', 'change_ytd',
            # Financial data
            'roe', 'debt_ratio', 'current_ratio', 'eps',
            'revenue_growth', 'net_profit_growth', 'dividend_yield',
            'gross_margin', 'net_margin',
        }
        if v not in allowed_fields:
            raise ValueError(f'Invalid field name: {v}. Allowed: {allowed_fields}')
        return v

class StrategyConditions(BaseModel):
    conditions: List[FilterCondition]
    logic: Literal["AND", "OR"] = "AND"

class StrategyExecuteRequest(BaseModel):
    strategy_type: Literal[
        "custom", "graham", "buffett", "peg", "lynch",
        "ma_breakout", "macd_divergence", "volume_breakout",
        "earnings_surprise", "northbound",
        "rs_momentum", "quality_factor",
        "dual_momentum", "shareholder_increase"
    ]
    conditions: Optional[StrategyConditions] = None
    params: Optional[Dict] = Field(default=None, description="Strategy-specific parameters")
    limit: int = Field(default=50, ge=1, le=500)
    sort_by: Optional[str] = "market_cap"
    sort_order: Literal["asc", "desc"] = "desc"
    force_refresh: bool = Field(default=False, description="Force refresh cache")
    include_industries: Optional[List[str]] = Field(default=None, description="Only include stocks in these industries (申万行业)")
    exclude_industries: Optional[List[str]] = Field(default=None, description="Exclude stocks in these industries")

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
    price: Optional[float] = None
    pct_change: Optional[float] = None
    market_cap: float
    pe: Optional[float] = None
    pb: Optional[float] = None
    roe: Optional[float] = None
    turnover_rate: Optional[float] = None
    score: Optional[float] = None
    risk_level: Optional[str] = None


# ---- User Strategy CRUD schemas ----

class UserStrategyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    strategy_type: str = Field(..., max_length=20)
    conditions: Dict = Field(...)

class UserStrategyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    strategy_type: Optional[str] = Field(None, max_length=20)
    conditions: Optional[Dict] = None

class UserStrategyResponse(BaseModel):
    id: int
    user_id: int
    name: str
    strategy_type: str
    conditions: Dict
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class StrategyExecutionCreate(BaseModel):
    strategy_id: int
    result_count: int
    result_snapshot: Optional[List[Dict]] = None

class StrategyExecutionResponse(BaseModel):
    id: int
    strategy_id: int
    executed_at: Optional[str] = None
    result_count: int
    result_snapshot: Optional[List[Dict]] = None

    class Config:
        from_attributes = True
