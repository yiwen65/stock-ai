"""Fundamental Agent - 基本面分析 Agent"""

from typing import Dict
from app.agents.base_agent import BaseAgent


class FundamentalAgent(BaseAgent):
    """基本面分析 Agent"""

    def __init__(self, llm_service, name: str = "fundamental-agent"):
        super().__init__(llm_service, name)

    def _get_system_prompt(self) -> str:
        return """你是一个专业的基本面分析师。

你的任务是分析股票的基本面，包括：
1. 估值水平（PE、PB、PS）
2. 盈利能力（ROE、ROA、净利率）
3. 成长性（营收增长、利润增长）
4. 财务健康（负债率、流动比率、现金流）

请给出：
- 各维度评分（0-10分）
- 优势和风险点
- 投资建议
"""

    async def execute(self, context: Dict) -> Dict:
        """执行基本面分析"""
        # 构建分析提示
        prompt = self._build_analysis_prompt(context)

        # 调用 LLM 分析
        analysis = await self._call_llm(prompt)

        return {
            'agent': 'fundamental',
            'analysis': analysis,
            'score': self._extract_score(analysis)
        }

    def _build_analysis_prompt(self, context: Dict) -> str:
        """构建分析提示"""
        stock_code = context.get('stock_code', 'N/A')
        financial = context.get('financial', {})
        realtime = context.get('realtime', {})

        return f"""请分析以下股票的基本面：

股票代码: {stock_code}

实时数据:
{self._format_realtime(realtime)}

财务数据:
{self._format_financial(financial)}

请从估值、盈利能力、成长性、财务健康四个维度进行分析，并给出综合评分（0-10分）。
"""

    def _format_realtime(self, realtime: Dict) -> str:
        """格式化实时数据"""
        if not realtime or 'error' in realtime:
            return "数据获取失败"

        return f"""
- 当前价格: {realtime.get('current_price', 'N/A')}
- 市盈率(PE): {realtime.get('pe', 'N/A')}
- 市净率(PB): {realtime.get('pb', 'N/A')}
- 总市值: {realtime.get('market_cap', 'N/A')}
"""

    def _format_financial(self, financial: Dict) -> str:
        """格式化财务数据"""
        if not financial or 'error' in financial:
            return "数据获取失败"

        return f"""
- ROE: {financial.get('roe', 'N/A')}
- ROA: {financial.get('roa', 'N/A')}
- 净利率: {financial.get('net_margin', 'N/A')}
- 营收增长率: {financial.get('revenue_growth', 'N/A')}
- 净利润增长率: {financial.get('profit_growth', 'N/A')}
- 资产负债率: {financial.get('debt_ratio', 'N/A')}
"""

    def _extract_score(self, analysis: str) -> float:
        """从分析文本中提取评分"""
        # 简化版：查找评分关键词
        import re
        match = re.search(r'评分[：:]\s*(\d+(?:\.\d+)?)', analysis)
        if match:
            return float(match.group(1))

        # 默认评分
        return 7.0
