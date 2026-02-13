# backend/app/api/v1/analysis.py

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.cache import get_cache
from app.engines.analyzer import StockAnalyzer
from app.schemas.analysis import AnalysisReport
import json

router = APIRouter()


@router.post("/{stock_code}/analyze", response_model=AnalysisReport)
async def analyze_stock(
    stock_code: str,
    report_type: str = Query(
        "comprehensive",
        regex="^(comprehensive|fundamental|technical)$",
        description="报告类型: comprehensive/fundamental/technical"
    ),
    force_refresh: bool = Query(
        False,
        description="是否强制刷新缓存"
    ),
    db: Session = Depends(get_db),
    cache = Depends(get_cache)
):
    """
    生成个股分析报告

    Args:
        stock_code: 股票代码（如 600519）
        report_type: 报告类型
            - comprehensive: 综合分析（基本面+技术面+资金面）
            - fundamental: 仅基本面分析
            - technical: 仅技术面分析
        force_refresh: 是否强制刷新缓存

    Returns:
        AnalysisReport: 完整的分析报告
    """
    try:
        analyzer = StockAnalyzer(db=db, cache=cache)
        report = await analyzer.analyze(stock_code, report_type, force_refresh)
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/{stock_code}/report", response_model=AnalysisReport)
async def get_analysis_report(
    stock_code: str,
    cache = Depends(get_cache)
):
    """
    获取缓存的分析报告

    Args:
        stock_code: 股票代码

    Returns:
        AnalysisReport: 缓存的分析报告

    Raises:
        404: 报告未找到（未生成或已过期）
    """
    try:
        cache_key = f"analysis:report:{stock_code}"
        cached = cache.get(cache_key)

        if not cached:
            raise HTTPException(
                status_code=404,
                detail=f"Report not found for stock {stock_code}. Please generate a new report first."
            )

        return AnalysisReport(**json.loads(cached))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve report: {str(e)}"
        )
