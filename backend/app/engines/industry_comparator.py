"""同行业对比分析引擎 (PRD §4.6)"""

import logging
from typing import Dict, Any, List, Optional
from app.services.data_service import DataService

logger = logging.getLogger(__name__)


class IndustryComparator:
    """同行业对比分析 — 横向对比 PE/PB/ROE/增长率，输出排名与定位"""

    def __init__(self, data_service: Optional[DataService] = None):
        self.data_service = data_service or DataService()

    async def compare(self, stock_code: str) -> Dict[str, Any]:
        """对比目标股票与同行业公司的关键指标

        Returns:
            {
                "industry": "白酒",
                "target": { stock metrics + ranks },
                "peers": [ peer metrics ],
                "comparison_metrics": [ metric summaries ],
                "industry_position": "...",
            }
        """
        # 1. Fetch peer data (already has industry detection + snapshot)
        peer_data = await self.data_service.fetch_peer_comparison(stock_code, limit=10)

        industry = peer_data.get("industry", "未知")
        target = peer_data.get("target")
        peers = peer_data.get("peers", [])

        if not target:
            return {
                "industry": industry,
                "target": None,
                "peers": [],
                "comparison_metrics": [],
                "industry_position": "无法获取目标股票数据",
            }

        # 2. Fetch financial data for target + top peers for ROE/growth
        all_stocks = [target] + peers
        await self._enrich_financials(all_stocks)

        # 3. Compute ranks for each metric
        metrics_to_rank = [
            ("pe", "asc"),           # lower PE is better
            ("pb", "asc"),           # lower PB is better
            ("roe", "desc"),         # higher ROE is better
            ("revenue_growth", "desc"),
            ("net_profit_growth", "desc"),
            ("market_cap", "desc"),
            ("pct_change", "desc"),
        ]

        total_count = len(all_stocks)
        comparison_metrics = []

        for metric, order in metrics_to_rank:
            values = []
            for s in all_stocks:
                val = s.get(metric)
                if val is not None and val != 0:
                    values.append((s["stock_code"], float(val)))

            if not values:
                continue

            reverse = (order == "desc")
            values.sort(key=lambda x: x[1], reverse=reverse)

            # Find target rank
            target_rank = None
            target_val = None
            for rank, (code, val) in enumerate(values, 1):
                if code == stock_code:
                    target_rank = rank
                    target_val = val
                    break

            if target_rank is None:
                continue

            # Compute industry average (exclude target)
            peer_vals = [v for c, v in values if c != stock_code]
            avg_val = sum(peer_vals) / len(peer_vals) if peer_vals else 0

            metric_label = self._metric_label(metric)
            comparison_metrics.append({
                "metric": metric,
                "label": metric_label,
                "target_value": round(target_val, 2),
                "industry_avg": round(avg_val, 2),
                "rank": target_rank,
                "total": len(values),
                "percentile": round((1 - (target_rank - 1) / max(len(values) - 1, 1)) * 100, 1),
                "vs_avg": "高于平均" if (
                    (target_val > avg_val and order == "desc") or
                    (target_val < avg_val and order == "asc")
                ) else "低于平均" if (
                    (target_val < avg_val and order == "desc") or
                    (target_val > avg_val and order == "asc")
                ) else "持平",
            })

        # 4. Set ranks on target
        for cm in comparison_metrics:
            target[f"{cm['metric']}_rank"] = cm["rank"]
            target[f"{cm['metric']}_total"] = cm["total"]

        # 5. Generate industry position summary
        position = self._assess_position(target, comparison_metrics, total_count)

        return {
            "industry": industry,
            "target": target,
            "peers": peers[:6],
            "comparison_metrics": comparison_metrics,
            "industry_position": position,
        }

    async def _enrich_financials(self, stocks: List[Dict]) -> None:
        """Enrich stock dicts with ROE/growth from financial data (best effort)."""
        for stock in stocks[:8]:
            code = stock.get("stock_code", "")
            if not code:
                continue
            try:
                financials = await self.data_service.fetch_financial_data(code, years=1)
                if financials:
                    latest = financials[-1]
                    stock.setdefault("roe", latest.get("roe"))
                    stock.setdefault("revenue_growth", latest.get("revenue_growth"))
                    stock.setdefault("net_profit_growth", latest.get("net_profit_growth"))
                    stock.setdefault("gross_margin", latest.get("gross_margin"))
                    stock.setdefault("net_margin", latest.get("net_margin"))
                    stock.setdefault("debt_ratio", latest.get("debt_ratio"))
            except Exception as e:
                logger.debug(f"Could not enrich financials for {code}: {e}")

    @staticmethod
    def _metric_label(metric: str) -> str:
        labels = {
            "pe": "市盈率(PE)",
            "pb": "市净率(PB)",
            "roe": "净资产收益率(ROE)",
            "revenue_growth": "营收增长率",
            "net_profit_growth": "净利润增长率",
            "market_cap": "总市值",
            "pct_change": "涨跌幅",
            "gross_margin": "毛利率",
            "net_margin": "净利率",
            "debt_ratio": "资产负债率",
        }
        return labels.get(metric, metric)

    @staticmethod
    def _assess_position(
        target: Dict, metrics: List[Dict], total: int
    ) -> str:
        """Generate a concise industry position summary."""
        if not metrics:
            return "行业对比数据不足，无法评估行业地位。"

        strengths = []
        weaknesses = []

        for m in metrics:
            label = m["label"]
            rank = m["rank"]
            total_m = m["total"]
            if rank <= max(total_m * 0.3, 1):
                strengths.append(f"{label}排名{rank}/{total_m}")
            elif rank >= total_m * 0.7:
                weaknesses.append(f"{label}排名{rank}/{total_m}")

        parts = []
        name = target.get("stock_name", target.get("stock_code", ""))
        parts.append(f"{name}在同行业{total}家公司中：")

        if strengths:
            parts.append(f"优势指标：{', '.join(strengths)}。")
        if weaknesses:
            parts.append(f"偏弱指标：{', '.join(weaknesses)}。")
        if not strengths and not weaknesses:
            parts.append("各项指标处于行业中游水平。")

        return " ".join(parts)
