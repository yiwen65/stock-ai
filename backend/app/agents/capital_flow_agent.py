"""Capital Flow Agent - 资金面分析 Agent"""

import logging
from typing import Dict, Any
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CapitalFlowAgent(BaseAgent):
    """资金面分析 Agent — 主力资金动向/资金趋势判断"""

    def __init__(self, llm_service, name: str = "capital-flow-agent"):
        super().__init__(llm_service, name)

    def _get_system_prompt(self) -> str:
        return """你是一位专业的A股资金面分析师，擅长解读主力资金动向和筹码分布。

分析维度：
1. 主力资金动向：今日/5日/10日/20日主力净流入趋势
2. 资金结构：超大单/大单/中单/小单资金分布
3. 资金趋势判断：持续流入/持续流出/资金分歧

输出要求：
- 判断资金趋势(持续流入/持续流出/资金分歧/无明显趋势)
- 分析主力意图(建仓/加仓/减仓/出货)
- 给出资金面评分 (0-10)
- 所有分析必须基于提供的数据

重要：资金分析仅供参考，不构成投资建议。"""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行资金面分析"""
        prompt = self._build_prompt(context)

        try:
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt},
            ]
            result = await self.llm_service.structured_output(messages)

            return {
                "agent": "capital_flow",
                "score": float(result.get("score", 5.0)),
                "trend": result.get("trend", "无明显趋势"),
                "main_intention": result.get("main_intention", ""),
                "summary": result.get("summary", ""),
                "analysis": result.get("analysis", result.get("raw_response", "")),
            }
        except Exception as e:
            logger.error(f"CapitalFlowAgent error: {e}")
            return {
                "agent": "capital_flow",
                "score": 5.0,
                "trend": "无明显趋势",
                "summary": f"资金面分析暂时无法完成: {e}",
                "analysis": "",
            }

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        stock_code = context.get("stock_code", "")
        stock_name = context.get("stock_name", stock_code)
        capital = context.get("capital_flow", {})
        realtime = context.get("realtime", {})

        lines = [f"请对 {stock_name}({stock_code}) 进行资金面分析。\n"]

        lines.append("【实时行情】")
        lines.append(f"- 最新价: {realtime.get('price', 'N/A')}")
        lines.append(f"- 涨跌幅: {realtime.get('pct_change', 'N/A')}%")
        lines.append(f"- 成交额: {realtime.get('amount', 'N/A')}")
        lines.append(f"- 换手率: {realtime.get('turnover_rate', 'N/A')}%")
        lines.append("")

        if capital:
            def _fmt_amount(val):
                if val is None:
                    return "N/A"
                v = float(val)
                if abs(v) >= 1e8:
                    return f"{v / 1e8:.2f}亿"
                if abs(v) >= 1e4:
                    return f"{v / 1e4:.0f}万"
                return f"{v:.0f}"

            lines.append("【资金流向数据】")
            lines.append(f"- 日期: {capital.get('date', 'N/A')}")
            lines.append(f"- 今日主力净流入: {_fmt_amount(capital.get('main_net_inflow'))}")
            lines.append(f"- 主力净流入占比: {capital.get('main_net_inflow_pct', 'N/A')}%")
            lines.append(f"- 超大单净流入: {_fmt_amount(capital.get('super_large_net_inflow'))}")
            lines.append(f"- 大单净流入: {_fmt_amount(capital.get('large_net_inflow'))}")
            lines.append(f"- 中单净流入: {_fmt_amount(capital.get('medium_net_inflow'))}")
            lines.append(f"- 小单净流入: {_fmt_amount(capital.get('small_net_inflow'))}")
            lines.append(f"- 近5日主力累计净流入: {_fmt_amount(capital.get('main_net_inflow_5d'))}")
            lines.append(f"- 近10日主力累计净流入: {_fmt_amount(capital.get('main_net_inflow_10d'))}")
            lines.append(f"- 近20日主力累计净流入: {_fmt_amount(capital.get('main_net_inflow_20d'))}")
            lines.append("")
        else:
            lines.append("【资金流向数据暂无】\n")

        lines.append(
            "请返回 JSON，包含字段: score(0-10), trend(持续流入/持续流出/资金分歧/无明显趋势), "
            "main_intention(建仓/加仓/减仓/出货/观望), summary(一段话), analysis(详细分析)"
        )
        return "\n".join(lines)
