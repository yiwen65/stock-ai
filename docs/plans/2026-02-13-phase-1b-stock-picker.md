# Phase 1B: Stock Picking Engine Core Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build core stock picking engine with classic strategies and custom condition filtering

**Architecture:** Strategy pattern with condition-based filtering, Redis caching, async execution

**Tech Stack:** Python 3.11, FastAPI, Pandas, Redis, PostgreSQL

**Duration:** Week 3-4 of MVP (12-week timeline)

---

## Task 1: Strategy Condition Models

**Files:**
- Create: `backend/app/schemas/strategy.py`
- Create: `backend/app/models/strategy.py`
- Create: `backend/tests/unit/test_strategy_models.py`

**Step 1: Write strategy schemas**

```python
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
```

**Step 2: Write strategy database model**

```python
# backend/app/models/strategy.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class UserStrategy(Base):
    __tablename__ = "user_strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    strategy_type = Column(String(20), nullable=False)
    conditions = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Step 3: Create migration**

```bash
alembic revision --autogenerate -m "Add user_strategies table"
alembic upgrade head
```

**Step 4: Commit**

```bash
git add backend/app/schemas/strategy.py backend/app/models/strategy.py backend/alembic/
git commit -m "feat: add strategy condition models and schemas"
```

---

## Task 2: Stock Filtering Engine

**Files:**
- Create: `backend/app/engines/stock_filter.py`
- Create: `backend/tests/unit/test_stock_filter.py`

**Step 1: Write failing test**

```python
# backend/tests/unit/test_stock_filter.py
import pytest
from app.engines.stock_filter import StockFilter
from app.schemas.strategy import FilterCondition, ConditionOperator

@pytest.mark.asyncio
async def test_filter_by_pe():
    filter_engine = StockFilter()
    condition = FilterCondition(field="pe", operator=ConditionOperator.LT, value=15.0)

    stocks = await filter_engine.apply_filter([condition])

    assert isinstance(stocks, list)
    assert all(stock.get("pe", 999) < 15.0 for stock in stocks if stock.get("pe"))
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_stock_filter.py::test_filter_by_pe -v
```

Expected: FAIL with "No module named 'app.engines.stock_filter'"

**Step 3: Write minimal implementation**

```python
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
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_stock_filter.py::test_filter_by_pe -v
```

Expected: PASS

**Step 5: Add test for multiple conditions**

```python
# backend/tests/unit/test_stock_filter.py (add test)
@pytest.mark.asyncio
async def test_filter_multiple_conditions():
    filter_engine = StockFilter()
    conditions = [
        FilterCondition(field="pe", operator=ConditionOperator.LT, value=15.0),
        FilterCondition(field="pb", operator=ConditionOperator.LT, value=2.0),
    ]

    stocks = await filter_engine.apply_filter(conditions)

    assert isinstance(stocks, list)
    for stock in stocks:
        if stock.get("pe"):
            assert stock["pe"] < 15.0
        if stock.get("pb"):
            assert stock["pb"] < 2.0
```

**Step 6: Run all tests**

```bash
pytest tests/unit/test_stock_filter.py -v
```

Expected: All tests PASS

**Step 7: Commit**

```bash
git add backend/app/engines/ backend/tests/
git commit -m "feat: add stock filtering engine with condition support"
```

---

## Task 3: Classic Strategy - Graham Value

**Files:**
- Create: `backend/app/engines/strategies/graham.py`
- Create: `backend/tests/unit/test_graham_strategy.py`

**Step 1: Write failing test**

```python
# backend/tests/unit/test_graham_strategy.py
import pytest
from app.engines.strategies.graham import GrahamStrategy

@pytest.mark.asyncio
async def test_graham_strategy_execution():
    strategy = GrahamStrategy()
    results = await strategy.execute()

    assert isinstance(results, list)
    assert len(results) > 0

    # Verify Graham criteria
    for stock in results:
        assert stock.get("pe", 999) < 15
        assert stock.get("pb", 999) < 2
        assert stock.get("debt_ratio", 100) < 60
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_graham_strategy.py::test_graham_strategy_execution -v
```

Expected: FAIL with "No module named 'app.engines.strategies.graham'"

**Step 3: Write minimal implementation**

```python
# backend/app/engines/strategies/graham.py
from typing import List, Dict
from app.engines.stock_filter import StockFilter
from app.schemas.strategy import FilterCondition, ConditionOperator

class GrahamStrategy:
    """Graham Value Investing Strategy

    Criteria:
    - PE < 15
    - PB < 2
    - Debt Ratio < 60%
    - Market Cap > 5B (risk filter)
    """

    def __init__(self):
        self.filter_engine = StockFilter()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute Graham value strategy"""
        # Default parameters
        pe_max = params.get("pe_max", 15.0) if params else 15.0
        pb_max = params.get("pb_max", 2.0) if params else 2.0
        debt_max = params.get("debt_max", 60.0) if params else 60.0
        market_cap_min = params.get("market_cap_min", 5000000000) if params else 5000000000

        # Build conditions
        conditions = [
            FilterCondition(field="pe", operator=ConditionOperator.LT, value=pe_max),
            FilterCondition(field="pb", operator=ConditionOperator.LT, value=pb_max),
            FilterCondition(field="debt_ratio", operator=ConditionOperator.LT, value=debt_max),
            FilterCondition(field="market_cap", operator=ConditionOperator.GT, value=market_cap_min),
        ]

        # Apply filters
        results = await self.filter_engine.apply_filter(conditions)

        # Sort by PE (lower is better)
        results.sort(key=lambda x: x.get("pe", 999))

        return results[:50]  # Top 50 results
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_graham_strategy.py::test_graham_strategy_execution -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/engines/strategies/ backend/tests/
git commit -m "feat: add Graham value investing strategy"
```

---

## Task 4: Strategy Execution API

**Files:**
- Create: `backend/app/api/v1/strategy.py`
- Modify: `backend/main.py`

**Step 1: Write strategy API endpoints**

```python
# backend/app/api/v1/strategy.py
from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.strategy import StrategyExecuteRequest, StockPickResult
from app.engines.strategies.graham import GrahamStrategy

router = APIRouter()

@router.post("/execute", response_model=List[StockPickResult])
async def execute_strategy(request: StrategyExecuteRequest):
    """Execute stock picking strategy"""
    try:
        if request.strategy_type == "graham":
            strategy = GrahamStrategy()
            results = await strategy.execute()
        elif request.strategy_type == "custom":
            if not request.conditions:
                raise HTTPException(status_code=400, detail="Custom strategy requires conditions")
            from app.engines.stock_filter import StockFilter
            filter_engine = StockFilter()
            results = await filter_engine.apply_filter(request.conditions.conditions)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy type: {request.strategy_type}")

        # Apply limit
        results = results[:request.limit]

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy execution failed: {str(e)}")
```

**Step 2: Register router in main.py**

```python
# backend/main.py (add after stock router)
from app.api.v1 import strategy

app.include_router(strategy.router, prefix=f"{settings.API_V1_STR}/strategy", tags=["strategy"])
```

**Step 3: Test endpoint**

```bash
# Start server
cd backend && python3 -m uvicorn main:app --reload &

# Wait for startup
sleep 5

# Test Graham strategy
curl -X POST http://localhost:8000/api/v1/strategy/execute \
  -H "Content-Type: application/json" \
  -d '{"strategy_type": "graham", "limit": 10}' | jq

# Test custom strategy
curl -X POST http://localhost:8000/api/v1/strategy/execute \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_type": "custom",
    "conditions": {
      "conditions": [
        {"field": "pe", "operator": "<", "value": 20}
      ],
      "logic": "AND"
    },
    "limit": 10
  }' | jq

# Stop server
pkill -f "uvicorn main:app"
```

Expected: JSON responses with filtered stock lists

**Step 4: Commit**

```bash
git add backend/app/api/v1/strategy.py backend/main.py
git commit -m "feat: add strategy execution API endpoint"
```

---

## Task 5: Risk Filters

**Files:**
- Create: `backend/app/engines/risk_filter.py`
- Create: `backend/tests/unit/test_risk_filter.py`

**Step 1: Write failing test**

```python
# backend/tests/unit/test_risk_filter.py
import pytest
from app.engines.risk_filter import RiskFilter

@pytest.mark.asyncio
async def test_filter_st_stocks():
    risk_filter = RiskFilter()
    stocks = [
        {"stock_code": "600519", "stock_name": "贵州茅台", "is_st": False},
        {"stock_code": "600123", "stock_name": "*ST股票", "is_st": True},
    ]

    filtered = await risk_filter.filter_st_stocks(stocks)

    assert len(filtered) == 1
    assert filtered[0]["stock_code"] == "600519"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_risk_filter.py::test_filter_st_stocks -v
```

Expected: FAIL with "No module named 'app.engines.risk_filter'"

**Step 3: Write minimal implementation**

```python
# backend/app/engines/risk_filter.py
from typing import List, Dict

class RiskFilter:
    """Risk control filters for stock picking"""

    async def filter_st_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """Remove ST and *ST stocks"""
        return [s for s in stocks if not s.get("is_st", False)]

    async def filter_suspended(self, stocks: List[Dict]) -> List[Dict]:
        """Remove suspended stocks"""
        return [s for s in stocks if not s.get("is_suspended", False)]

    async def filter_low_liquidity(self, stocks: List[Dict], min_volume: int = 1000000) -> List[Dict]:
        """Remove stocks with low trading volume"""
        return [s for s in stocks if s.get("volume", 0) >= min_volume]

    async def apply_all_filters(self, stocks: List[Dict]) -> List[Dict]:
        """Apply all risk filters"""
        stocks = await self.filter_st_stocks(stocks)
        stocks = await self.filter_suspended(stocks)
        stocks = await self.filter_low_liquidity(stocks)
        return stocks
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_risk_filter.py::test_filter_st_stocks -v
```

Expected: PASS

**Step 5: Add more tests**

```python
# backend/tests/unit/test_risk_filter.py (add tests)
@pytest.mark.asyncio
async def test_filter_suspended():
    risk_filter = RiskFilter()
    stocks = [
        {"stock_code": "600519", "is_suspended": False},
        {"stock_code": "600123", "is_suspended": True},
    ]

    filtered = await risk_filter.filter_suspended(stocks)
    assert len(filtered) == 1

@pytest.mark.asyncio
async def test_apply_all_filters():
    risk_filter = RiskFilter()
    stocks = [
        {"stock_code": "600519", "is_st": False, "is_suspended": False, "volume": 2000000},
        {"stock_code": "600123", "is_st": True, "is_suspended": False, "volume": 2000000},
        {"stock_code": "600456", "is_st": False, "is_suspended": True, "volume": 2000000},
        {"stock_code": "600789", "is_st": False, "is_suspended": False, "volume": 500000},
    ]

    filtered = await risk_filter.apply_all_filters(stocks)
    assert len(filtered) == 1
    assert filtered[0]["stock_code"] == "600519"
```

**Step 6: Run all tests**

```bash
pytest tests/unit/test_risk_filter.py -v
```

Expected: All tests PASS

**Step 7: Integrate risk filters into StockFilter**

```python
# backend/app/engines/stock_filter.py (modify apply_filter method)
from app.engines.risk_filter import RiskFilter

class StockFilter:
    def __init__(self):
        self.data_service = DataService()
        self.risk_filter = RiskFilter()

    async def apply_filter(self, conditions: List[FilterCondition], apply_risk_filters: bool = True) -> List[Dict]:
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
```

**Step 8: Commit**

```bash
git add backend/app/engines/ backend/tests/
git commit -m "feat: add risk filters for ST stocks, suspended stocks, and low liquidity"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-02-13-phase-1b-stock-picker.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
