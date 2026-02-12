# backend/app/schemas/strategy.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

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

class StrategyConditions(BaseModel):
    conditions: List[FilterCondition]
    logic: Literal["AND", "OR"] = "AND"

class StrategyExecuteRequest(BaseModel):
    strategy_type: Literal["custom", "graham", "buffett", "peg"]
    conditions: Optional[StrategyConditions] = None
    limit: int = Field(default=50, ge=1, le=500)
    sort_by: Optional[str] = "market_cap"
    sort_order: Literal["asc", "desc"] = "desc"

class StockPickResult(BaseModel):
    stock_code: str
    stock_name: str
    market_cap: float
    pe: Optional[float]
    pb: Optional[float]
    roe: Optional[float]
    score: Optional[float]
