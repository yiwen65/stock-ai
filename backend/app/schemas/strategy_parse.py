"""策略解析相关 Schema"""

from pydantic import BaseModel
from typing import List, Optional


class StrategyParseRequest(BaseModel):
    """策略解析请求"""
    description: str  # 用户的自然语言描述


class ParsedCondition(BaseModel):
    """解析后的条件"""
    field: str
    operator: str
    value: float | List[float]
    description: str  # 条件的中文描述


class StrategyParseResponse(BaseModel):
    """策略解析响应"""
    conditions: List[ParsedCondition]
    logic: str  # "AND" or "OR"
    conflicts: List[str]  # 逻辑冲突提示
    confidence: float  # 解析置信度 (0-1)
    summary: str  # 策略总结
