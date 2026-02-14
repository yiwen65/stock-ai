"""策略解析引擎 — 支持技术/资金/事件字段 + OR/NOT 逻辑"""

import logging
from typing import Dict, List
from app.services.llm_service import LLMService
from app.schemas.strategy_parse import StrategyParseResponse, ParsedCondition

logger = logging.getLogger(__name__)

# All valid fields that the stock filter can handle
VALID_FIELDS = {
    # 估值
    'pe', 'pb', 'ps',
    # 盈利
    'roe', 'roa', 'eps', 'net_margin', 'gross_margin',
    # 成长
    'revenue_growth', 'profit_growth', 'net_profit_growth',
    # 财务健康
    'debt_ratio', 'current_ratio',
    # 市值 / 行情
    'market_cap', 'circulating_market_cap', 'price',
    'pct_change', 'turnover_rate', 'volume_ratio', 'amplitude',
    'change_60d', 'change_ytd',
    # 技术指标 (需要由后续引擎计算)
    'rsi', 'macd_dif', 'macd_dea', 'kdj_k', 'kdj_d',
    'ma5', 'ma10', 'ma20', 'ma60',
    # 资金面
    'main_net_inflow', 'main_net_inflow_5d', 'main_net_inflow_pct',
    # 事件 / 标签
    'dividend_yield',
}

FIELD_NAMES_CN = {
    'pe': '市盈率', 'pb': '市净率', 'ps': '市销率',
    'roe': '净资产收益率', 'roa': '总资产收益率', 'eps': '每股收益',
    'net_margin': '净利率', 'gross_margin': '毛利率',
    'revenue_growth': '营收增长率', 'profit_growth': '净利润增长率',
    'net_profit_growth': '净利润增长率',
    'debt_ratio': '资产负债率', 'current_ratio': '流动比率',
    'market_cap': '总市值(元)', 'circulating_market_cap': '流通市值(元)',
    'price': '股价', 'pct_change': '涨跌幅%', 'turnover_rate': '换手率%',
    'volume_ratio': '量比', 'amplitude': '振幅%',
    'change_60d': '60日涨跌幅%', 'change_ytd': '年初至今涨跌幅%',
    'rsi': 'RSI(14)', 'macd_dif': 'MACD DIF', 'macd_dea': 'MACD DEA',
    'kdj_k': 'KDJ K值', 'kdj_d': 'KDJ D值',
    'ma5': '5日均线', 'ma10': '10日均线', 'ma20': '20日均线', 'ma60': '60日均线',
    'main_net_inflow': '当日主力净流入(元)', 'main_net_inflow_5d': '5日主力净流入(元)',
    'main_net_inflow_pct': '主力净流入占比%',
    'dividend_yield': '股息率%',
}


class StrategyParser:
    """策略解析引擎 — 支持技术/资金字段 + OR/NOT 逻辑"""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def parse(self, description: str) -> StrategyParseResponse:
        """解析自然语言策略描述"""
        prompt = self._build_parse_prompt(description)

        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_service.structured_output(messages=messages)

        parsed = self._validate_and_convert(response)
        conflicts = self._detect_conflicts(parsed['conditions'])

        # Warn if too many conditions (likely over-filtering)
        if len(parsed['conditions']) > 8:
            conflicts.append("条件数量较多(>8)，可能导致筛选结果过少")

        return StrategyParseResponse(
            conditions=[ParsedCondition(**c) for c in parsed['conditions']],
            logic=parsed.get('logic', 'AND'),
            conflicts=conflicts,
            confidence=parsed.get('confidence', 0.8),
            summary=parsed.get('summary', '')
        )

    def _get_system_prompt(self) -> str:
        fields_desc = "\n".join(f"  - {k}: {v}" for k, v in FIELD_NAMES_CN.items())
        return f"""你是一个专业的A股选股策略解析助手。

你的任务是将用户的自然语言描述转换为结构化的选股条件。

【支持的字段】
{fields_desc}

【支持的运算符】
  <, >, <=, >=, ==, between

【支持的逻辑】
  AND — 所有条件同时满足（默认）
  OR  — 满足任一条件即可
  用户说"或者"/"或"时用 OR，否则用 AND

【模糊表达理解示例】
  "便宜的好公司" → pe < 20, roe > 15, debt_ratio < 50
  "大盘蓝筹" → market_cap > 50000000000 (500亿)
  "小盘成长" → market_cap < 10000000000, revenue_growth > 20
  "资金追捧" → main_net_inflow > 0, turnover_rate > 3
  "超跌反弹" → change_60d < -30, rsi < 30
  "放量上涨" → pct_change > 2, volume_ratio > 2
  "高股息" → dividend_yield > 3

【市值单位】
  市值字段的值单位是"元"，注意：1亿 = 100000000

【输出 JSON 格式】
{{
  "conditions": [
    {{"field": "pe", "operator": "<", "value": 15, "description": "市盈率小于15"}},
    ...
  ],
  "logic": "AND",
  "confidence": 0.9,
  "summary": "寻找低估值、高盈利的价值股"
}}

【注意事项】
  - field 必须是上面列出的英文字段名之一
  - 如果用户的描述无法映射到任何字段，设 confidence 为低值并在 summary 中说明
  - between 运算符的 value 为 [min, max] 数组"""

    def _build_parse_prompt(self, description: str) -> str:
        return f"""请解析以下选股策略描述，转换为结构化筛选条件：

"{description}"

请输出 JSON 格式的结构化条件。"""

    def _validate_and_convert(self, response: Dict) -> Dict:
        """验证和转换 LLM 输出"""
        conditions = response.get('conditions', [])
        valid_conditions = []

        for cond in conditions:
            field = cond.get('field', '')
            if field in VALID_FIELDS:
                valid_conditions.append(cond)
            else:
                # Try fuzzy match
                matched = self._fuzzy_match_field(field)
                if matched:
                    cond['field'] = matched
                    valid_conditions.append(cond)
                else:
                    logger.warning(f"Dropping unknown field from NL parse: {field}")

        response['conditions'] = valid_conditions
        return response

    @staticmethod
    def _fuzzy_match_field(field: str) -> str:
        """Try to fuzzy-match a field name to a valid field."""
        aliases = {
            '市盈率': 'pe', 'pe_ttm': 'pe', 'pe_ratio': 'pe',
            '市净率': 'pb', 'pb_ratio': 'pb',
            '市销率': 'ps',
            'roe': 'roe', '净资产收益率': 'roe',
            'roa': 'roa',
            '净利率': 'net_margin', '净利润率': 'net_margin',
            '毛利率': 'gross_margin',
            '营收增长': 'revenue_growth', '营收增长率': 'revenue_growth',
            '净利润增长': 'net_profit_growth', '利润增长': 'net_profit_growth',
            'profit_growth_rate': 'profit_growth',
            '负债率': 'debt_ratio', '资产负债率': 'debt_ratio',
            '流动比率': 'current_ratio',
            '总市值': 'market_cap', '市值': 'market_cap',
            '流通市值': 'circulating_market_cap',
            '股价': 'price', '价格': 'price',
            '涨跌幅': 'pct_change', '涨幅': 'pct_change',
            '换手率': 'turnover_rate',
            '量比': 'volume_ratio',
            '振幅': 'amplitude',
            'rsi': 'rsi', 'RSI': 'rsi',
            '主力净流入': 'main_net_inflow',
            '股息率': 'dividend_yield', '分红率': 'dividend_yield',
        }
        return aliases.get(field, aliases.get(field.lower(), ''))

    def _detect_conflicts(self, conditions: List[Dict]) -> List[str]:
        """检测逻辑冲突"""
        conflicts = []

        field_conditions: Dict[str, List[Dict]] = {}
        for cond in conditions:
            field = cond.get('field', '')
            field_conditions.setdefault(field, []).append(cond)

        for field, conds in field_conditions.items():
            if len(conds) > 1 and self._has_range_conflict(conds):
                cn = FIELD_NAMES_CN.get(field, field)
                conflicts.append(f"{cn}({field}) 存在范围冲突")

        return conflicts

    @staticmethod
    def _has_range_conflict(conditions: List[Dict]) -> bool:
        """Check if < and > conditions conflict (e.g. pe < 10 AND pe > 20)."""
        lt_vals = [c['value'] for c in conditions if c.get('operator') in ('<', '<=')]
        gt_vals = [c['value'] for c in conditions if c.get('operator') in ('>', '>=')]

        if lt_vals and gt_vals:
            return max(gt_vals) >= min(lt_vals)
        return False
