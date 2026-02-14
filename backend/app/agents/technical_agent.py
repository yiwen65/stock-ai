"""Technical Agent - 技术面分析 Agent (PRD 6.2.1 模板3)"""

import logging
import pandas as pd
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class TechnicalAgent(BaseAgent):
    """技术面分析 Agent — 趋势/支撑压力/技术指标综合信号"""

    def __init__(self, llm_service, name: str = "technical-agent"):
        super().__init__(llm_service, name)

    def _get_system_prompt(self) -> str:
        return """你是一位专业的A股技术分析师，精通均线系统、MACD、RSI、KDJ、布林带等技术指标。

分析维度：
1. 趋势判断：均线排列状态(多头/空头/交叉)、ADX趋势强度
2. 技术指标综合信号：MACD金叉/死叉、RSI超买超卖、KDJ位置、布林带位置
3. 支撑位与压力位：近期高低点、均线支撑、整数关口
4. 成交量配合：量价关系、放量/缩量特征

输出要求：
- 给出趋势判断(上涨/下跌/震荡)
- 识别 2-3 个关键支撑位和压力位
- 列出当前技术信号(看多/看空/中性)
- 给出技术面综合评分 (0-10)
- 所有分析必须基于提供的数据

重要：技术分析仅供参考，不构成投资建议。"""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行技术面分析"""
        prompt = self._build_prompt(context)

        try:
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt},
            ]
            result = await self.llm_service.structured_output(messages)

            return {
                "agent": "technical",
                "score": float(result.get("score", 5.0)),
                "trend": result.get("trend", "震荡"),
                "support_levels": result.get("support_levels", []),
                "resistance_levels": result.get("resistance_levels", []),
                "signals": result.get("signals", []),
                "summary": result.get("summary", ""),
                "analysis": result.get("analysis", result.get("raw_response", "")),
            }
        except Exception as e:
            logger.error(f"TechnicalAgent error: {e}")
            return {
                "agent": "technical",
                "score": 5.0,
                "trend": "震荡",
                "summary": f"技术面分析暂时无法完成: {e}",
                "analysis": "",
            }

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        stock_code = context.get("stock_code", "")
        stock_name = context.get("stock_name", stock_code)
        realtime = context.get("realtime", {})
        kline: List[Dict] = context.get("kline", [])

        lines = [f"请对 {stock_name}({stock_code}) 进行技术面分析。\n"]

        # Real-time
        lines.append("【实时行情】")
        lines.append(f"- 最新价: {realtime.get('price', 'N/A')}")
        lines.append(f"- 涨跌幅: {realtime.get('pct_change', 'N/A')}%")
        lines.append(f"- 成交量: {realtime.get('volume', 'N/A')}")
        lines.append(f"- 换手率: {realtime.get('turnover_rate', 'N/A')}%")
        lines.append(f"- 量比: {realtime.get('volume_ratio', 'N/A')}")
        lines.append(f"- 振幅: {realtime.get('amplitude', 'N/A')}%")
        lines.append("")

        # Compute indicators from K-line if available
        if kline and len(kline) >= 20:
            indicators = self._compute_indicators(kline)
            lines.append("【技术指标 (基于日K线)】")
            for k, v in indicators.items():
                lines.append(f"- {k}: {v}")
            lines.append("")

            # Recent K-line (last 10 days)
            lines.append("【近10日K线】")
            for bar in kline[-10:]:
                lines.append(
                    f"  {bar['date']}: O={bar['open']:.2f} H={bar['high']:.2f} "
                    f"L={bar['low']:.2f} C={bar['close']:.2f} V={bar['volume']}"
                )
            lines.append("")
        else:
            lines.append("【K线数据不足，无法计算技术指标】\n")

        lines.append(
            "请返回 JSON，包含字段: score(0-10), trend(上涨/下跌/震荡), "
            "support_levels(list of float), resistance_levels(list of float), "
            "signals(list of string, 如'MACD金叉','RSI超卖'), summary(一段话), analysis(详细分析)"
        )
        return "\n".join(lines)

    def _compute_indicators(self, kline: List[Dict]) -> Dict[str, str]:
        """Pre-compute key indicators to include in the prompt."""
        try:
            from app.utils.indicators import (
                calculate_ma, calculate_macd, calculate_rsi,
                calculate_kdj, calculate_bollinger_bands,
            )
            closes = pd.Series([bar["close"] for bar in kline])
            highs = pd.Series([bar["high"] for bar in kline])
            lows = pd.Series([bar["low"] for bar in kline])

            result = {}

            # MA
            for period in [5, 10, 20, 60]:
                ma = calculate_ma(closes, period)
                val = ma.iloc[-1] if len(ma) > 0 and not pd.isna(ma.iloc[-1]) else None
                result[f"MA{period}"] = f"{val:.2f}" if val else "N/A"

            # MACD
            dif, dea, hist = calculate_macd(closes)
            if len(dif) > 0:
                result["MACD DIF"] = f"{dif.iloc[-1]:.4f}" if not pd.isna(dif.iloc[-1]) else "N/A"
                result["MACD DEA"] = f"{dea.iloc[-1]:.4f}" if not pd.isna(dea.iloc[-1]) else "N/A"
                result["MACD柱"] = f"{hist.iloc[-1]:.4f}" if not pd.isna(hist.iloc[-1]) else "N/A"

            # RSI
            rsi = calculate_rsi(closes, 14)
            result["RSI(14)"] = f"{rsi.iloc[-1]:.2f}" if len(rsi) > 0 and not pd.isna(rsi.iloc[-1]) else "N/A"

            # KDJ
            k, d, j = calculate_kdj(highs, lows, closes)
            if len(k) > 0:
                result["KDJ K"] = f"{k.iloc[-1]:.2f}" if not pd.isna(k.iloc[-1]) else "N/A"
                result["KDJ D"] = f"{d.iloc[-1]:.2f}" if not pd.isna(d.iloc[-1]) else "N/A"
                result["KDJ J"] = f"{j.iloc[-1]:.2f}" if not pd.isna(j.iloc[-1]) else "N/A"

            # Bollinger
            upper, mid, lower = calculate_bollinger_bands(closes)
            if len(upper) > 0:
                result["布林上轨"] = f"{upper.iloc[-1]:.2f}" if not pd.isna(upper.iloc[-1]) else "N/A"
                result["布林中轨"] = f"{mid.iloc[-1]:.2f}" if not pd.isna(mid.iloc[-1]) else "N/A"
                result["布林下轨"] = f"{lower.iloc[-1]:.2f}" if not pd.isna(lower.iloc[-1]) else "N/A"

            return result
        except Exception as e:
            logger.warning(f"Indicator computation error: {e}")
            return {"error": str(e)}
