# backend/app/api/v1/strategy.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from sqlalchemy.orm import Session
from app.schemas.strategy import (
    StrategyExecuteRequest, StockPickResult,
    UserStrategyCreate, UserStrategyUpdate, UserStrategyResponse,
    StrategyExecutionResponse,
)
from app.schemas.strategy_parse import StrategyParseRequest, StrategyParseResponse
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.strategy import UserStrategy, StrategyExecution
from app.engines.strategies.graham import GrahamStrategy
from app.engines.strategies.buffett import BuffettStrategy
from app.engines.strategies.peg import PEGStrategy
from app.engines.strategies.lynch import LynchStrategy
from app.engines.strategies.ma_breakout import MABreakoutStrategy
from app.engines.strategies.macd_divergence import MACDDivergenceStrategy
from app.engines.strategies.volume_breakout import VolumeBreakoutStrategy
from app.engines.strategies.earnings_surprise import EarningsSurpriseStrategy
from app.engines.strategies.northbound import NorthboundStrategy
from app.engines.strategies.rs_momentum import RSMomentumStrategy
from app.engines.strategies.quality_factor import QualityFactorStrategy
from app.engines.strategies.dual_momentum import DualMomentumStrategy
from app.engines.strategies.shareholder_increase import ShareholderIncreaseStrategy
from app.engines.stock_filter import StockFilter
from app.engines.strategy_parser import StrategyParser
from app.services.llm_service import LLMService
from app.core.llm_config import LLMSettings
from app.core.cache import cache_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

STRATEGY_REGISTRY = {
    "graham": {"cls": GrahamStrategy, "description": "格雷厄姆价值投资策略", "category": "value"},
    "buffett": {"cls": BuffettStrategy, "description": "巴菲特护城河策略", "category": "value"},
    "peg": {"cls": PEGStrategy, "description": "PEG成长策略", "category": "growth"},
    "lynch": {"cls": LynchStrategy, "description": "彼得·林奇成长策略", "category": "growth"},
    "ma_breakout": {"cls": MABreakoutStrategy, "description": "均线多头排列策略", "category": "technical"},
    "macd_divergence": {"cls": MACDDivergenceStrategy, "description": "MACD底背离策略", "category": "technical"},
    "volume_breakout": {"cls": VolumeBreakoutStrategy, "description": "放量突破平台策略", "category": "technical"},
    "earnings_surprise": {"cls": EarningsSurpriseStrategy, "description": "业绩预增事件驱动策略", "category": "event"},
    "northbound": {"cls": NorthboundStrategy, "description": "北向资金持续流入策略", "category": "capital"},
    "rs_momentum": {"cls": RSMomentumStrategy, "description": "RS相对强度动量策略", "category": "technical"},
    "quality_factor": {"cls": QualityFactorStrategy, "description": "质量因子策略", "category": "value"},
    "dual_momentum": {"cls": DualMomentumStrategy, "description": "双动量策略", "category": "technical"},
    "shareholder_increase": {"cls": ShareholderIncreaseStrategy, "description": "股东增持/回购策略", "category": "event"},
}


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
        if request.strategy_type == "custom":
            if not request.conditions:
                raise HTTPException(status_code=400, detail="Custom strategy requires conditions")
            filter_engine = StockFilter()
            # Apply industry filter if specified
            if request.include_industries or request.exclude_industries:
                filter_engine.risk_filter.set_industry_filter(
                    include=request.include_industries,
                    exclude=request.exclude_industries,
                )
            results = await filter_engine.apply_filter(request.conditions.conditions)
        elif request.strategy_type in STRATEGY_REGISTRY:
            strategy_info = STRATEGY_REGISTRY[request.strategy_type]
            strategy = strategy_info["cls"]()
            # Apply industry filter if specified
            if request.include_industries or request.exclude_industries:
                strategy.filter_engine.risk_filter.set_industry_filter(
                    include=request.include_industries,
                    exclude=request.exclude_industries,
                )
            results = await strategy.execute(params=request.params)
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
                price=stock.get("price"),
                pct_change=stock.get("pct_change"),
                market_cap=stock.get("market_cap", 0),
                pe=stock.get("pe"),
                pb=stock.get("pb"),
                roe=stock.get("roe"),
                turnover_rate=stock.get("turnover_rate"),
                score=stock.get("score"),
                risk_level=stock.get("risk_level"),
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
        logger.error(f"Strategy execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Strategy execution failed: {str(e)}")

@router.get("", response_model=List[Dict])
async def list_strategies():
    """List all available strategies"""
    return [
        {
            "name": name,
            "description": info["description"],
            "category": info["category"],
        }
        for name, info in STRATEGY_REGISTRY.items()
    ] + [
        {"name": "custom", "description": "自定义策略", "category": "custom"}
    ]

@router.get("/industries", response_model=List[str])
async def list_industries():
    """获取申万行业分类列表（用于行业筛选下拉框）"""
    try:
        import akshare as ak
        df = ak.stock_board_industry_name_em()
        if not df.empty and "板块名称" in df.columns:
            return sorted(df["板块名称"].tolist())
        return []
    except Exception as e:
        logger.warning(f"Failed to fetch industry list: {e}")
        return []


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


# ---- User Strategy CRUD ----


@router.get("/user/list", response_model=List[UserStrategyResponse])
async def list_user_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户保存的策略列表"""
    strategies = (
        db.query(UserStrategy)
        .filter(UserStrategy.user_id == current_user.id)
        .order_by(UserStrategy.updated_at.desc())
        .all()
    )
    return [
        UserStrategyResponse(
            id=s.id,
            user_id=s.user_id,
            name=s.name,
            strategy_type=s.strategy_type,
            conditions=s.conditions,
            created_at=str(s.created_at) if s.created_at else None,
            updated_at=str(s.updated_at) if s.updated_at else None,
        )
        for s in strategies
    ]


@router.post("/user/create", response_model=UserStrategyResponse, status_code=201)
async def create_user_strategy(
    body: UserStrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """保存用户策略"""
    count = db.query(UserStrategy).filter(UserStrategy.user_id == current_user.id).count()
    if count >= 50:
        raise HTTPException(status_code=400, detail="策略数量已达上限(50)")

    strategy = UserStrategy(
        user_id=current_user.id,
        name=body.name,
        strategy_type=body.strategy_type,
        conditions=body.conditions,
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return UserStrategyResponse(
        id=strategy.id,
        user_id=strategy.user_id,
        name=strategy.name,
        strategy_type=strategy.strategy_type,
        conditions=strategy.conditions,
        created_at=str(strategy.created_at) if strategy.created_at else None,
        updated_at=str(strategy.updated_at) if strategy.updated_at else None,
    )


@router.put("/user/{strategy_id}", response_model=UserStrategyResponse)
async def update_user_strategy(
    strategy_id: int,
    body: UserStrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新用户策略"""
    strategy = (
        db.query(UserStrategy)
        .filter(UserStrategy.id == strategy_id, UserStrategy.user_id == current_user.id)
        .first()
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    if body.name is not None:
        strategy.name = body.name
    if body.strategy_type is not None:
        strategy.strategy_type = body.strategy_type
    if body.conditions is not None:
        strategy.conditions = body.conditions

    db.commit()
    db.refresh(strategy)
    return UserStrategyResponse(
        id=strategy.id,
        user_id=strategy.user_id,
        name=strategy.name,
        strategy_type=strategy.strategy_type,
        conditions=strategy.conditions,
        created_at=str(strategy.created_at) if strategy.created_at else None,
        updated_at=str(strategy.updated_at) if strategy.updated_at else None,
    )


@router.delete("/user/{strategy_id}", status_code=204)
async def delete_user_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除用户策略"""
    strategy = (
        db.query(UserStrategy)
        .filter(UserStrategy.id == strategy_id, UserStrategy.user_id == current_user.id)
        .first()
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    db.delete(strategy)
    db.commit()


# ---- Strategy Execution History ----


@router.post("/user/{strategy_id}/executions", response_model=StrategyExecutionResponse, status_code=201)
async def record_execution(
    strategy_id: int,
    result_count: int = 0,
    result_snapshot: List[Dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """记录策略执行结果"""
    strategy = (
        db.query(UserStrategy)
        .filter(UserStrategy.id == strategy_id, UserStrategy.user_id == current_user.id)
        .first()
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    execution = StrategyExecution(
        strategy_id=strategy_id,
        result_count=result_count,
        result_snapshot=result_snapshot,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return StrategyExecutionResponse(
        id=execution.id,
        strategy_id=execution.strategy_id,
        executed_at=str(execution.executed_at) if execution.executed_at else None,
        result_count=execution.result_count,
        result_snapshot=execution.result_snapshot,
    )


@router.get("/user/{strategy_id}/executions", response_model=List[StrategyExecutionResponse])
async def list_executions(
    strategy_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取策略执行历史"""
    strategy = (
        db.query(UserStrategy)
        .filter(UserStrategy.id == strategy_id, UserStrategy.user_id == current_user.id)
        .first()
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    executions = (
        db.query(StrategyExecution)
        .filter(StrategyExecution.strategy_id == strategy_id)
        .order_by(StrategyExecution.executed_at.desc())
        .limit(limit)
        .all()
    )
    return [
        StrategyExecutionResponse(
            id=e.id,
            strategy_id=e.strategy_id,
            executed_at=str(e.executed_at) if e.executed_at else None,
            result_count=e.result_count,
            result_snapshot=e.result_snapshot,
        )
        for e in executions
    ]
