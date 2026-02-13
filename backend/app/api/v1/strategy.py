# backend/app/api/v1/strategy.py
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from app.schemas.strategy import StrategyExecuteRequest, StockPickResult
from app.schemas.strategy_parse import StrategyParseRequest, StrategyParseResponse
from app.engines.strategies.graham import GrahamStrategy
from app.engines.strategies.buffett import BuffettStrategy
from app.engines.strategies.peg import PEGStrategy
from app.engines.strategies.lynch import LynchStrategy
from app.engines.stock_filter import StockFilter
from app.engines.strategy_parser import StrategyParser
from app.services.llm_service import LLMService
from app.core.llm_config import LLMSettings
from app.core.cache import cache_manager

router = APIRouter()

class StrategyInfo(Dict):
    """Strategy information model"""
    pass

@router.post("/execute", response_model=List[StockPickResult])
async def execute_strategy(request: StrategyExecuteRequest):
    """Execute stock picking strategy"""
    try:
        # Generate cache key
        cache_key = cache_manager.generate_cache_key(
            request.strategy_type,
            request.dict(exclude={"force_refresh"})
        )

        # Try to get from cache
        if not request.force_refresh:
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                return cached_result

        # Route to appropriate strategy
        if request.strategy_type == "graham":
            strategy = GrahamStrategy()
            results = await strategy.execute()
        elif request.strategy_type == "buffett":
            strategy = BuffettStrategy()
            results = await strategy.execute()
        elif request.strategy_type == "peg":
            strategy = PEGStrategy()
            results = await strategy.execute()
        elif request.strategy_type == "lynch":
            strategy = LynchStrategy()
            results = await strategy.execute()
        elif request.strategy_type == "custom":
            if not request.conditions:
                raise HTTPException(status_code=400, detail="Custom strategy requires conditions")
            filter_engine = StockFilter()
            results = await filter_engine.apply_filter(request.conditions.conditions)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown strategy type: {request.strategy_type}"
            )

        # Apply limit
        results = results[:request.limit]

        # Convert to response model
        response_data = [
            StockPickResult(
                stock_code=stock.get("stock_code", ""),
                stock_name=stock.get("stock_name", ""),
                market_cap=stock.get("market_cap", 0),
                pe=stock.get("pe"),
                pb=stock.get("pb"),
                roe=stock.get("roe"),
                score=stock.get("score")
            )
            for stock in results
        ]

        # Cache the result
        cache_manager.set(cache_key, [r.dict() for r in response_data])

        return response_data
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy execution failed: {str(e)}")

@router.get("/strategies", response_model=List[Dict])
async def list_strategies():
    """List all available strategies"""
    return [
        {"name": "graham", "description": "格雷厄姆价值投资策略"},
        {"name": "buffett", "description": "巴菲特护城河策略"},
        {"name": "peg", "description": "PEG成长策略"},
        {"name": "lynch", "description": "彼得·林奇成长策略"},
        {"name": "custom", "description": "自定义策略"}
    ]

@router.post("/parse", response_model=StrategyParseResponse)
async def parse_strategy(request: StrategyParseRequest):
    """解析自然语言策略描述"""
    try:
        llm_settings = LLMSettings()
        llm_service = LLMService(llm_settings)
        parser = StrategyParser(llm_service)
        result = await parser.parse(request.description)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy parsing failed: {str(e)}")
