"""Technical Agent - 技术面分析 Agent"""

from typing import Dict
from app.agents.base_agent import BaseAgent


class TechnicalAgent(BaseAgent):
    """技术面分析 Agent"""

    def __init__(self, llm_service, name: str = "technical-agent"):
        super().__init__(llm_service, name)

    def _get_system_prompt(self) -> str:
        return """你是一个专业的技术分析师。

你的任务是分析股票的技术面，包括：
1. 趋势判断（上涨/下跌/震荡）
2. 技术指标（MA、MACD、RSI、KDJ）
3. 支撑位和压力位
4. 买卖时机

请给出：
- 技术面评分（0-10分）
- 关键技术信号
- 操作建议
"""

    async def execute(self, context: Dict) -> Dict:
        """执行技术面分析"""
        prompt = self._build_analysis_prompt(context)
        analysis = await self._call_llm(prompt)

        return {
            'agent': 'technical',
            'analysis': analysis,
            'score': self._extract_score(analysis)
        }

    def _build_analysis_prompt(self, context: Dict) -> str:
        """构建分析提示"""
        stock_code = context.get('stock_code', 'N/A')
        kline = context.get('kline', {})
        realtime = context.get('realtime', {})

        return f"""请分析以下股票的技术面：

股票代码: {stock_code}

实时数据:
{self._format_realtime(realtime)}

K线数据:
{self._format_kline(kline)}

请从趋势、技术指标、支撑压力位三个维度进行分析，并给出综合评分（0-10分）。
"""

    def _format_realtime(self, realtime: Dict) -> str:
        """格式化实时数据"""
        if not realtime or 'error' in realtime:
            return "数据获取失败"

        return f"""
- 当前价格: {realtime.get('current_price', 'N/A')}
- 涨跌幅: {realtime.get('change_percent', 'N/A')}%
- 成交量: {realtime.get('volume', 'N/A')}
- 换手率: {realtime.get('turnover_rate', 'N/A')}%
"""

    def _format_kline(self, kline: Dict) -> str:
        """格式化K线数据"""
        if not kline or 'error' in kline:
            return "数据获取失败"

        # 简化版：只显示最近几天的数据
        return f"""
- 最近5日均价: {kline.get('ma5', 'N/A')}
- 最近20日均价: {kline.get('ma20', 'N/A')}
- MACD: {kline.get('macd', 'N/A')}
- RSI: {kline.get('rsi', 'N/A')}
"""

    def _extract_score(self, analysis: str) -> float:
        """从分析文本中提取评分"""
        import re
        match = re.search(r'评分[：:]\s*(\d+(?:\.\d+)?)', analysis)
        if match:
            return float(match.group(1))
        return 7.0
