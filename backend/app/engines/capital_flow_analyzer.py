# backend/app/engines/capital_flow_analyzer.py

import pandas as pd
from typing import Dict, List
from app.schemas.analysis import CapitalFlowAnalysis


class CapitalFlowAnalyzer:
    """资金流向分析器 - 分析主力资金流向和趋势"""

    async def analyze(self, stock_code: str) -> CapitalFlowAnalysis:
        """
        资金流向分析

        Args:
            stock_code: 股票代码

        Returns:
            CapitalFlowAnalysis: 资金流向分析结果
        """
        # 获取资金流向数据（最近 20 天）
        flow_data = await self._get_capital_flow_data(stock_code, days=20)

        # 计算主力资金净流入
        main_net_inflow = flow_data['main_net'].sum()

        # 计算多时间维度净流入
        main_net_inflow_5d = flow_data['main_net'].tail(5).sum()
        main_net_inflow_10d = flow_data['main_net'].tail(10).sum()

        # 计算主力资金流入占比
        total_amount = flow_data['amount'].sum()
        main_inflow_ratio = main_net_inflow / total_amount if total_amount > 0 else 0

        # 判断趋势
        trend, score = self._analyze_trend(main_net_inflow_5d, main_inflow_ratio)

        # 生成总结
        summary = self._generate_summary(
            main_net_inflow, main_inflow_ratio, trend
        )

        return CapitalFlowAnalysis(
            score=score,
            main_net_inflow=main_net_inflow,
            main_net_inflow_5d=main_net_inflow_5d,
            main_net_inflow_10d=main_net_inflow_10d,
            main_inflow_ratio=main_inflow_ratio,
            trend=trend,
            summary=summary
        )

    def _analyze_trend(self, recent_5d: float, main_inflow_ratio: float) -> tuple:
        """
        分析资金流向趋势

        Args:
            recent_5d: 最近5天主力资金净流入
            main_inflow_ratio: 主力资金流入占比

        Returns:
            (trend, score): 趋势描述和评分
        """
        if recent_5d > 0 and main_inflow_ratio > 0.05:
            trend = "持续流入"
            score = 8.0
        elif recent_5d > 0:
            trend = "流入"
            score = 6.5
        elif recent_5d < 0 and main_inflow_ratio < -0.05:
            trend = "持续流出"
            score = 3.0
        elif recent_5d < 0:
            trend = "流出"
            score = 4.5
        else:
            trend = "平衡"
            score = 5.0

        return trend, score

    def _generate_summary(
        self,
        main_net_inflow: float,
        main_inflow_ratio: float,
        trend: str
    ) -> str:
        """
        生成资金面分析总结

        Args:
            main_net_inflow: 主力资金净流入
            main_inflow_ratio: 主力资金流入占比
            trend: 资金流向趋势

        Returns:
            分析总结文本
        """
        # 格式化金额（转换为万元或亿元）
        if abs(main_net_inflow) >= 100000000:  # 1亿
            amount_str = f"{main_net_inflow / 100000000:.2f}亿元"
        else:
            amount_str = f"{main_net_inflow / 10000:.2f}万元"

        # 格式化占比
        ratio_str = f"{main_inflow_ratio * 100:.2f}%"

        # 生成总结
        if trend == "持续流入":
            return f"主力资金{trend}，净流入{amount_str}，占比{ratio_str}，资金面强势"
        elif trend == "流入":
            return f"主力资金{trend}，净流入{amount_str}，占比{ratio_str}，资金面良好"
        elif trend == "持续流出":
            return f"主力资金{trend}，净流出{amount_str}，占比{ratio_str}，资金面疲弱"
        elif trend == "流出":
            return f"主力资金{trend}，净流出{amount_str}，占比{ratio_str}，资金面偏弱"
        else:
            return f"主力资金{trend}，净流入{amount_str}，占比{ratio_str}，资金面中性"

    async def _get_capital_flow_data(
        self,
        stock_code: str,
        days: int = 20
    ) -> pd.DataFrame:
        """
        获取资金流向数据（TODO: 实现数据获取）

        Args:
            stock_code: 股票代码
            days: 天数

        Returns:
            资金流向数据 DataFrame
        """
        # 临时返回模拟数据
        import numpy as np

        dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='D')
        np.random.seed(42)

        # 模拟主力资金净流入（有正有负）
        main_net = np.random.randn(days) * 10000000  # 随机正负值

        # 模拟总成交额
        amount = np.random.uniform(50000000, 200000000, days)

        return pd.DataFrame({
            'date': dates,
            'main_net': main_net,  # 主力资金净流入
            'amount': amount,  # 总成交额
            'main_inflow': np.abs(main_net) * 0.6,  # 主力流入
            'main_outflow': np.abs(main_net) * 0.4  # 主力流出
        })
