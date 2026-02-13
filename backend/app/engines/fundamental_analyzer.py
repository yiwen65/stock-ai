# backend/app/engines/fundamental_analyzer.py

import numpy as np
from typing import Dict, List, Optional
from app.schemas.analysis import FundamentalAnalysis


class FundamentalAnalyzer:
    """基本面分析器 - 分析估值、盈利能力、成长性、财务健康"""

    async def analyze(self, stock_code: str) -> FundamentalAnalysis:
        """
        综合基本面分析

        Args:
            stock_code: 股票代码

        Returns:
            FundamentalAnalysis: 基本面分析结果
        """
        # 获取数据
        stock_data = await self._get_stock_data(stock_code)
        financials = await self._get_financials(stock_code)

        # 各维度分析
        valuation = await self.analyze_valuation(stock_data)
        profitability = await self.analyze_profitability(financials)
        growth = await self.analyze_growth(financials)
        health = await self.analyze_financial_health(financials[0] if financials else {})

        # 综合评分（加权平均）
        score = (
            valuation['score'] * 0.25 +
            profitability['score'] * 0.30 +
            growth['score'] * 0.25 +
            health['score'] * 0.20
        )

        # 生成总结
        summary = self._generate_summary(valuation, profitability, growth, health)

        return FundamentalAnalysis(
            score=round(score, 2),
            valuation=valuation,
            profitability=profitability,
            growth=growth,
            financial_health=health,
            summary=summary
        )

    async def analyze_valuation(self, stock_data: Dict) -> Dict[str, float]:
        """
        估值分析

        Args:
            stock_data: 股票数据（包含 PE, PB, PS 等）

        Returns:
            估值指标和评分
        """
        pe = stock_data.get('pe_ttm', 0)
        pb = stock_data.get('pb', 0)
        ps = stock_data.get('ps', 0)
        industry = stock_data.get('industry', '')

        # 获取行业平均 PE（TODO: 从数据库获取）
        industry_avg_pe = await self._get_industry_avg_pe(industry)

        # 计算估值评分
        valuation_score = self._calculate_valuation_score(
            pe, pb, ps, industry_avg_pe
        )

        # 计算 PE 百分位
        pe_percentile = self._calculate_percentile(pe, industry_avg_pe)

        return {
            'pe_ttm': pe,
            'pb': pb,
            'ps': ps,
            'industry_avg_pe': industry_avg_pe,
            'pe_percentile': pe_percentile,
            'score': valuation_score
        }

    async def analyze_profitability(self, financials: List[Dict]) -> Dict[str, float]:
        """
        盈利能力分析

        Args:
            financials: 财务数据列表（按时间倒序）

        Returns:
            盈利能力指标和评分
        """
        if not financials:
            return {
                'roe': 0,
                'roa': 0,
                'net_margin': 0,
                'gross_margin': 0,
                'roe_std': 0,
                'score': 0
            }

        latest = financials[0]

        roe = latest.get('roe', 0)
        roa = latest.get('roa', 0)
        net_margin = latest.get('net_margin', 0)
        gross_margin = latest.get('gross_margin', 0)

        # 计算 ROE 稳定性（过去 5 年标准差）
        roe_history = [f.get('roe', 0) for f in financials[:5]]
        roe_std = float(np.std(roe_history)) if len(roe_history) > 1 else 0

        # 计算盈利能力评分
        profitability_score = self._calculate_profitability_score(
            roe, roa, net_margin, roe_std
        )

        return {
            'roe': roe,
            'roa': roa,
            'net_margin': net_margin,
            'gross_margin': gross_margin,
            'roe_std': roe_std,
            'score': profitability_score
        }

    async def analyze_growth(self, financials: List[Dict]) -> Dict[str, float]:
        """
        成长性分析

        Args:
            financials: 财务数据列表（按时间倒序）

        Returns:
            成长性指标和评分
        """
        if len(financials) < 2:
            return {
                'revenue_growth_yoy': 0,
                'profit_growth_yoy': 0,
                'revenue_cagr_3y': 0,
                'score': 0
            }

        # 计算营收增长率（YoY）
        revenue_growth = self._calculate_yoy_growth(
            [f.get('revenue', 0) for f in financials[:2]]
        )

        # 计算净利润增长率（YoY）
        profit_growth = self._calculate_yoy_growth(
            [f.get('net_profit', 0) for f in financials[:2]]
        )

        # 计算 3 年复合增长率
        revenue_cagr = self._calculate_cagr(
            [f.get('revenue', 0) for f in financials[:4]]
        )

        # 计算成长性评分
        growth_score = self._calculate_growth_score(
            revenue_growth, profit_growth, revenue_cagr
        )

        return {
            'revenue_growth_yoy': revenue_growth,
            'profit_growth_yoy': profit_growth,
            'revenue_cagr_3y': revenue_cagr,
            'score': growth_score
        }

    async def analyze_financial_health(self, financials: Dict) -> Dict[str, float]:
        """
        财务健康分析

        Args:
            financials: 最新财务数据

        Returns:
            财务健康指标和评分
        """
        if not financials:
            return {
                'debt_ratio': 0,
                'current_ratio': 0,
                'operating_cash_flow': 0,
                'free_cash_flow': 0,
                'score': 0
            }

        debt_ratio = financials.get('debt_ratio', 0)
        current_ratio = financials.get('current_ratio', 0)
        operating_cash_flow = financials.get('operating_cash_flow', 0)
        free_cash_flow = financials.get('free_cash_flow', 0)

        # 计算财务健康评分
        health_score = self._calculate_health_score(
            debt_ratio, current_ratio, operating_cash_flow, free_cash_flow
        )

        return {
            'debt_ratio': debt_ratio,
            'current_ratio': current_ratio,
            'operating_cash_flow': operating_cash_flow,
            'free_cash_flow': free_cash_flow,
            'score': health_score
        }

    def _calculate_valuation_score(
        self,
        pe: float,
        pb: float,
        ps: float,
        industry_avg_pe: float
    ) -> float:
        """计算估值评分 (0-10)"""
        score = 5.0  # 基准分

        # PE 评分（相对行业平均）
        if industry_avg_pe > 0 and pe > 0:
            pe_ratio = pe / industry_avg_pe
            if pe_ratio < 0.7:
                score += 2.0  # 低估
            elif pe_ratio < 1.0:
                score += 1.0  # 合理偏低
            elif pe_ratio > 1.5:
                score -= 2.0  # 高估
            elif pe_ratio > 1.2:
                score -= 1.0  # 合理偏高

        # PB 评分
        if pb > 0:
            if pb < 1.0:
                score += 1.5
            elif pb < 2.0:
                score += 0.5
            elif pb > 5.0:
                score -= 1.5

        # PS 评分
        if ps > 0:
            if ps < 2.0:
                score += 0.5
            elif ps > 10.0:
                score -= 0.5

        return max(0, min(10, score))

    def _calculate_profitability_score(
        self,
        roe: float,
        roa: float,
        net_margin: float,
        roe_std: float
    ) -> float:
        """计算盈利能力评分 (0-10)"""
        score = 0.0

        # ROE 评分
        if roe >= 0.20:
            score += 4.0
        elif roe >= 0.15:
            score += 3.0
        elif roe >= 0.10:
            score += 2.0
        elif roe >= 0.05:
            score += 1.0

        # ROA 评分
        if roa >= 0.10:
            score += 2.0
        elif roa >= 0.05:
            score += 1.0

        # 净利率评分
        if net_margin >= 0.20:
            score += 2.0
        elif net_margin >= 0.10:
            score += 1.0

        # ROE 稳定性评分（标准差越小越好）
        if roe_std < 0.02:
            score += 2.0
        elif roe_std < 0.05:
            score += 1.0

        return min(10, score)

    def _calculate_growth_score(
        self,
        revenue_growth: float,
        profit_growth: float,
        revenue_cagr: float
    ) -> float:
        """计算成长性评分 (0-10)"""
        score = 0.0

        # 营收增长评分
        if revenue_growth >= 0.30:
            score += 3.0
        elif revenue_growth >= 0.20:
            score += 2.5
        elif revenue_growth >= 0.10:
            score += 2.0
        elif revenue_growth >= 0.05:
            score += 1.0

        # 利润增长评分
        if profit_growth >= 0.30:
            score += 3.0
        elif profit_growth >= 0.20:
            score += 2.5
        elif profit_growth >= 0.10:
            score += 2.0
        elif profit_growth >= 0.05:
            score += 1.0

        # CAGR 评分
        if revenue_cagr >= 0.25:
            score += 4.0
        elif revenue_cagr >= 0.15:
            score += 3.0
        elif revenue_cagr >= 0.10:
            score += 2.0
        elif revenue_cagr >= 0.05:
            score += 1.0

        return min(10, score)

    def _calculate_health_score(
        self,
        debt_ratio: float,
        current_ratio: float,
        operating_cash_flow: float,
        free_cash_flow: float
    ) -> float:
        """计算财务健康评分 (0-10)"""
        score = 0.0

        # 负债率评分（越低越好）
        if debt_ratio < 0.30:
            score += 3.0
        elif debt_ratio < 0.50:
            score += 2.0
        elif debt_ratio < 0.70:
            score += 1.0

        # 流动比率评分
        if current_ratio >= 2.0:
            score += 2.5
        elif current_ratio >= 1.5:
            score += 2.0
        elif current_ratio >= 1.0:
            score += 1.0

        # 经营现金流评分
        if operating_cash_flow > 0:
            score += 2.5

        # 自由现金流评分
        if free_cash_flow > 0:
            score += 2.0

        return min(10, score)

    def _calculate_yoy_growth(self, values: List[float]) -> float:
        """计算同比增长率"""
        if len(values) < 2 or values[1] == 0:
            return 0.0
        return (values[0] - values[1]) / values[1]

    def _calculate_cagr(self, values: List[float]) -> float:
        """计算复合年增长率"""
        if len(values) < 2 or values[-1] == 0:
            return 0.0
        n = len(values) - 1
        return (values[0] / values[-1]) ** (1 / n) - 1

    def _calculate_percentile(self, value: float, avg: float) -> float:
        """计算百分位（简化版）"""
        if avg == 0:
            return 50.0
        ratio = value / avg
        if ratio < 0.5:
            return 10.0
        elif ratio < 0.8:
            return 30.0
        elif ratio < 1.2:
            return 50.0
        elif ratio < 1.5:
            return 70.0
        else:
            return 90.0

    def _generate_summary(
        self,
        valuation: Dict,
        profitability: Dict,
        growth: Dict,
        health: Dict
    ) -> str:
        """生成基本面分析总结"""
        parts = []

        # 估值总结
        pe = valuation.get('pe_ttm', 0)
        if pe > 0:
            if valuation['score'] >= 7:
                parts.append("估值偏低")
            elif valuation['score'] >= 5:
                parts.append("估值合理")
            else:
                parts.append("估值偏高")

        # 盈利能力总结
        roe = profitability.get('roe', 0)
        if profitability['score'] >= 7:
            parts.append(f"盈利能力强（ROE {roe:.1%}）")
        elif profitability['score'] >= 5:
            parts.append("盈利能力中等")
        else:
            parts.append("盈利能力较弱")

        # 成长性总结
        revenue_growth = growth.get('revenue_growth_yoy', 0)
        if growth['score'] >= 7:
            parts.append(f"高成长（营收增长 {revenue_growth:.1%}）")
        elif growth['score'] >= 5:
            parts.append("稳定增长")
        else:
            parts.append("增长乏力")

        # 财务健康总结
        if health['score'] >= 7:
            parts.append("财务健康")
        elif health['score'] >= 5:
            parts.append("财务状况良好")
        else:
            parts.append("财务风险较高")

        return "，".join(parts)

    async def _get_stock_data(self, stock_code: str) -> Dict:
        """获取股票数据（TODO: 实现数据获取）"""
        return {
            'stock_code': stock_code,
            'pe_ttm': 15.0,
            'pb': 2.0,
            'ps': 3.0,
            'industry': '白酒'
        }

    async def _get_financials(self, stock_code: str) -> List[Dict]:
        """获取财务数据（TODO: 实现数据获取）"""
        return [
            {
                'roe': 0.18,
                'roa': 0.10,
                'net_margin': 0.15,
                'gross_margin': 0.45,
                'revenue': 100000000,
                'net_profit': 15000000,
                'debt_ratio': 0.40,
                'current_ratio': 1.8,
                'operating_cash_flow': 20000000,
                'free_cash_flow': 12000000
            }
        ]

    async def _get_industry_avg_pe(self, industry: str) -> float:
        """获取行业平均 PE（TODO: 实现数据获取）"""
        return 20.0
