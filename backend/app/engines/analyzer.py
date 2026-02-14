# backend/app/engines/analyzer.py

import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from redis import Redis
import pandas as pd
import numpy as np

from app.schemas.analysis import (
    AnalysisReport,
    FundamentalAnalysis,
    TechnicalAnalysis,
    CapitalFlowAnalysis,
    IndustryComparison,
    DuPontAnalysis
)
from app.services.data_service import DataService
from app.engines.industry_comparator import IndustryComparator
from app.utils.indicators import (
    calculate_ma, calculate_macd, calculate_rsi, calculate_kdj,
    calculate_boll, calculate_volume_ma, detect_ma_alignment, detect_macd_cross
)

logger = logging.getLogger(__name__)


class StockAnalyzer:
    """股票分析引擎 - 协调基本面、技术面、资金面分析"""

    # PRD 4.7.1 五维权重
    WEIGHT_FUNDAMENTAL = 0.35
    WEIGHT_TECHNICAL = 0.25
    WEIGHT_CAPITAL = 0.20
    WEIGHT_VALUATION = 0.15
    WEIGHT_NEWS = 0.05

    def __init__(self, db: Session, cache: Redis):
        self.db = db
        self.cache = cache
        self.data_service = DataService()
        self.industry_comparator = IndustryComparator(self.data_service)

    async def analyze(
        self,
        stock_code: str,
        report_type: str = 'comprehensive',
        force_refresh: bool = False
    ) -> AnalysisReport:
        """生成股票分析报告"""
        # 1. 检查缓存
        cache_key = f"analysis:report:{stock_code}"
        if not force_refresh:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return AnalysisReport(**cached)

        # 2. 获取分析所需数据 (并发获取，含新闻)
        data = await self._fetch_analysis_data(stock_code)

        if not data.get('quote'):
            raise ValueError(f"无法获取股票 {stock_code} 的行情数据")

        # 3. 执行各维度分析 (并发执行)
        fundamental, technical, capital_flow, industry_data = await asyncio.gather(
            self._analyze_fundamental(data),
            self._analyze_technical(data),
            self._analyze_capital_flow(data),
            self.industry_comparator.compare(stock_code),
        )

        # Handle industry comparison exception
        if isinstance(industry_data, Exception):
            logger.error(f"Industry comparison failed for {stock_code}: {industry_data}")
            industry_data = None

        industry_comparison = None
        if industry_data and industry_data.get("target"):
            industry_comparison = IndustryComparison(**industry_data)

        # 4. 计算综合评分（PRD 5维）
        valuation_score = self._score_valuation(
            fundamental.valuation.get('pe', 0),
            fundamental.valuation.get('pb', 0),
        )
        news_score = self._score_news(data.get('news', []))
        overall_score = self._calculate_overall_score(
            fundamental, technical, capital_flow, valuation_score, news_score
        )

        # 4b. 置信度：维度离散度 + 数据可用性
        dim_scores = [fundamental.score, technical.score, capital_flow.score, valuation_score, news_score]
        mean_s = sum(dim_scores) / len(dim_scores)
        std_s = (sum((s - mean_s) ** 2 for s in dim_scores) / len(dim_scores)) ** 0.5
        # Data availability: more data sources = higher confidence
        data_avail = sum([
            1 if data.get('financials') else 0,
            1 if len(data.get('kline_data', [])) > 60 else 0,
            1 if data.get('capital_flow') else 0,
            1 if data.get('news') else 0,
            1 if data.get('quote') else 0,
        ])
        if data_avail >= 4 and std_s < 1.5:
            confidence = "high"
        elif data_avail >= 3 and std_s < 2.5:
            confidence = "medium"
        else:
            confidence = "low"

        # 5. 生成报告
        report = AnalysisReport(
            stock_code=stock_code,
            stock_name=data.get('stock_name', stock_code),
            fundamental=fundamental,
            technical=technical,
            capital_flow=capital_flow,
            industry_comparison=industry_comparison,
            overall_score=overall_score,
            risk_level=self._assess_risk(overall_score, data),
            recommendation=self._generate_recommendation(overall_score),
            confidence=confidence,
            summary=self._generate_summary(fundamental, technical, capital_flow, overall_score),
            generated_at=int(time.time())
        )

        # 6. 缓存结果 (TTL: 1小时)
        await self._set_to_cache(cache_key, report.model_dump(), ttl=3600)

        return report

    async def _fetch_analysis_data(self, stock_code: str) -> Dict[str, Any]:
        """获取分析所需的所有数据（并发，含新闻）"""
        quote_task = self.data_service.fetch_realtime_quote(stock_code)
        kline_task = self.data_service.fetch_kline_data(stock_code, period='1d', days=500)
        financial_task = self.data_service.fetch_financial_data(stock_code, years=5)
        capital_task = self.data_service.fetch_capital_flow(stock_code)
        news_task = self.data_service.fetch_stock_news(stock_code, limit=20)
        valuation_task = self.data_service.fetch_valuation_history(stock_code)

        quote, kline_data, financials, capital_flow, news, valuation_hist = await asyncio.gather(
            quote_task, kline_task, financial_task, capital_task, news_task, valuation_task,
            return_exceptions=True
        )

        # Handle exceptions gracefully
        if isinstance(quote, Exception):
            logger.error(f"Failed to fetch quote for {stock_code}: {quote}")
            quote = None
        if isinstance(kline_data, Exception):
            logger.error(f"Failed to fetch kline for {stock_code}: {kline_data}")
            kline_data = []
        if isinstance(financials, Exception):
            logger.error(f"Failed to fetch financials for {stock_code}: {financials}")
            financials = []
        if isinstance(capital_flow, Exception):
            logger.error(f"Failed to fetch capital flow for {stock_code}: {capital_flow}")
            capital_flow = None
        if isinstance(news, Exception):
            logger.error(f"Failed to fetch news for {stock_code}: {news}")
            news = []
        if isinstance(valuation_hist, Exception):
            logger.warning(f"Failed to fetch valuation history for {stock_code}: {valuation_hist}")
            valuation_hist = None

        return {
            'stock_code': stock_code,
            'stock_name': quote.get('stock_name', stock_code) if quote else stock_code,
            'quote': quote,
            'kline_data': kline_data or [],
            'financials': financials or [],
            'capital_flow': capital_flow,
            'news': news or [],
            'valuation_hist': valuation_hist,
        }

    async def _analyze_fundamental(self, data: Dict) -> FundamentalAnalysis:
        """基本面分析 — Piotroski-inspired multi-quarter quality assessment

        Best-practice enhancements:
        1. Multi-quarter trend detection (ROE/margin improving or deteriorating)
        2. Piotroski-style quality signals (positive ROE, margin stability, deleveraging)
        3. Gross margin & net margin factored into profitability scoring
        4. Revenue-profit growth consistency check
        5. Financial trend bonus/penalty from historical comparison
        """
        quote = data.get('quote', {})
        financials = data.get('financials', [])

        # Extract valuation from quote
        pe = quote.get('pe', 0) if quote else 0
        pb = quote.get('pb', 0) if quote else 0
        market_cap = quote.get('market_cap', 0) if quote else 0

        # Extract latest financial metrics
        roe = 0
        debt_ratio = 0
        current_ratio = 0
        revenue_growth = 0
        net_profit_growth = 0
        eps = 0
        gross_margin = 0
        net_margin = 0

        if financials and len(financials) > 0:
            latest = financials[-1]  # most recent record (list is chronological)
            roe = latest.get('roe', 0) or 0
            debt_ratio = latest.get('debt_ratio', 0) or 0
            current_ratio = latest.get('current_ratio', 0) or 0
            revenue_growth = latest.get('revenue_growth', 0) or 0
            net_profit_growth = latest.get('net_profit_growth', 0) or 0
            eps = latest.get('eps', 0) or 0
            gross_margin = latest.get('gross_margin', 0) or 0
            net_margin = latest.get('net_margin', 0) or 0

        # ── Piotroski-style quality signals (0-9 scale, mapped to bonus) ──
        # Inspired by Piotroski F-Score: academic gold-standard for fundamental quality
        piotroski_signals = self._compute_piotroski_signals(financials)

        # ── Multi-quarter trend detection ──
        trend_bonus = self._compute_financial_trend(financials)

        # ── Valuation percentile from real historical PE/PB data ──
        pe_percentile = None
        pb_percentile = None
        valuation_hist = data.get('valuation_hist')
        if valuation_hist:
            pe_percentile = valuation_hist.get('pe_percentile')
            pb_percentile = valuation_hist.get('pb_percentile')

        # ── DuPont Analysis ──
        dupont = None
        if roe != 0 and net_margin != 0 and debt_ratio < 100:
            equity_multiplier = round(1.0 / (1.0 - debt_ratio / 100.0), 2) if debt_ratio < 100 else 0
            asset_turnover = round(roe / (net_margin * equity_multiplier), 2) if (net_margin * equity_multiplier) != 0 else 0
            drivers = {
                '盈利能力驱动': abs(net_margin),
                '运营效率驱动': abs(asset_turnover),
                '杠杆驱动': abs(equity_multiplier - 1),
            }
            driver = max(drivers, key=drivers.get) if drivers else '均衡型'
            dupont = DuPontAnalysis(
                roe=round(roe, 2),
                net_profit_margin=round(net_margin, 2),
                asset_turnover=asset_turnover,
                equity_multiplier=equity_multiplier,
                driver=driver
            )

        # ── DCF (two-stage) ──
        dcf_result = self._calculate_dcf(eps, net_profit_growth, roe)

        # ── Dimension sub-scores ──
        valuation_score = self._score_valuation(pe, pb)  # summary text only
        profitability_score = self._score_profitability(roe, eps, gross_margin, net_margin)
        growth_score = self._score_growth(revenue_growth, net_profit_growth)
        health_score = self._score_financial_health(debt_ratio, current_ratio)

        # ── Weighted fundamental score (0-10) ──
        # Valuation is a separate overall dimension to avoid double-counting.
        raw_score = (
            profitability_score * 0.35 +
            growth_score * 0.30 +
            health_score * 0.20 +
            piotroski_signals * 0.15
        )
        # Apply multi-quarter trend bonus/penalty (±0.8 max)
        raw_score += trend_bonus
        score = round(max(0, min(10, raw_score)), 1)

        # ── Generate summary ──
        parts = []
        if valuation_score >= 7:
            parts.append("估值合理偏低")
        elif valuation_score >= 5:
            parts.append("估值合理")
        else:
            parts.append("估值偏高")

        if profitability_score >= 7:
            parts.append("盈利能力强")
        elif profitability_score >= 5:
            parts.append("盈利能力一般")
        else:
            parts.append("盈利能力较弱")

        if growth_score >= 7:
            parts.append("成长性良好")
        elif growth_score >= 5:
            parts.append("成长性一般")
        else:
            parts.append("成长性不足")

        if trend_bonus > 0.3:
            parts.append("财务趋势改善")
        elif trend_bonus < -0.3:
            parts.append("财务趋势恶化")

        summary = "，".join(parts) + f"。基本面评分{score}分。"

        return FundamentalAnalysis(
            score=score,
            valuation={
                'pe': pe, 'pb': pb, 'market_cap': market_cap,
                **(({'pe_percentile': pe_percentile} if pe_percentile is not None else {})),
                **(({'pb_percentile': pb_percentile} if pb_percentile is not None else {})),
                **(({'dcf': dcf_result} if dcf_result else {})),
            },
            profitability={'roe': roe, 'eps': eps, 'gross_margin': gross_margin, 'net_margin': net_margin},
            growth={'revenue_growth': revenue_growth, 'profit_growth': net_profit_growth},
            financial_health={'debt_ratio': debt_ratio, 'current_ratio': current_ratio},
            dupont=dupont,
            summary=summary
        )

    def _score_valuation(self, pe: float, pb: float) -> float:
        """估值评分 (0-10)"""
        score = 5.0
        if pe > 0:
            if pe < 10:
                score += 3.0
            elif pe < 15:
                score += 2.0
            elif pe < 25:
                score += 1.0
            elif pe < 40:
                score -= 1.0
            else:
                score -= 2.0

        if pb > 0:
            if pb < 1:
                score += 2.0
            elif pb < 2:
                score += 1.0
            elif pb < 5:
                pass
            else:
                score -= 1.0

        return max(0, min(10, score))

    def _score_profitability(self, roe: float, eps: float,
                              gross_margin: float = 0, net_margin: float = 0) -> float:
        """盈利能力评分 (0-10)
        Best practice: ROE is the primary metric (Buffett/Munger standard).
        Supplement with margin analysis for quality of earnings.
        """
        score = 5.0

        # ROE: primary profitability indicator (±3.0)
        if roe > 20:
            score += 3.0
        elif roe > 15:
            score += 2.0
        elif roe > 10:
            score += 1.0
        elif roe > 5:
            pass
        elif roe > 0:
            score -= 1.0
        else:
            score -= 3.0

        # EPS positivity (±0.5)
        if eps > 0:
            score += 0.5
        else:
            score -= 0.5

        # Gross margin quality (±1.0) — high margins indicate pricing power
        if gross_margin > 60:
            score += 1.0
        elif gross_margin > 40:
            score += 0.5
        elif gross_margin > 20:
            pass
        elif gross_margin > 0:
            score -= 0.5
        # gross_margin == 0 means data missing, no penalty

        # Net margin efficiency (±0.5)
        if net_margin > 20:
            score += 0.5
        elif net_margin < 0:
            score -= 0.5

        return max(0, min(10, score))

    def _score_growth(self, revenue_growth: float, profit_growth: float) -> float:
        """成长性评分 (0-10)
        Best practice: profit growth is primary; revenue-profit consistency
        check detects unsustainable growth (profit growing without revenue = accounting tricks).
        """
        score = 5.0

        # Net profit growth (±3.0)
        if profit_growth > 30:
            score += 3.0
        elif profit_growth > 15:
            score += 2.0
        elif profit_growth > 5:
            score += 1.0
        elif profit_growth > 0:
            pass
        elif profit_growth > -10:
            score -= 1.0
        else:
            score -= 3.0

        # Revenue growth (±1.5)
        if revenue_growth > 20:
            score += 1.5
        elif revenue_growth > 10:
            score += 1.0
        elif revenue_growth > 0:
            score += 0.5
        else:
            score -= 1.0

        # Revenue-profit consistency check (±0.5)
        # If profit grows >20% but revenue shrinks, earnings quality is suspect
        if profit_growth > 20 and revenue_growth < 0:
            score -= 0.5  # unsustainable: profit via cost-cutting, not real growth
        elif revenue_growth > 10 and profit_growth > 10:
            score += 0.5  # healthy: both revenue and profit growing together

        return max(0, min(10, score))

    def _score_financial_health(self, debt_ratio: float, current_ratio: float) -> float:
        """财务健康评分 (0-10)"""
        score = 5.0
        if debt_ratio < 30:
            score += 3.0
        elif debt_ratio < 50:
            score += 1.5
        elif debt_ratio < 65:
            pass
        elif debt_ratio < 80:
            score -= 1.5
        else:
            score -= 3.0

        if current_ratio > 2:
            score += 1.5
        elif current_ratio > 1.5:
            score += 1.0
        elif current_ratio > 1:
            pass
        else:
            score -= 1.5

        return max(0, min(10, score))

    def _compute_piotroski_signals(self, financials: List[Dict]) -> float:
        """Piotroski F-Score inspired quality assessment (mapped to 0-10).

        Original F-Score uses 9 binary signals across profitability, leverage,
        and operating efficiency.  We adapt for available A-share quarterly data.

        Signals checked (1 point each, max 9 → mapped to 0-10):
        1. ROE > 0  (positive return)
        2. EPS > 0  (positive earnings)
        3. Gross margin > 20%  (decent margins)
        4. Net margin > 0  (not loss-making)
        5. Current ratio > 1  (short-term solvency)
        6. Debt ratio < 70%  (reasonable leverage)
        7. ROE improved vs prior period
        8. Gross margin improved vs prior period
        9. Debt ratio decreased vs prior period
        """
        if not financials:
            return 5.0  # neutral when no data

        latest = financials[-1]
        signals = 0

        # Static quality signals (latest quarter)
        if (latest.get('roe', 0) or 0) > 0:
            signals += 1
        if (latest.get('eps', 0) or 0) > 0:
            signals += 1
        if (latest.get('gross_margin', 0) or 0) > 20:
            signals += 1
        if (latest.get('net_margin', 0) or 0) > 0:
            signals += 1
        if (latest.get('current_ratio', 0) or 0) > 1:
            signals += 1
        if (latest.get('debt_ratio', 0) or 0) < 70:
            signals += 1

        # Trend signals (compare latest vs prior period)
        if len(financials) >= 2:
            prior = financials[-2]
            if (latest.get('roe', 0) or 0) > (prior.get('roe', 0) or 0):
                signals += 1
            if (latest.get('gross_margin', 0) or 0) > (prior.get('gross_margin', 0) or 0):
                signals += 1
            if (latest.get('debt_ratio', 100) or 100) < (prior.get('debt_ratio', 100) or 100):
                signals += 1
        else:
            # No prior data → assume neutral for trend signals
            signals += 1  # give 1 of 3 trend points as neutral

        # Map 0-9 signals to 0-10 score
        return round(signals / 9.0 * 10.0, 1)

    def _compute_financial_trend(self, financials: List[Dict]) -> float:
        """Multi-quarter financial trend analysis.

        Best practice: compare last 4 quarters to detect improving or
        deteriorating fundamentals.  Returns a bonus/penalty in [-0.8, +0.8].

        Checks:
        - ROE trend (improving / stable / declining)
        - Margin stability (gross margin coefficient of variation)
        - Growth acceleration/deceleration
        """
        if not financials or len(financials) < 3:
            return 0.0  # insufficient data

        # Use last 4 quarters (or whatever is available)
        recent = financials[-4:] if len(financials) >= 4 else financials

        bonus = 0.0

        # 1. ROE trend: linear regression direction
        roe_vals = [(f.get('roe', 0) or 0) for f in recent]
        if len(roe_vals) >= 3:
            roe_first_half = sum(roe_vals[:len(roe_vals)//2]) / max(len(roe_vals)//2, 1)
            roe_second_half = sum(roe_vals[len(roe_vals)//2:]) / max(len(roe_vals) - len(roe_vals)//2, 1)
            if roe_second_half > roe_first_half + 1:
                bonus += 0.3  # ROE improving
            elif roe_second_half < roe_first_half - 1:
                bonus -= 0.3  # ROE declining

        # 2. Gross margin stability: low CV = stable pricing power
        gm_vals = [(f.get('gross_margin', 0) or 0) for f in recent if (f.get('gross_margin', 0) or 0) > 0]
        if len(gm_vals) >= 3:
            gm_mean = sum(gm_vals) / len(gm_vals)
            if gm_mean > 0:
                gm_std = (sum((g - gm_mean) ** 2 for g in gm_vals) / len(gm_vals)) ** 0.5
                cv = gm_std / gm_mean
                if cv < 0.05:
                    bonus += 0.3  # very stable margins
                elif cv > 0.20:
                    bonus -= 0.3  # highly volatile margins

        # 3. Growth acceleration
        growth_vals = [(f.get('net_profit_growth', 0) or 0) for f in recent]
        if len(growth_vals) >= 3:
            recent_growth = growth_vals[-1]
            earlier_growth = growth_vals[0]
            if recent_growth > earlier_growth + 5:
                bonus += 0.2  # growth accelerating
            elif recent_growth < earlier_growth - 10:
                bonus -= 0.2  # growth decelerating sharply

        return max(-0.8, min(0.8, round(bonus, 2)))

    def _calculate_dcf(self, eps: float, growth_rate: float, roe: float) -> Optional[Dict]:
        """简化 DCF 两阶段模型 (PRD §4.2.4)
        Stage 1: 5年高增长期，用当前增长率（衰减）
        Stage 2: 永续期，增长率3%
        折现率10%
        """
        if eps <= 0 or growth_rate is None:
            return None

        discount_rate = 0.10
        terminal_growth = 0.03
        stage1_years = 5

        # Cap growth rate to reasonable range
        g = max(-0.05, min(growth_rate / 100.0, 0.50))

        # Stage 1: project EPS with decaying growth
        projected_eps = []
        current_eps = eps
        for yr in range(1, stage1_years + 1):
            yr_growth = g * (1 - 0.1 * (yr - 1))  # decay 10% per year
            current_eps = current_eps * (1 + yr_growth)
            projected_eps.append(current_eps)

        # PV of Stage 1 cash flows
        pv_stage1 = sum(
            e / (1 + discount_rate) ** (i + 1)
            for i, e in enumerate(projected_eps)
        )

        # Stage 2: terminal value using Gordon Growth
        terminal_eps = projected_eps[-1] * (1 + terminal_growth)
        if discount_rate <= terminal_growth:
            return None
        terminal_value = terminal_eps / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / (1 + discount_rate) ** stage1_years

        intrinsic_value = round(pv_stage1 + pv_terminal, 2)

        # Safety margin scenarios
        return {
            'intrinsic_value': intrinsic_value,
            'margin_of_safety_20': round(intrinsic_value * 0.80, 2),
            'margin_of_safety_30': round(intrinsic_value * 0.70, 2),
            'discount_rate': discount_rate,
            'terminal_growth': terminal_growth,
            'stage1_years': stage1_years,
        }

    async def _analyze_technical(self, data: Dict) -> TechnicalAnalysis:
        """技术面分析 — multi-indicator confluence scoring

        Best-practice enhancements:
        1. ADX for trend strength measurement (not just direction)
        2. RSI-price divergence detection (leading reversal signal)
        3. Signal confluence bonus (aligned signals > individual signals)
        4. Bollinger Band width for volatility regime detection
        5. Volume-price relationship in both directions
        """
        from app.utils.indicators import calculate_atr, calculate_adx

        kline_data = data.get('kline_data', [])
        quote = data.get('quote', {})

        if not kline_data or len(kline_data) < 20:
            return TechnicalAnalysis(
                score=5.0, trend="数据不足", support_levels=[],
                resistance_levels=[], indicators={},
                summary="K线数据不足，无法进行技术分析"
            )

        df = pd.DataFrame(kline_data)
        closes = df['close'].astype(float)
        highs = df['high'].astype(float)
        lows = df['low'].astype(float)
        volumes = df['volume'].astype(float)

        # ── Compute all indicators ──
        alignment = detect_ma_alignment(closes)
        ma_data = calculate_ma(closes, [5, 10, 20, 60])
        ma_latest = {k: round(float(v.iloc[-1]), 2) for k, v in ma_data.items() if not np.isnan(v.iloc[-1])}

        macd_cross = detect_macd_cross(closes)

        rsi_data = calculate_rsi(closes, [6, 14])
        rsi14 = float(rsi_data['rsi14'].iloc[-1]) if not np.isnan(rsi_data['rsi14'].iloc[-1]) else 50

        kdj_data = calculate_kdj(highs, lows, closes)
        k_val = float(kdj_data['k'].iloc[-1]) if not np.isnan(kdj_data['k'].iloc[-1]) else 50
        d_val = float(kdj_data['d'].iloc[-1]) if not np.isnan(kdj_data['d'].iloc[-1]) else 50
        j_val = float(kdj_data['j'].iloc[-1]) if not np.isnan(kdj_data['j'].iloc[-1]) else 50

        boll = calculate_boll(closes)
        current_price = float(closes.iloc[-1])
        boll_upper = float(boll['upper'].iloc[-1]) if not np.isnan(boll['upper'].iloc[-1]) else current_price
        boll_mid = float(boll['mid'].iloc[-1]) if not np.isnan(boll['mid'].iloc[-1]) else current_price
        boll_lower = float(boll['lower'].iloc[-1]) if not np.isnan(boll['lower'].iloc[-1]) else current_price

        # ADX: trend strength (0-100, >25 = trending, <20 = ranging)
        adx_data = calculate_adx(highs, lows, closes)
        adx_val = float(adx_data['adx'].iloc[-1]) if not np.isnan(adx_data['adx'].iloc[-1]) else 20
        plus_di = float(adx_data['plus_di'].iloc[-1]) if not np.isnan(adx_data['plus_di'].iloc[-1]) else 0
        minus_di = float(adx_data['minus_di'].iloc[-1]) if not np.isnan(adx_data['minus_di'].iloc[-1]) else 0

        vol_ma = calculate_volume_ma(volumes, [5, 20])
        vol_ratio = 1.0
        if 'vol_ma5' in vol_ma and 'vol_ma20' in vol_ma:
            recent_vol = float(vol_ma['vol_ma5'].iloc[-1])
            avg_vol = float(vol_ma['vol_ma20'].iloc[-1])
            if avg_vol > 0:
                vol_ratio = recent_vol / avg_vol

        # ── Trend determination (enhanced with ADX) ──
        trend = "震荡"
        if alignment['bullish']:
            trend = "强势上涨" if adx_val > 25 else "弱势上涨"
        elif alignment.get('bearish'):
            trend = "强势下跌" if adx_val > 25 else "弱势下跌"
        elif 'ma5' in ma_latest and 'ma20' in ma_latest:
            if ma_latest['ma5'] > ma_latest['ma20']:
                trend = "弱势上涨"
            else:
                trend = "弱势下跌"

        # ── RSI-price divergence detection (leading reversal signal) ──
        bullish_divergence = False
        bearish_divergence = False
        if len(closes) >= 30 and len(rsi_data['rsi14']) >= 30:
            rsi_series = rsi_data['rsi14']
            # Check last 20 bars for divergence
            price_20 = closes.iloc[-20:]
            rsi_20 = rsi_series.iloc[-20:]
            price_low_idx = price_20.idxmin()
            rsi_at_price_low = rsi_20.loc[price_low_idx] if price_low_idx in rsi_20.index else None
            # Bullish: price makes new low but RSI doesn't
            if (rsi_at_price_low is not None and not np.isnan(rsi_at_price_low)
                    and current_price <= price_20.quantile(0.15)
                    and rsi14 > rsi_at_price_low + 3):
                bullish_divergence = True
            # Bearish: price makes new high but RSI doesn't
            price_high_idx = price_20.idxmax()
            rsi_at_price_high = rsi_20.loc[price_high_idx] if price_high_idx in rsi_20.index else None
            if (rsi_at_price_high is not None and not np.isnan(rsi_at_price_high)
                    and current_price >= price_20.quantile(0.85)
                    and rsi14 < rsi_at_price_high - 3):
                bearish_divergence = True

        # ── Support / Resistance ──
        support_levels = self._find_support_levels(
            closes, lows, current_price, ma_latest, boll_lower=boll_lower, volumes=volumes)
        resistance_levels = self._find_resistance_levels(
            closes, highs, current_price, ma_latest, boll_upper=boll_upper, volumes=volumes)

        # ══════════════════════════════════════════════════════════════
        # Technical score (0-10) — signal-by-signal with confluence bonus
        # ══════════════════════════════════════════════════════════════
        bullish_signals = 0
        bearish_signals = 0
        tech_score = 5.0

        # 1. MA alignment (±1.5)
        if alignment['bullish']:
            tech_score += 1.5; bullish_signals += 1
        elif alignment.get('bearish'):
            tech_score -= 1.5; bearish_signals += 1

        # 2. ADX trend strength modifier (±0.5)
        # Strong trend (ADX>25) amplifies existing direction
        if adx_val > 25:
            if plus_di > minus_di:
                tech_score += 0.5; bullish_signals += 1
            else:
                tech_score -= 0.5; bearish_signals += 1

        # 3. MACD (±1.0)
        if macd_cross['golden_cross']:
            tech_score += 1.0; bullish_signals += 1
        elif macd_cross['death_cross']:
            tech_score -= 1.0; bearish_signals += 1
        elif macd_cross['dif'] > macd_cross['dea']:
            tech_score += 0.3

        # 4. RSI (±0.8)
        if rsi14 <= 30:
            tech_score += 0.8; bullish_signals += 1
        elif rsi14 >= 70:
            tech_score -= 0.5; bearish_signals += 1
        elif 40 < rsi14 < 60:
            tech_score += 0.3  # healthy neutral zone

        # 5. KDJ (±0.5)
        if k_val > d_val and k_val < 80:
            tech_score += 0.5; bullish_signals += 1
        elif k_val < d_val and k_val > 20:
            tech_score -= 0.5; bearish_signals += 1

        # 6. Bollinger Band position (±0.5)
        if current_price < boll_lower:
            tech_score += 0.5; bullish_signals += 1
        elif current_price > boll_upper:
            tech_score -= 0.5; bearish_signals += 1

        # 7. RSI-price divergence (±0.8) — high-value leading signal
        if bullish_divergence:
            tech_score += 0.8; bullish_signals += 1
        if bearish_divergence:
            tech_score -= 0.8; bearish_signals += 1

        # 8. Volume-price relationship (±0.8)
        if vol_ratio > 1.3 and trend in ["强势上涨", "弱势上涨"]:
            tech_score += 0.8; bullish_signals += 1
        elif vol_ratio > 1.5 and trend in ["强势下跌", "弱势下跌"]:
            tech_score -= 0.5; bearish_signals += 1
        elif vol_ratio < 0.6 and trend in ["强势上涨", "弱势上涨"]:
            tech_score -= 0.3  # low-volume rally is suspect

        # 9. Signal confluence bonus (±0.5)
        # When ≥3 indicators agree, conviction is much higher
        if bullish_signals >= 3:
            tech_score += 0.5
        elif bearish_signals >= 3:
            tech_score -= 0.5

        tech_score = round(max(0, min(10, tech_score)), 1)

        # ── Summary ──
        signals = []
        if alignment['bullish']:
            signals.append("均线多头排列")
        elif alignment.get('bearish'):
            signals.append("均线空头排列")
        if macd_cross['golden_cross']:
            signals.append("MACD金叉")
        elif macd_cross['death_cross']:
            signals.append("MACD死叉")
        if rsi14 < 30:
            signals.append("RSI超卖")
        elif rsi14 > 70:
            signals.append("RSI超买")
        if k_val > d_val and k_val < 80:
            signals.append("KDJ金叉")
        if bullish_divergence:
            signals.append("底背离")
        if bearish_divergence:
            signals.append("顶背离")
        if adx_val > 25:
            signals.append(f"趋势强(ADX={adx_val:.0f})")

        signal_text = "、".join(signals) if signals else "无明显信号"
        summary = f"当前趋势：{trend}。技术信号：{signal_text}。RSI={rsi14:.0f}。技术评分{tech_score}分。"

        indicators = {
            **ma_latest,
            'rsi14': round(rsi14, 1),
            'macd_dif': round(macd_cross['dif'], 3),
            'macd_dea': round(macd_cross['dea'], 3),
            'kdj_k': round(k_val, 1),
            'kdj_d': round(d_val, 1),
            'kdj_j': round(j_val, 1),
            'boll_upper': round(boll_upper, 2),
            'boll_mid': round(boll_mid, 2),
            'boll_lower': round(boll_lower, 2),
            'adx': round(adx_val, 1),
            'vol_ratio': round(vol_ratio, 2),
        }

        return TechnicalAnalysis(
            score=tech_score,
            trend=trend,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            indicators=indicators,
            summary=summary
        )

    @staticmethod
    def _detect_swing_points(series: pd.Series, order: int = 5) -> List[float]:
        """Detect swing highs or swing lows (local extrema).

        A swing low at index i means series[i] is the minimum within
        [i-order, i+order].  These are actual reversal points where price
        bounced, not random single-bar extremes.
        """
        points = []
        values = series.values
        n = len(values)
        for i in range(order, n - order):
            window = values[i - order: i + order + 1]
            if values[i] == window.min():
                points.append(float(values[i]))
            elif values[i] == window.max():
                points.append(float(values[i]))
        return points

    @staticmethod
    def _cluster_levels(raw_levels: List[float], threshold_pct: float = 0.015) -> List[float]:
        """Cluster nearby price levels into zones.

        Prices within threshold_pct of each other are merged into their
        average.  This turns many individual points into meaningful
        support/resistance *zones*.
        """
        if not raw_levels:
            return []
        sorted_vals = sorted(raw_levels)
        clusters: List[List[float]] = [[sorted_vals[0]]]
        for val in sorted_vals[1:]:
            if abs(val - clusters[-1][-1]) / max(clusters[-1][-1], 1e-9) < threshold_pct:
                clusters[-1].append(val)
            else:
                clusters.append([val])
        # Return average of each cluster, weighted by count (more touches = stronger)
        return [round(sum(c) / len(c), 2) for c in clusters]

    def _find_support_levels(self, closes, lows, current_price, ma_latest,
                             boll_lower: float = None, volumes=None) -> List[float]:
        """Find key support levels using multi-method best practices.

        Methods combined:
        1. Swing lows (actual reversal points from recent 120 bars)
        2. Price clustering (zones with multiple touches)
        3. MA dynamic support (MA20/MA60 below current price)
        4. Bollinger lower band
        5. Psychological round-number levels
        Ordered nearest-first (closest support is most actionable).
        """
        candidates: List[float] = []

        # 1. Swing lows from recent 120 bars (actual reversal points)
        lookback = min(120, len(lows))
        if lookback >= 15:
            swing_lows = []
            vals = lows.tail(lookback).values
            for i in range(5, lookback - 5):
                window = vals[i - 5: i + 6]
                if vals[i] == window.min():
                    swing_lows.append(float(vals[i]))
            # Cluster nearby swing lows into zones
            zones = self._cluster_levels(swing_lows)
            for z in zones:
                if z < current_price * 0.995:  # at least 0.5% below
                    candidates.append(z)

        # 2. MA dynamic support
        for key in ['ma20', 'ma60', 'ma10']:
            if key in ma_latest and ma_latest[key] < current_price * 0.998:
                candidates.append(round(ma_latest[key], 2))

        # 3. Bollinger lower band
        if boll_lower is not None and boll_lower < current_price * 0.998:
            candidates.append(round(boll_lower, 2))

        # 4. Psychological round-number levels (整数关口)
        # Find the nearest round numbers below current price
        if current_price > 10:
            step = 10 if current_price > 50 else 5
            nearest_round = int(current_price / step) * step
            if nearest_round < current_price * 0.998:
                candidates.append(float(nearest_round))

        # Deduplicate (cluster levels within 1%)
        if candidates:
            candidates = self._cluster_levels(candidates, threshold_pct=0.01)

        # Filter: only below current price, within 15% range
        lower_bound = current_price * 0.85
        filtered = [c for c in candidates if lower_bound < c < current_price * 0.998]

        # Sort nearest-first (highest values first = closest to current price)
        filtered.sort(reverse=True)
        return filtered[:3]

    def _find_resistance_levels(self, closes, highs, current_price, ma_latest,
                                boll_upper: float = None, volumes=None) -> List[float]:
        """Find key resistance levels using multi-method best practices.

        Methods combined:
        1. Swing highs (actual reversal points from recent 120 bars)
        2. Price clustering (zones with multiple touches)
        3. MA dynamic resistance (MA20/MA60 above current price)
        4. Bollinger upper band
        5. Psychological round-number levels
        Ordered nearest-first (closest resistance is most actionable).
        """
        candidates: List[float] = []

        # 1. Swing highs from recent 120 bars
        lookback = min(120, len(highs))
        if lookback >= 15:
            swing_highs = []
            vals = highs.tail(lookback).values
            for i in range(5, lookback - 5):
                window = vals[i - 5: i + 6]
                if vals[i] == window.max():
                    swing_highs.append(float(vals[i]))
            zones = self._cluster_levels(swing_highs)
            for z in zones:
                if z > current_price * 1.005:  # at least 0.5% above
                    candidates.append(z)

        # 2. MA dynamic resistance
        for key in ['ma20', 'ma60', 'ma10']:
            if key in ma_latest and ma_latest[key] > current_price * 1.002:
                candidates.append(round(ma_latest[key], 2))

        # 3. Bollinger upper band
        if boll_upper is not None and boll_upper > current_price * 1.002:
            candidates.append(round(boll_upper, 2))

        # 4. Psychological round-number levels
        if current_price > 10:
            step = 10 if current_price > 50 else 5
            nearest_round = (int(current_price / step) + 1) * step
            if nearest_round > current_price * 1.002:
                candidates.append(float(nearest_round))

        # Deduplicate
        if candidates:
            candidates = self._cluster_levels(candidates, threshold_pct=0.01)

        # Filter: only above current price, within 15% range
        upper_bound = current_price * 1.15
        filtered = [c for c in candidates if current_price * 1.002 < c < upper_bound]

        # Sort nearest-first (lowest values first = closest to current price)
        filtered.sort()
        return filtered[:3]

    async def _analyze_capital_flow(self, data: Dict) -> CapitalFlowAnalysis:
        """资金面分析 — size-normalized, multi-tier scoring

        Best-practice enhancements:
        1. Size-normalized: net inflow % of circulating market cap
        2. Super-large order weighting: institutional orders carry more signal
        3. Flow momentum: 5d vs 10d acceleration/deceleration
        4. Multi-timeframe consistency (today + 5d + 10d alignment)
        """
        capital_flow = data.get('capital_flow')
        quote = data.get('quote', {})

        if not capital_flow:
            return CapitalFlowAnalysis(
                score=5.0, main_net_inflow=0, main_inflow_ratio=0,
                trend="数据不足", summary="资金流向数据不可用"
            )

        main_inflow = capital_flow.get('main_net_inflow', 0) or 0
        main_inflow_pct = capital_flow.get('main_net_inflow_pct', 0) or 0
        super_large = capital_flow.get('super_large_net_inflow', 0) or 0
        inflow_5d = capital_flow.get('main_net_inflow_5d', 0) or 0
        inflow_10d = capital_flow.get('main_net_inflow_10d', 0) or 0
        inflow_20d = capital_flow.get('main_net_inflow_20d', 0) or 0

        # Size-normalized inflow ratio (% of circulating market cap)
        circ_cap = (quote.get('circulating_market_cap', 0) or 0) if quote else 0
        norm_pct = (main_inflow / circ_cap * 100) if circ_cap > 0 else main_inflow_pct

        # ── Trend: multi-timeframe consistency ──
        today_dir = 1 if main_inflow > 0 else (-1 if main_inflow < 0 else 0)
        five_dir = 1 if inflow_5d > 0 else (-1 if inflow_5d < 0 else 0)
        ten_dir = 1 if inflow_10d > 0 else (-1 if inflow_10d < 0 else 0)
        consistency = today_dir + five_dir + ten_dir  # [-3, +3]

        if consistency >= 2:
            trend = "持续流入"
        elif today_dir > 0:
            trend = "流入"
        elif consistency <= -2:
            trend = "持续流出"
        elif today_dir < 0:
            trend = "流出"
        else:
            trend = "平衡"

        # ── Flow momentum ──
        avg_5d = inflow_5d / 5 if inflow_5d else 0
        avg_10d = inflow_10d / 10 if inflow_10d else 0
        momentum = "加速" if avg_5d > avg_10d * 1.3 else ("减速" if avg_10d != 0 and avg_5d < avg_10d * 0.7 else "平稳")

        # ── Score (0-10) ──
        score = 5.0

        # 1. Today direction (±1.0)
        if main_inflow > 0:
            score += 1.0
        elif main_inflow < 0:
            score -= 1.0

        # 2. Multi-timeframe consistency (±1.5)
        if consistency >= 2:
            score += 1.5
        elif consistency <= -2:
            score -= 1.5
        elif consistency == 1:
            score += 0.5
        elif consistency == -1:
            score -= 0.5

        # 3. Size-normalized magnitude (±1.0)
        if abs(norm_pct) > 2:
            score += 1.0 if norm_pct > 0 else -1.0
        elif abs(norm_pct) > 0.5:
            score += 0.5 if norm_pct > 0 else -0.5

        # 4. Super-large order signal (±0.8) — institutional smart money
        if super_large > 0:
            score += 0.8
        elif super_large < 0:
            score -= 0.5

        # 5. Flow momentum (±0.5)
        if momentum == "加速" and main_inflow > 0:
            score += 0.5
        elif momentum == "加速" and main_inflow < 0:
            score -= 0.5

        # 6. 20-day trend context (±0.3)
        if inflow_20d > 0 and inflow_5d > 0:
            score += 0.3
        elif inflow_20d < 0 and inflow_5d < 0:
            score -= 0.3

        score = round(max(0, min(10, score)), 1)

        # ── Summary ──
        def _fmt(val):
            if abs(val) >= 1e8:
                return f"{val/1e8:.1f}亿"
            elif abs(val) >= 1e4:
                return f"{val/1e4:.0f}万"
            return f"{val:.0f}"

        summary = f"主力资金{trend}（{momentum}）。"
        summary += f"今日主力净{'流入' if main_inflow > 0 else '流出'}{_fmt(abs(main_inflow))}"
        if super_large != 0:
            summary += f"，超大单净{'流入' if super_large > 0 else '流出'}{_fmt(abs(super_large))}"
        summary += f"。近5日累计净{'流入' if inflow_5d > 0 else '流出'}{_fmt(abs(inflow_5d))}。"
        summary += f"资金面评分{score}分。"

        return CapitalFlowAnalysis(
            score=score,
            main_net_inflow=main_inflow,
            main_net_inflow_5d=inflow_5d,
            main_net_inflow_10d=inflow_10d,
            super_large_net_inflow=super_large,
            large_net_inflow=capital_flow.get('large_net_inflow', 0) or 0,
            super_large_net_inflow_5d=capital_flow.get('super_large_net_inflow_5d', 0) or 0,
            large_net_inflow_5d=capital_flow.get('large_net_inflow_5d', 0) or 0,
            super_large_net_inflow_10d=capital_flow.get('super_large_net_inflow_10d', 0) or 0,
            large_net_inflow_10d=capital_flow.get('large_net_inflow_10d', 0) or 0,
            medium_net_inflow=capital_flow.get('medium_net_inflow', 0) or 0,
            small_net_inflow=capital_flow.get('small_net_inflow', 0) or 0,
            main_inflow_ratio=main_inflow_pct / 100 if main_inflow_pct else 0,
            trend=trend,
            summary=summary
        )

    def _calculate_overall_score(
        self,
        fundamental: FundamentalAnalysis,
        technical: TechnicalAnalysis,
        capital_flow: CapitalFlowAnalysis,
        valuation_score: float = 5.0,
        news_score: float = 5.0,
    ) -> float:
        """计算综合评分（PRD 4.7.1 五维加权）
        基本面35% + 技术面25% + 资金面20% + 估值15% + 消息面5%
        """
        overall = (
            fundamental.score * self.WEIGHT_FUNDAMENTAL +
            technical.score * self.WEIGHT_TECHNICAL +
            capital_flow.score * self.WEIGHT_CAPITAL +
            valuation_score * self.WEIGHT_VALUATION +
            news_score * self.WEIGHT_NEWS
        )
        return round(overall, 1)

    def _score_news(self, news_list: list) -> float:
        """消息面评分 (0-10) — severity-weighted keyword sentiment

        Best-practice enhancements:
        1. Severity-weighted keywords (退市 >> 减持, 回购 >> 增长)
        2. Time decay: recent news (top of list) weighted 2x vs older news
        3. Expanded keyword dictionary with A-share specific terms
        4. Per-article dedup (same keyword in one article counted once)
        """
        if not news_list:
            return 5.0

        # {keyword: severity_weight} — higher weight = stronger signal
        positive_kw = {
            '回购': 3, '增持': 3, '业绩预增': 3, '扭亏': 2, '超预期': 3,
            '获批': 2, '中标': 2, '战略合作': 2, '突破': 1, '创新高': 2,
            '利好': 1, '增长': 1, '分红': 2, '消费复苏': 1, '提价': 2,
            '大单': 1, '金叉': 1, '放量上涨': 1, '涨停': 2, '龙头': 1,
            '摆脱困境': 1, '利润大增': 2, '订单': 1, '创新高': 2,
        }
        negative_kw = {
            '退市': 5, 'ST': 4, '*ST': 5, '立案调查': 4, '违规': 3,
            '处罚': 3, '诉讼': 2, '减持': 2, '亏损': 2, '业绩预减': 3,
            '下滑': 1, '暴跌': 2, '跌停': 3, '质押': 2, '冻结': 2,
            '警示': 2, '利空': 1, '违约': 2, '破产': 4, '失信': 3,
            '爆雷': 3, '商誉减值': 2, '停产': 2, '召回': 1,
        }

        pos_score = 0.0
        neg_score = 0.0
        total_articles = min(len(news_list), 20)

        for idx, item in enumerate(news_list[:20]):
            text = item.get('title', '') + ' ' + (item.get('content', '') or '')[:200]
            # Time decay: first 5 articles get 2x weight, next 10 get 1x, rest 0.5x
            if idx < 5:
                decay = 2.0
            elif idx < 15:
                decay = 1.0
            else:
                decay = 0.5

            # Per-article dedup: each keyword counted once per article
            article_pos = set()
            article_neg = set()
            for kw, weight in positive_kw.items():
                if kw in text and kw not in article_pos:
                    pos_score += weight * decay
                    article_pos.add(kw)
            for kw, weight in negative_kw.items():
                if kw in text and kw not in article_neg:
                    neg_score += weight * decay
                    article_neg.add(kw)

        total = pos_score + neg_score
        if total == 0:
            return 5.0
        sentiment = (pos_score - neg_score) / total  # [-1, 1]
        return round(max(0, min(10, 5.0 + sentiment * 4.0)), 1)

    def _assess_risk(self, overall_score: float, data: Optional[Dict] = None) -> str:
        """评估风险等级 (PRD 4.7.2) — enhanced with volatility & liquidity

        Best practice: risk is NOT just the inverse of score.
        High-scoring volatile small-caps can still be high-risk.
        """
        # Base risk from overall score
        if overall_score >= 7.0:
            risk = "low"
        elif overall_score >= 5.0:
            risk = "medium"
        else:
            risk = "high"

        # Volatility & liquidity adjustments (if data available)
        if data:
            quote = data.get('quote', {})
            if quote:
                # High amplitude (>5%) today suggests elevated risk
                amplitude = quote.get('amplitude', 0) or 0
                if amplitude > 5 and risk == "low":
                    risk = "medium"

                # Very low turnover (<0.3%) = liquidity risk
                turnover = quote.get('turnover_rate', 0) or 0
                if turnover < 0.3 and risk == "low":
                    risk = "medium"

                # ST stocks are always high risk
                name = quote.get('stock_name', '')
                if 'ST' in name or '*ST' in name:
                    risk = "high"

        return risk

    def _generate_recommendation(self, overall_score: float) -> str:
        """生成投资建议 (PRD 4.7.3)"""
        if overall_score >= 7.0:
            return "buy"
        elif overall_score >= 5.5:
            return "hold"
        elif overall_score >= 4.0:
            return "watch"
        else:
            return "sell"

    def _generate_summary(
        self,
        fundamental: FundamentalAnalysis,
        technical: TechnicalAnalysis,
        capital_flow: CapitalFlowAnalysis,
        overall_score: float = 0,
    ) -> str:
        """生成综合分析总结"""
        return f"基本面：{fundamental.summary} 技术面：{technical.summary} 资金面：{capital_flow.summary} 综合评分{overall_score}分。以上分析仅供参考，不构成投资建议。"

    async def _get_from_cache(self, key: str) -> Optional[Dict]:
        """从缓存获取数据"""
        try:
            cached = self.cache.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def _set_to_cache(self, key: str, value: Dict, ttl: int) -> bool:
        """设置缓存"""
        try:
            self.cache.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
