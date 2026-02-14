"""Evaluator Agent - 综合评估 Agent (PRD 6.2.1 模板4)"""

import logging
from typing import Dict, Any
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class EvaluatorAgent(BaseAgent):
    """综合评估 Agent — 多维加权评分 + 风险等级 + 操作建议"""

    # PRD 4.7.1 权重
    WEIGHTS = {"fundamental": 0.35, "technical": 0.25, "capital_flow": 0.20, "valuation": 0.15, "news": 0.05}

    def __init__(self, llm_service, name: str = "evaluator-agent"):
        super().__init__(llm_service, name)

    def _get_system_prompt(self) -> str:
        return """你是一位资深A股投资顾问，需要综合多维度分析给出最终投资评估。

评估维度权重(PRD规定)：
- 基本面: 35%
- 技术面: 25%
- 资金面: 20%
- 估值:   15%
- 消息面: 5% (暂无数据时用中性5分)

你需要输出：
1. 综合评分 (0-10)
2. 风险等级 (low/medium/high)
3. 投资建议 (buy/hold/watch/sell)
4. 置信度 confidence (high/medium/low) — 基于数据完整性和各维度一致性
5. 建议仓位比例 (0-100%)
6. 建议买入价区间 / 止损价 / 目标价
7. 3-5 条核心投资逻辑
8. 综合分析摘要

重要合规要求：
- 所有建议必须附带"仅供参考，不构成投资建议"
- 不得使用绝对化用语如"一定"、"保证"
- 必须提示投资风险"""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """综合评估：汇总基本面/技术面/资金面/消息面分析"""
        stock_code = context.get("stock_code", "")
        stock_name = context.get("stock_name", stock_code)

        fundamental = context.get("fundamental", {})
        technical = context.get("technical", {})
        capital_flow = context.get("capital_flow", {})
        news = context.get("news", {})
        realtime = context.get("realtime", {})

        prompt = self._build_prompt(
            stock_code, stock_name, realtime, fundamental, technical, capital_flow, news
        )

        try:
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt},
            ]
            result = await self.llm_service.structured_output(messages)

            # Compute weighted score from sub-agents as fallback
            f_score = fundamental.get("score", 5.0)
            t_score = technical.get("score", 5.0)
            c_score = capital_flow.get("score", 5.0)
            n_score = news.get("score", 5.0)
            weighted = (
                f_score * self.WEIGHTS["fundamental"]
                + t_score * self.WEIGHTS["technical"]
                + c_score * self.WEIGHTS["capital_flow"]
                + f_score * self.WEIGHTS["valuation"]  # use fundamental as proxy
                + n_score * self.WEIGHTS["news"]
            )

            overall = float(result.get("overall_score", weighted))
            risk_level = result.get("risk_level", "medium")
            recommendation = result.get("recommendation", "watch")

            # Compute confidence from data completeness & score agreement
            scores = [f_score, t_score, c_score, n_score]
            score_std = (sum((s - weighted) ** 2 for s in scores) / len(scores)) ** 0.5
            llm_confidence = result.get("confidence", "")
            if llm_confidence in ("high", "medium", "low"):
                confidence = llm_confidence
            elif score_std < 1.5:
                confidence = "high"
            elif score_std < 2.5:
                confidence = "medium"
            else:
                confidence = "low"

            return {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "overall_score": round(overall, 2),
                "risk_level": risk_level,
                "recommendation": recommendation,
                "confidence": confidence,
                "position_pct": result.get("position_pct", 0),
                "buy_range": result.get("buy_range", []),
                "stop_loss": result.get("stop_loss", None),
                "target_price": result.get("target_price", None),
                "reasons": result.get("reasons", []),
                "summary": result.get("summary", ""),
                "fundamental": fundamental,
                "technical": technical,
                "capital_flow": capital_flow,
                "news": news,
            }
        except Exception as e:
            logger.error(f"EvaluatorAgent error: {e}")
            return {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "overall_score": 5.0,
                "risk_level": "medium",
                "recommendation": "watch",
                "summary": f"综合评估暂时无法完成: {e}",
                "fundamental": fundamental,
                "technical": technical,
                "capital_flow": capital_flow,
                "news": news,
            }

    def _build_prompt(
        self, stock_code, stock_name, realtime, fundamental, technical, capital_flow, news=None
    ) -> str:
        price = realtime.get("price", "N/A")
        pct = realtime.get("pct_change", "N/A")
        news = news or {}

        lines = [
            f"请对 {stock_name}({stock_code}) 做综合投资评估。",
            f"当前价格: {price}  涨跌幅: {pct}%\n",
            "=== 基本面分析结果 ===",
            f"评分: {fundamental.get('score', 'N/A')}/10",
            f"摘要: {fundamental.get('summary', 'N/A')}",
            f"优势: {fundamental.get('strengths', [])}",
            f"风险: {fundamental.get('risks', [])}\n",
            "=== 技术面分析结果 ===",
            f"评分: {technical.get('score', 'N/A')}/10",
            f"趋势: {technical.get('trend', 'N/A')}",
            f"支撑位: {technical.get('support_levels', [])}",
            f"压力位: {technical.get('resistance_levels', [])}",
            f"信号: {technical.get('signals', [])}",
            f"摘要: {technical.get('summary', 'N/A')}\n",
            "=== 资金面分析结果 ===",
            f"评分: {capital_flow.get('score', 'N/A')}/10",
            f"趋势: {capital_flow.get('trend', 'N/A')}",
            f"主力意图: {capital_flow.get('main_intention', 'N/A')}",
            f"摘要: {capital_flow.get('summary', 'N/A')}\n",
            "=== 消息面分析结果 ===",
            f"评分: {news.get('score', 'N/A')}/10",
            f"情绪倾向: {news.get('sentiment', 'N/A')}",
            f"摘要: {news.get('summary', 'N/A')}\n",
            "请返回 JSON，包含字段: overall_score(0-10), risk_level(low/medium/high), "
            "recommendation(buy/hold/watch/sell), confidence(high/medium/low, 基于数据完整性和一致性), "
            "position_pct(建议仓位0-100), "
            "buy_range(list, 如[10.5, 11.0]), stop_loss(float), target_price(float), "
            "reasons(list of string, 3-5条核心逻辑), summary(综合分析摘要，200字以内)"
        ]
        return "\n".join(lines)
