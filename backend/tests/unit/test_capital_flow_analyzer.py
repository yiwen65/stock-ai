# backend/tests/unit/test_capital_flow_analyzer.py

import pytest
import pandas as pd
import numpy as np
from app.engines.capital_flow_analyzer import CapitalFlowAnalyzer
from app.schemas.analysis import CapitalFlowAnalysis


@pytest.fixture
def analyzer():
    """Create CapitalFlowAnalyzer instance"""
    return CapitalFlowAnalyzer()


@pytest.mark.asyncio
async def test_analyze_returns_capital_flow_analysis(analyzer):
    """Test that analyze returns a valid CapitalFlowAnalysis"""
    stock_code = "600519"

    result = await analyzer.analyze(stock_code)

    assert isinstance(result, CapitalFlowAnalysis)
    assert 0 <= result.score <= 10
    assert result.trend in ["持续流入", "流入", "平衡", "流出", "持续流出"]
    assert isinstance(result.main_net_inflow, float)
    assert isinstance(result.main_inflow_ratio, float)
    assert result.summary is not None


def test_analyze_trend_continuous_inflow(analyzer):
    """Test trend analysis for continuous inflow"""
    trend, score = analyzer._analyze_trend(50000000, 0.08)

    assert trend == "持续流入"
    assert score == 8.0


def test_analyze_trend_inflow(analyzer):
    """Test trend analysis for inflow"""
    trend, score = analyzer._analyze_trend(10000000, 0.03)

    assert trend == "流入"
    assert score == 6.5


def test_analyze_trend_continuous_outflow(analyzer):
    """Test trend analysis for continuous outflow"""
    trend, score = analyzer._analyze_trend(-50000000, -0.08)

    assert trend == "持续流出"
    assert score == 3.0


def test_analyze_trend_outflow(analyzer):
    """Test trend analysis for outflow"""
    trend, score = analyzer._analyze_trend(-10000000, -0.03)

    assert trend == "流出"
    assert score == 4.5


def test_analyze_trend_balanced(analyzer):
    """Test trend analysis for balanced flow"""
    trend, score = analyzer._analyze_trend(0, 0)

    assert trend == "平衡"
    assert score == 5.0


def test_generate_summary_continuous_inflow(analyzer):
    """Test summary generation for continuous inflow"""
    summary = analyzer._generate_summary(150000000, 0.08, "持续流入")

    assert "持续流入" in summary
    assert "1.50亿元" in summary
    assert "8.00%" in summary
    assert "强势" in summary


def test_generate_summary_inflow(analyzer):
    """Test summary generation for inflow"""
    summary = analyzer._generate_summary(50000000, 0.03, "流入")

    assert "流入" in summary
    assert "5000.00万元" in summary
    assert "3.00%" in summary
    assert "良好" in summary


def test_generate_summary_continuous_outflow(analyzer):
    """Test summary generation for continuous outflow"""
    summary = analyzer._generate_summary(-150000000, -0.08, "持续流出")

    assert "持续流出" in summary
    assert "1.50亿元" in summary
    assert "8.00%" in summary
    assert "疲弱" in summary


def test_generate_summary_outflow(analyzer):
    """Test summary generation for outflow"""
    summary = analyzer._generate_summary(-50000000, -0.03, "流出")

    assert "流出" in summary
    assert "5000.00万元" in summary
    assert "3.00%" in summary
    assert "偏弱" in summary


def test_generate_summary_balanced(analyzer):
    """Test summary generation for balanced flow"""
    summary = analyzer._generate_summary(5000000, 0.01, "平衡")

    assert "平衡" in summary
    assert "500.00万元" in summary
    assert "1.00%" in summary
    assert "中性" in summary


def test_generate_summary_large_amount(analyzer):
    """Test summary generation with large amount (in 亿元)"""
    summary = analyzer._generate_summary(500000000, 0.10, "持续流入")

    assert "5.00亿元" in summary


def test_generate_summary_small_amount(analyzer):
    """Test summary generation with small amount (in 万元)"""
    summary = analyzer._generate_summary(50000000, 0.05, "流入")

    assert "5000.00万元" in summary


@pytest.mark.asyncio
async def test_get_capital_flow_data_structure(analyzer):
    """Test that capital flow data has correct structure"""
    stock_code = "600519"

    data = await analyzer._get_capital_flow_data(stock_code, days=20)

    assert isinstance(data, pd.DataFrame)
    assert len(data) == 20
    assert 'date' in data.columns
    assert 'main_net' in data.columns
    assert 'amount' in data.columns
    assert 'main_inflow' in data.columns
    assert 'main_outflow' in data.columns
