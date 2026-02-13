# backend/app/schemas/analysis.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class FundamentalAnalysis(BaseModel):
    score: float = Field(..., ge=0, le=10, description="基本面综合评分 (0-10)")
    valuation: Dict[str, float] = Field(..., description="估值指标: PE, PB, PS")
    profitability: Dict[str, float] = Field(..., description="盈利能力: ROE, ROA, net_margin")
    growth: Dict[str, float] = Field(..., description="成长性: revenue_growth, profit_growth")
    financial_health: Dict[str, float] = Field(..., description="财务健康: debt_ratio, current_ratio")
    summary: str = Field(..., description="基本面分析总结")


class TechnicalAnalysis(BaseModel):
    score: float = Field(..., ge=0, le=10, description="技术面综合评分 (0-10)")
    trend: str = Field(..., description="趋势判断: 上涨/下跌/震荡")
    support_levels: List[float] = Field(default_factory=list, description="支撑位列表")
    resistance_levels: List[float] = Field(default_factory=list, description="压力位列表")
    indicators: Dict[str, Any] = Field(default_factory=dict, description="技术指标: MA, MACD, RSI, KDJ")
    summary: str = Field(..., description="技术面分析总结")


class CapitalFlowAnalysis(BaseModel):
    score: float = Field(..., ge=0, le=10, description="资金面综合评分 (0-10)")
    main_net_inflow: float = Field(..., description="主力资金净流入 (元)")
    main_inflow_ratio: float = Field(..., description="主力资金流入占比")
    trend: str = Field(..., description="资金流向趋势: 流入/流出/平衡")
    summary: str = Field(..., description="资金面分析总结")


class AnalysisReport(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    fundamental: FundamentalAnalysis = Field(..., description="基本面分析")
    technical: TechnicalAnalysis = Field(..., description="技术面分析")
    capital_flow: CapitalFlowAnalysis = Field(..., description="资金面分析")
    overall_score: float = Field(..., ge=0, le=10, description="综合评分 (0-10)")
    risk_level: str = Field(..., description="风险等级: low/medium/high")
    recommendation: str = Field(..., description="投资建议: buy/hold/watch/sell")
    summary: str = Field(..., description="综合分析总结")
    generated_at: int = Field(..., description="报告生成时间戳")


class AIAnalysisReport(BaseModel):
    """AI Agent 生成的分析报告"""
    overall_score: float = Field(..., ge=0, le=10, description="综合评分 (0-10)")
    risk_level: str = Field(..., description="风险等级: 低/中/高")
    recommendation: str = Field(..., description="投资建议: 买入/持有/观望/卖出")
    summary: str = Field(..., description="综合分析总结")

