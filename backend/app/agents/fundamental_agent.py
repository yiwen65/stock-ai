"""Fundamental Agent - 基本面分析 Agent (PRD 6.2.1 模板2)"""

import json
import logging
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class FundamentalAgent(BaseAgent):
    """基本面分析 Agent — 估值/盈利/成长/财务健康"""

    def __init__(self, llm_service, name: str = "fundamental-agent"):
        super().__init__(llm_service, name)

    def _get_system_prompt(self) -> str:
        return """你是一位专业的A股基本面分析师，擅长财务报表分析和公司估值。

分析维度和权重：
1. 估值水平 (25%)：PE/PB 与行业均值对比，历史分位判断
2. 盈利能力 (30%)：ROE、净利率、EPS 趋势
3. 成长性 (25%)：营收增长率、净利润增长率、CAGR
4. 财务健康 (20%)：资产负债率、流动比率、现金流状况

输出要求：
- 每个维度给出 0-10 分评分和简要分析
- 列出 2-3 个核心优势和 2-3 个主要风险
- 给出基本面综合评分 (0-10)
- 所有分析必须基于提供的数据，不可臆测

重要：你的分析仅供参考，不构成投资建议。"""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行基本面分析"""
        prompt = self._build_prompt(context)

        try:
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt},
            ]
            result = await self.llm_service.structured_output(messages)

            return {
                "agent": "fundamental",
                "score": float(result.get("score", 5.0)),
                "valuation_score": float(result.get("valuation_score", 5.0)),
                "profitability_score": float(result.get("profitability_score", 5.0)),
                "growth_score": float(result.get("growth_score", 5.0)),
                "health_score": float(result.get("health_score", 5.0)),
                "strengths": result.get("strengths", []),
                "risks": result.get("risks", []),
                "summary": result.get("summary", ""),
                "analysis": result.get("analysis", result.get("raw_response", "")),
            }
        except Exception as e:
            logger.error(f"FundamentalAgent error: {e}")
            return {
                "agent": "fundamental",
                "score": 5.0,
                "summary": f"基本面分析暂时无法完成: {e}",
                "analysis": "",
            }

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        stock_code = context.get("stock_code", "")
        stock_name = context.get("stock_name", stock_code)
        realtime = context.get("realtime", {})
        financials: List[Dict] = context.get("financial", [])

        lines = [f"请对 {stock_name}({stock_code}) 进行基本面分析。\n"]

        # Real-time valuation
        lines.append("【实时估值数据】")
        lines.append(f"- 最新价: {realtime.get('price', 'N/A')}")
        lines.append(f"- 市盈率(PE-TTM): {realtime.get('pe', 'N/A')}")
        lines.append(f"- 市净率(PB): {realtime.get('pb', 'N/A')}")
        mcap = realtime.get("market_cap", 0)
        lines.append(f"- 总市值: {mcap / 1e8:.2f} 亿" if mcap else "- 总市值: N/A")
        lines.append(f"- 换手率: {realtime.get('turnover_rate', 'N/A')}%")
        lines.append("")

        # Financial data (recent quarters)
        if financials:
            lines.append("【近期财务指标】")
            for i, f in enumerate(financials[:8]):
                lines.append(
                    f"  {f.get('report_date', '?')}: "
                    f"EPS={f.get('eps', 'N/A')} | ROE={f.get('roe', 'N/A')}% | "
                    f"营收增长={f.get('revenue_growth', 'N/A')}% | "
                    f"净利润增长={f.get('net_profit_growth', 'N/A')}% | "
                    f"负债率={f.get('debt_ratio', 'N/A')}% | "
                    f"流动比率={f.get('current_ratio', 'N/A')} | "
                    f"毛利率={f.get('gross_margin', 'N/A')}% | "
                    f"净利率={f.get('net_margin', 'N/A')}%"
                )
            lines.append("")
        else:
            lines.append("【财务数据暂无】\n")

        lines.append(
            "请返回 JSON，包含字段: score(综合0-10), valuation_score, profitability_score, "
            "growth_score, health_score, strengths(list), risks(list), summary(一段话), analysis(详细分析文字)"
        )
        return "\n".join(lines)
