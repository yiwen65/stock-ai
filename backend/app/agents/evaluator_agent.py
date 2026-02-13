"""Evaluator Agent - 综合评估 Agent"""

from typing import Dict
from app.agents.base_agent import BaseAgent


class EvaluatorAgent(BaseAgent):
    """综合评估 Agent"""

    def __init__(self, llm_service, name: str = "evaluator-agent"):
        super().__init__(llm_service, name)

    def _get_system_prompt(self) -> str:
        return """你是一个资深投资顾问。

你的任务是综合基本面和技术面分析，给出：
1. 综合评分（0-10分）
2. 风险等级（低/中/高）
3. 投资建议（买入/持有/观望/卖出）
4. 核心理由（3-5条）

请基于多维度分析给出客观、专业的投资建议。
"""

    async def execute(self, context: Dict) -> Dict:
        """执行综合评估"""
        prompt = f"""
股票代码: {context['stock_code']}

基本面分析:
{context['fundamental']['analysis']}
评分: {context['fundamental']['score']}/10

技术面分析:
{context['technical']['analysis']}
评分: {context['technical']['score']}/10

请给出综合评估。
"""

        evaluation = await self._call_llm(prompt)

        return {
            'overall_score': self._extract_score(evaluation),
            'risk_level': self._extract_risk_level(evaluation),
            'recommendation': self._extract_recommendation(evaluation),
            'summary': evaluation
        }

    def _extract_score(self, evaluation: str) -> float:
        """提取综合评分"""
        import re
        match = re.search(r'综合评分[：:]\s*(\d+(?:\.\d+)?)', evaluation)
        if match:
            return float(match.group(1))
        return 7.5

    def _extract_risk_level(self, evaluation: str) -> str:
        """提取风险等级"""
        if '低风险' in evaluation or '风险较低' in evaluation:
            return '低'
        elif '高风险' in evaluation or '风险较高' in evaluation:
            return '高'
        else:
            return '中'

    def _extract_recommendation(self, evaluation: str) -> str:
        """提取投资建议"""
        if '买入' in evaluation:
            return '买入'
        elif '卖出' in evaluation:
            return '卖出'
        elif '持有' in evaluation:
            return '持有'
        else:
            return '观望'
