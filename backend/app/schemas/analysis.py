# backend/app/schemas/analysis.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class DuPontAnalysis(BaseModel):
    """杜邦分析: ROE = 净利率 × 总资产周转率 × 权益乘数"""
    roe: float = Field(0, description="净资产收益率 (%)")
    net_profit_margin: float = Field(0, description="销售净利率 (%)")
    asset_turnover: float = Field(0, description="总资产周转率")
    equity_multiplier: float = Field(0, description="权益乘数")
    driver: str = Field("", description="ROE主驱动因子判断")


class FundamentalAnalysis(BaseModel):
    score: float = Field(..., ge=0, le=10, description="基本面综合评分 (0-10)")
    valuation: Dict[str, Any] = Field(..., description="估值指标: PE, PB, dcf 等")
    profitability: Dict[str, float] = Field(..., description="盈利能力: ROE, ROA, net_margin")
    growth: Dict[str, float] = Field(..., description="成长性: revenue_growth, profit_growth")
    financial_health: Dict[str, float] = Field(..., description="财务健康: debt_ratio, current_ratio")
    dupont: Optional[DuPontAnalysis] = Field(None, description="杜邦分析")
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
    main_net_inflow_5d: float = Field(0, description="近5日主力资金净流入 (元)")
    main_net_inflow_10d: float = Field(0, description="近10日主力资金净流入 (元)")
    super_large_net_inflow: float = Field(0, description="超大单净流入-今日 (元)")
    large_net_inflow: float = Field(0, description="大单净流入-今日 (元)")
    super_large_net_inflow_5d: float = Field(0, description="超大单净流入-近5日 (元)")
    large_net_inflow_5d: float = Field(0, description="大单净流入-近5日 (元)")
    super_large_net_inflow_10d: float = Field(0, description="超大单净流入-近10日 (元)")
    large_net_inflow_10d: float = Field(0, description="大单净流入-近10日 (元)")
    medium_net_inflow: float = Field(0, description="中单净流入-今日 (元)")
    small_net_inflow: float = Field(0, description="小单净流入-今日 (元)")
    main_inflow_ratio: float = Field(..., description="主力资金流入占比")
    trend: str = Field(..., description="资金流向趋势: 流入/流出/平衡")
    summary: str = Field(..., description="资金面分析总结")


class IndustryComparison(BaseModel):
    """同行业对比分析"""
    industry: str = Field("", description="所属行业")
    target: Optional[Dict[str, Any]] = Field(None, description="目标股票指标+排名")
    peers: List[Dict[str, Any]] = Field(default_factory=list, description="同行业对比公司列表")
    comparison_metrics: List[Dict[str, Any]] = Field(default_factory=list, description="各指标对比详情")
    industry_position: str = Field("", description="行业地位评估")


class AnalysisReport(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    fundamental: FundamentalAnalysis = Field(..., description="基本面分析")
    technical: TechnicalAnalysis = Field(..., description="技术面分析")
    capital_flow: CapitalFlowAnalysis = Field(..., description="资金面分析")
    industry_comparison: Optional[IndustryComparison] = Field(None, description="同行业对比分析")
    overall_score: float = Field(..., ge=0, le=10, description="综合评分 (0-10)")
    risk_level: str = Field(..., description="风险等级: low/medium/high")
    recommendation: str = Field(..., description="投资建议: buy/hold/watch/sell")
    confidence: str = Field("medium", description="置信度: high/medium/low")
    summary: str = Field(..., description="综合分析总结")
    generated_at: int = Field(..., description="报告生成时间戳")


class AIAnalysisReport(BaseModel):
    """AI Agent 生成的分析报告"""
    stock_code: str = Field("", description="股票代码")
    stock_name: str = Field("", description="股票名称")
    overall_score: float = Field(5.0, ge=0, le=10, description="综合评分 (0-10)")
    risk_level: str = Field("medium", description="风险等级: low/medium/high")
    recommendation: str = Field("watch", description="投资建议: buy/hold/watch/sell")
    confidence: str = Field("medium", description="置信度: high/medium/low")
    position_pct: Optional[int] = Field(None, description="建议仓位比例 0-100")
    buy_range: Optional[List[float]] = Field(None, description="建议买入价区间")
    stop_loss: Optional[float] = Field(None, description="建议止损价")
    target_price: Optional[float] = Field(None, description="建议目标价")
    reasons: List[str] = Field(default_factory=list, description="核心投资逻辑")
    summary: str = Field("", description="综合分析总结")
    fundamental: Optional[Dict[str, Any]] = Field(None, description="基本面分析结果")
    technical: Optional[Dict[str, Any]] = Field(None, description="技术面分析结果")
    capital_flow: Optional[Dict[str, Any]] = Field(None, description="资金面分析结果")
    news: Optional[Dict[str, Any]] = Field(None, description="消息面分析结果")
    analysis_time: Optional[float] = Field(None, description="分析耗时(秒)")

