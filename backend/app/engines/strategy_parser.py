"""策略解析引擎"""

from typing import Dict, List
from app.services.llm_service import LLMService
from app.schemas.strategy_parse import StrategyParseResponse, ParsedCondition


class StrategyParser:
    """策略解析引擎"""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def parse(self, description: str) -> StrategyParseResponse:
        """解析自然语言策略描述"""
        # 1. 构建 Prompt
        prompt = self._build_parse_prompt(description)

        # 2. 调用 LLM
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_service.structured_output(
            messages=messages,
            response_format={"type": "json_object"}
        )

        # 3. 验证和转换
        parsed = self._validate_and_convert(response)

        # 4. 检测逻辑冲突
        conflicts = self._detect_conflicts(parsed['conditions'])

        return StrategyParseResponse(
            conditions=[ParsedCondition(**c) for c in parsed['conditions']],
            logic=parsed['logic'],
            conflicts=conflicts,
            confidence=parsed.get('confidence', 0.8),
            summary=parsed.get('summary', '')
        )

    def _get_system_prompt(self) -> str:
        """系统提示词"""
        return """你是一个专业的A股选股策略解析助手。

你的任务是将用户的自然语言描述转换为结构化的选股条件。

支持的字段：
- 估值指标: pe (市盈率), pb (市净率), ps (市销率)
- 盈利指标: roe (净资产收益率), roa (总资产收益率), net_margin (净利率)
- 成长指标: revenue_growth (营收增长率), profit_growth (净利润增长率)
- 财务健康: debt_ratio (资产负债率), current_ratio (流动比率)
- 市值: market_cap (总市值)

支持的运算符: <, >, <=, >=, ==, between

输出 JSON 格式：
{
  "conditions": [
    {"field": "pe", "operator": "<", "value": 15, "description": "市盈率小于15"},
    ...
  ],
  "logic": "AND",
  "confidence": 0.9,
  "summary": "寻找低估值、高盈利的价值股"
}
"""

    def _build_parse_prompt(self, description: str) -> str:
        """构建解析提示"""
        return f"""请解析以下选股策略描述：

"{description}"

请输出结构化的筛选条件。"""

    def _validate_and_convert(self, response: Dict) -> Dict:
        """验证和转换 LLM 输出"""
        # 验证字段合法性
        valid_fields = {
            'pe', 'pb', 'ps', 'roe', 'roa', 'net_margin',
            'revenue_growth', 'profit_growth', 'debt_ratio',
            'current_ratio', 'market_cap'
        }

        for condition in response['conditions']:
            if condition['field'] not in valid_fields:
                raise ValueError(f"Invalid field: {condition['field']}")

        return response

    def _detect_conflicts(self, conditions: List[Dict]) -> List[str]:
        """检测逻辑冲突"""
        conflicts = []

        # 检测同一字段的冲突条件
        field_conditions = {}
        for cond in conditions:
            field = cond['field']
            if field not in field_conditions:
                field_conditions[field] = []
            field_conditions[field].append(cond)

        for field, conds in field_conditions.items():
            if len(conds) > 1:
                # 检查是否有冲突（如 pe < 10 且 pe > 20）
                if self._has_conflict(conds):
                    conflicts.append(f"{field} 存在冲突条件")

        return conflicts

    def _has_conflict(self, conditions: List[Dict]) -> bool:
        """检查条件是否冲突"""
        # 简化版：检查 < 和 > 的冲突
        has_lt = any(c['operator'] in ['<', '<='] for c in conditions)
        has_gt = any(c['operator'] in ['>', '>='] for c in conditions)

        if has_lt and has_gt:
            lt_val = next(c['value'] for c in conditions if c['operator'] in ['<', '<='])
            gt_val = next(c['value'] for c in conditions if c['operator'] in ['>', '>='])
            return gt_val >= lt_val

        return False
