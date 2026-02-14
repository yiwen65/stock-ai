"""News Agent - 消息面分析 Agent (PRD §4.5)"""

import logging
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class NewsAgent(BaseAgent):
    """消息面分析 Agent — 公告/新闻分类 + 影响判断"""

    def __init__(self, llm_service, name: str = "news-agent"):
        super().__init__(llm_service, name)

    def _get_system_prompt(self) -> str:
        return """你是一位专业的A股消息面分析师，擅长解读上市公司公告和新闻对股价的影响。

分析维度：
1. 公告/新闻分类：业绩相关、重大事项、股东变动、分红送转、风险提示、行业政策、其他
2. 影响判断：利好/利空/中性，影响程度（重大/一般/轻微）
3. 时效性：短期影响（1-5日）/中期影响（1-3月）/长期影响（3月以上）
4. 综合消息面评分

输出要求：
- 对每条重要消息给出分类和影响判断
- 综合所有消息给出消息面评分 (0-10)
- 判断消息面整体倾向（偏多/偏空/中性）
- 所有分析必须基于提供的数据

重要：消息面分析仅供参考，不构成投资建议。市场对消息的反应可能与分析不一致。"""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行消息面分析"""
        news_list = context.get("news", [])

        # No news available — return neutral result
        if not news_list:
            return {
                "agent": "news",
                "score": 5.0,
                "sentiment": "中性",
                "key_events": [],
                "summary": "暂无近期公告或新闻数据，消息面无法评估。",
                "analysis": "",
            }

        prompt = self._build_prompt(context)

        try:
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt},
            ]
            result = await self.llm_service.structured_output(messages)

            return {
                "agent": "news",
                "score": float(result.get("score", 5.0)),
                "sentiment": result.get("sentiment", "中性"),
                "key_events": result.get("key_events", []),
                "summary": result.get("summary", ""),
                "analysis": result.get("analysis", result.get("raw_response", "")),
            }
        except Exception as e:
            logger.error(f"NewsAgent error: {e}")
            return {
                "agent": "news",
                "score": 5.0,
                "sentiment": "中性",
                "key_events": [],
                "summary": f"消息面分析暂时无法完成: {e}",
                "analysis": "",
            }

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        stock_code = context.get("stock_code", "")
        stock_name = context.get("stock_name", stock_code)
        news_list: List[Dict] = context.get("news", [])
        realtime = context.get("realtime", {})

        lines = [f"请对 {stock_name}({stock_code}) 进行消息面分析。\n"]

        lines.append("【实时行情】")
        lines.append(f"- 最新价: {realtime.get('price', 'N/A')}")
        lines.append(f"- 涨跌幅: {realtime.get('pct_change', 'N/A')}%")
        lines.append("")

        lines.append(f"【近期新闻/公告（共{len(news_list)}条）】")
        for i, news in enumerate(news_list[:10], 1):
            title = news.get("title", "无标题")
            content = news.get("content", "")[:150]
            pub_time = news.get("publish_time", "")
            source = news.get("source", "")
            lines.append(f"{i}. [{pub_time}] {title}")
            if content:
                lines.append(f"   摘要: {content}")
            if source:
                lines.append(f"   来源: {source}")
            lines.append("")

        lines.append(
            "请返回 JSON，包含字段: "
            "score(消息面评分0-10), "
            "sentiment(偏多/偏空/中性), "
            "key_events(list of object, 每个包含 title/category/impact/impact_level, "
            "category为: 业绩相关/重大事项/股东变动/分红送转/风险提示/行业政策/其他, "
            "impact为: 利好/利空/中性, "
            "impact_level为: 重大/一般/轻微), "
            "summary(消息面综合分析，100字以内), "
            "analysis(详细分析，每条重要消息的解读)"
        )
        return "\n".join(lines)
