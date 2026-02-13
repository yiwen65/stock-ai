# backend/app/engines/technical_analyzer.py

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from app.schemas.analysis import TechnicalAnalysis
from app.utils.indicators import (
    calculate_ma,
    calculate_macd,
    calculate_rsi,
    calculate_kdj,
    calculate_boll
)


class TechnicalAnalyzer:
    """技术面分析器 - 分析趋势、动量、支撑压力位"""

    async def analyze(self, stock_code: str) -> TechnicalAnalysis:
        """
        综合技术面分析

        Args:
            stock_code: 股票代码

        Returns:
            TechnicalAnalysis: 技术面分析结果
        """
        # 获取 K 线数据（90 天）
        kline_data = await self._get_kline_data(stock_code, period='1d', days=90)

        # 趋势分析
        trend_result = await self.analyze_trend(kline_data)

        # 动量分析
        momentum_result = await self.analyze_momentum(kline_data)

        # 支撑压力位
        levels = await self.find_support_resistance(kline_data)

        # 综合评分
        score = (
            trend_result['score'] * 0.5 +
            momentum_result['score'] * 0.5
        )

        # 生成总结
        summary = self._generate_summary(trend_result, momentum_result, levels)

        return TechnicalAnalysis(
            score=round(score, 2),
            trend=trend_result['trend'],
            support_levels=levels['support_levels'],
            resistance_levels=levels['resistance_levels'],
            indicators={
                'ma': self._serialize_ma_data(trend_result['ma_data']),
                'macd': self._serialize_indicator(momentum_result['macd']),
                'rsi': self._serialize_indicator(momentum_result['rsi']),
                'kdj': self._serialize_indicator(momentum_result['kdj'])
            },
            summary=summary
        )

    async def analyze_trend(self, kline_data: pd.DataFrame) -> Dict:
        """
        趋势分析

        Args:
            kline_data: K 线数据

        Returns:
            趋势分析结果
        """
        close = kline_data['close']

        # 计算均线
        ma_data = calculate_ma(close, [5, 10, 20, 60])

        # 判断趋势
        ma5 = ma_data['ma5'].iloc[-1]
        ma10 = ma_data['ma10'].iloc[-1]
        ma20 = ma_data['ma20'].iloc[-1]
        ma60 = ma_data['ma60'].iloc[-1]

        # 多头排列：短期均线 > 中期均线 > 长期均线
        if ma5 > ma10 > ma20 > ma60:
            trend = "强势上涨"
            trend_score = 9.0
        elif ma5 > ma10 > ma20:
            trend = "上涨"
            trend_score = 7.0
        elif ma5 < ma10 < ma20 < ma60:
            trend = "强势下跌"
            trend_score = 2.0
        elif ma5 < ma10 < ma20:
            trend = "下跌"
            trend_score = 4.0
        else:
            trend = "震荡"
            trend_score = 5.0

        return {
            'trend': trend,
            'score': trend_score,
            'ma_data': ma_data
        }

    async def analyze_momentum(self, kline_data: pd.DataFrame) -> Dict:
        """
        动量分析

        Args:
            kline_data: K 线数据

        Returns:
            动量分析结果
        """
        close = kline_data['close']
        high = kline_data['high']
        low = kline_data['low']

        # MACD
        macd_data = calculate_macd(close)
        macd_signal = self._interpret_macd(macd_data)

        # RSI
        rsi_data = calculate_rsi(close, [6, 12, 24])
        rsi_signal = self._interpret_rsi(rsi_data)

        # KDJ
        kdj_data = calculate_kdj(high, low, close)
        kdj_signal = self._interpret_kdj(kdj_data)

        # 综合评分
        momentum_score = (
            macd_signal['score'] * 0.4 +
            rsi_signal['score'] * 0.3 +
            kdj_signal['score'] * 0.3
        )

        return {
            'macd': macd_data,
            'rsi': rsi_data,
            'kdj': kdj_data,
            'score': momentum_score
        }

    async def find_support_resistance(self, kline_data: pd.DataFrame) -> Dict:
        """
        寻找支撑位和压力位

        Args:
            kline_data: K 线数据

        Returns:
            支撑位和压力位列表
        """
        high = kline_data['high']
        low = kline_data['low']

        # 使用局部极值点
        support_levels = self._find_local_minima(low)
        resistance_levels = self._find_local_maxima(high)

        return {
            'support_levels': support_levels[:3],  # 前3个支撑位
            'resistance_levels': resistance_levels[:3]  # 前3个压力位
        }

    def _interpret_macd(self, macd_data: Dict[str, pd.Series]) -> Dict:
        """
        解读 MACD 信号

        Args:
            macd_data: MACD 数据

        Returns:
            MACD 信号和评分
        """
        dif = macd_data['dif'].iloc[-1]
        dea = macd_data['dea'].iloc[-1]
        bar = macd_data['bar'].iloc[-1]

        # 金叉：DIF 上穿 DEA
        if dif > dea and bar > 0:
            if dif > 0 and dea > 0:
                signal = "强势金叉"
                score = 9.0
            else:
                signal = "金叉"
                score = 7.0
        # 死叉：DIF 下穿 DEA
        elif dif < dea and bar < 0:
            if dif < 0 and dea < 0:
                signal = "强势死叉"
                score = 2.0
            else:
                signal = "死叉"
                score = 4.0
        else:
            signal = "中性"
            score = 5.0

        return {
            'signal': signal,
            'score': score
        }

    def _interpret_rsi(self, rsi_data: Dict[str, pd.Series]) -> Dict:
        """
        解读 RSI 信号

        Args:
            rsi_data: RSI 数据

        Returns:
            RSI 信号和评分
        """
        rsi6 = rsi_data['rsi6'].iloc[-1]

        # RSI 超买超卖判断
        if rsi6 >= 80:
            signal = "严重超买"
            score = 3.0
        elif rsi6 >= 70:
            signal = "超买"
            score = 4.0
        elif rsi6 >= 50:
            signal = "强势"
            score = 7.0
        elif rsi6 >= 30:
            signal = "弱势"
            score = 4.0
        elif rsi6 >= 20:
            signal = "超卖"
            score = 6.0
        else:
            signal = "严重超卖"
            score = 7.0

        return {
            'signal': signal,
            'score': score
        }

    def _interpret_kdj(self, kdj_data: Dict[str, pd.Series]) -> Dict:
        """
        解读 KDJ 信号

        Args:
            kdj_data: KDJ 数据

        Returns:
            KDJ 信号和评分
        """
        k = kdj_data['k'].iloc[-1]
        d = kdj_data['d'].iloc[-1]
        j = kdj_data['j'].iloc[-1]

        # KDJ 金叉死叉判断
        if k > d and j > k:
            if k > 50:
                signal = "强势金叉"
                score = 8.0
            else:
                signal = "金叉"
                score = 7.0
        elif k < d and j < k:
            if k < 50:
                signal = "强势死叉"
                score = 3.0
            else:
                signal = "死叉"
                score = 4.0
        else:
            # 超买超卖判断
            if k >= 80:
                signal = "超买"
                score = 4.0
            elif k <= 20:
                signal = "超卖"
                score = 6.0
            else:
                signal = "中性"
                score = 5.0

        return {
            'signal': signal,
            'score': score
        }

    def _find_local_minima(self, series: pd.Series, window: int = 5) -> List[float]:
        """
        寻找局部最小值（支撑位）

        Args:
            series: 价格序列
            window: 窗口大小

        Returns:
            支撑位列表（降序）
        """
        minima = []

        for i in range(window, len(series) - window):
            if series.iloc[i] == series.iloc[i - window:i + window + 1].min():
                minima.append(float(series.iloc[i]))

        # 去重并降序排列
        minima = sorted(list(set(minima)), reverse=True)

        return minima

    def _find_local_maxima(self, series: pd.Series, window: int = 5) -> List[float]:
        """
        寻找局部最大值（压力位）

        Args:
            series: 价格序列
            window: 窗口大小

        Returns:
            压力位列表（升序）
        """
        maxima = []

        for i in range(window, len(series) - window):
            if series.iloc[i] == series.iloc[i - window:i + window + 1].max():
                maxima.append(float(series.iloc[i]))

        # 去重并升序排列
        maxima = sorted(list(set(maxima)))

        return maxima

    def _generate_summary(
        self,
        trend_result: Dict,
        momentum_result: Dict,
        levels: Dict
    ) -> str:
        """生成技术面分析总结"""
        parts = []

        # 趋势总结
        trend = trend_result['trend']
        parts.append(f"趋势{trend}")

        # 动量总结
        if momentum_result['score'] >= 7:
            parts.append("动量强劲")
        elif momentum_result['score'] >= 5:
            parts.append("动量中性")
        else:
            parts.append("动量疲弱")

        # 支撑压力位总结
        if levels['support_levels']:
            support = levels['support_levels'][0]
            parts.append(f"关键支撑位 {support:.2f}")

        if levels['resistance_levels']:
            resistance = levels['resistance_levels'][-1]
            parts.append(f"关键压力位 {resistance:.2f}")

        return "，".join(parts)

    def _serialize_ma_data(self, ma_data: Dict[str, pd.Series]) -> Dict[str, float]:
        """序列化均线数据（取最新值）"""
        return {
            key: float(series.iloc[-1]) if not pd.isna(series.iloc[-1]) else 0.0
            for key, series in ma_data.items()
        }

    def _serialize_indicator(self, indicator_data: Dict[str, pd.Series]) -> Dict[str, float]:
        """序列化指标数据（取最新值）"""
        return {
            key: float(series.iloc[-1]) if not pd.isna(series.iloc[-1]) else 0.0
            for key, series in indicator_data.items()
        }

    async def _get_kline_data(
        self,
        stock_code: str,
        period: str = '1d',
        days: int = 90
    ) -> pd.DataFrame:
        """
        获取 K 线数据（TODO: 实现数据获取）

        Args:
            stock_code: 股票代码
            period: 周期
            days: 天数

        Returns:
            K 线数据 DataFrame
        """
        # 临时返回模拟数据
        dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='D')
        np.random.seed(42)

        base_price = 100.0
        prices = base_price + np.cumsum(np.random.randn(days) * 2)

        return pd.DataFrame({
            'date': dates,
            'open': prices + np.random.randn(days) * 0.5,
            'high': prices + np.abs(np.random.randn(days) * 1.5),
            'low': prices - np.abs(np.random.randn(days) * 1.5),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, days)
        })
