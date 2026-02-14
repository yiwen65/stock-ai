# backend/app/engines/risk_scorer.py
"""
Comprehensive risk scoring engine.
Evaluates stocks on multiple risk dimensions and returns a 1-10 score
(1 = highest risk, 10 = lowest risk) plus a risk level label.
"""
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class RiskScorer:
    """Multi-dimensional risk scorer per PRD 1.3.4."""

    def __init__(self):
        # Weights for each dimension (sum = 1.0)
        self.weights = {
            "financial": 0.30,
            "valuation": 0.25,
            "liquidity": 0.20,
            "volatility": 0.15,
            "event": 0.10,
        }

    def score(
        self,
        quote: Dict,
        financials: Optional[List[Dict]] = None,
        capital_flow: Optional[Dict] = None,
    ) -> Dict:
        """
        Return {"score": float 1-10, "risk_level": str, "details": {...}}.
        """
        details = {}

        details["financial"] = self._score_financial(financials)
        details["valuation"] = self._score_valuation(quote)
        details["liquidity"] = self._score_liquidity(quote)
        details["volatility"] = self._score_volatility(quote)
        details["event"] = self._score_event(quote, capital_flow)

        total = sum(
            details[dim] * self.weights[dim] for dim in self.weights
        )
        total = max(1.0, min(10.0, total))

        risk_level = self._level(total)

        return {
            "score": round(total, 2),
            "risk_level": risk_level,
            "details": {k: round(v, 2) for k, v in details.items()},
        }

    # ------------------------------------------------------------------
    # Dimension scorers (each returns 1-10, higher = safer)
    # ------------------------------------------------------------------

    def _score_financial(self, financials: Optional[List[Dict]]) -> float:
        """Financial health risk: debt ratio, current ratio, profitability."""
        if not financials:
            return 5.0  # neutral when data unavailable

        latest = financials[0]
        score = 5.0

        debt = latest.get("debt_ratio", 50)
        if debt < 30:
            score += 2
        elif debt < 50:
            score += 1
        elif debt > 70:
            score -= 2
        elif debt > 60:
            score -= 1

        cr = latest.get("current_ratio", 1.0)
        if cr > 2:
            score += 1.5
        elif cr > 1.5:
            score += 0.5
        elif cr < 1:
            score -= 1.5

        roe = latest.get("roe", 0)
        if roe > 15:
            score += 1
        elif roe < 0:
            score -= 2
        elif roe < 5:
            score -= 1

        return max(1.0, min(10.0, score))

    def _score_valuation(self, quote: Dict) -> float:
        """Valuation risk: PE/PB extremes."""
        score = 6.0
        pe = quote.get("pe")
        pb = quote.get("pb")

        if pe is not None and pe > 0:
            if pe < 15:
                score += 2
            elif pe < 30:
                score += 1
            elif pe > 100:
                score -= 3
            elif pe > 60:
                score -= 2
        elif pe is not None and pe < 0:
            score -= 2  # negative PE = loss-making

        if pb is not None and pb > 0:
            if pb < 2:
                score += 1
            elif pb > 10:
                score -= 2
            elif pb > 5:
                score -= 1

        return max(1.0, min(10.0, score))

    def _score_liquidity(self, quote: Dict) -> float:
        """Liquidity risk: turnover rate, market cap, volume."""
        score = 5.0

        mcap = quote.get("market_cap", 0)
        if mcap > 50e9:
            score += 2
        elif mcap > 10e9:
            score += 1
        elif mcap < 2e9:
            score -= 2
        elif mcap < 5e9:
            score -= 1

        tr = quote.get("turnover_rate", 0)
        if 1 < tr < 10:
            score += 1.5  # healthy turnover
        elif tr < 0.5:
            score -= 1.5  # illiquid
        elif tr > 20:
            score -= 1  # overly speculative

        amount = quote.get("amount", 0)
        if amount > 1e9:
            score += 0.5
        elif amount < 1e7:
            score -= 1.5

        return max(1.0, min(10.0, score))

    def _score_volatility(self, quote: Dict) -> float:
        """Volatility risk: amplitude, recent change magnitude."""
        score = 6.0

        amp = abs(quote.get("amplitude", 0))
        if amp > 8:
            score -= 2
        elif amp > 5:
            score -= 1
        elif amp < 2:
            score += 1

        pct = abs(quote.get("pct_change", 0))
        if pct > 8:
            score -= 2
        elif pct > 5:
            score -= 1

        change_60d = abs(quote.get("change_60d", 0))
        if change_60d > 50:
            score -= 1.5
        elif change_60d > 30:
            score -= 0.5

        return max(1.0, min(10.0, score))

    def _score_event(self, quote: Dict, capital_flow: Optional[Dict]) -> float:
        """Event / capital risk: ST, capital outflow."""
        score = 6.0
        name = quote.get("stock_name", "")

        if "ST" in name or "*ST" in name:
            score -= 4

        if capital_flow:
            main_net = capital_flow.get("main_net_inflow", 0)
            if main_net < -5e7:
                score -= 2
            elif main_net < -1e7:
                score -= 1
            elif main_net > 5e7:
                score += 1.5

        return max(1.0, min(10.0, score))

    # ------------------------------------------------------------------
    @staticmethod
    def _level(score: float) -> str:
        if score >= 7:
            return "low"
        elif score >= 4:
            return "medium"
        else:
            return "high"
