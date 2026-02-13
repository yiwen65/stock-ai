# Phase 2: 个股分析引擎

**优先级**: 🔴 高
**状态**: ⬜ 待开始
**预计工作量**: 大
**依赖**: Phase 1C 完成

---

## 任务清单

### ⬜ Task 1: 分析引擎架构设计
**状态**: 待开始
**文件**:
- 创建: `backend/app/engines/analyzer.py`
- 创建: `backend/app/schemas/analysis.py`
- 创建: `backend/tests/unit/test_analyzer.py`

**步骤**:

1. **设计分析报告 Schema**
   ```python
   # backend/app/schemas/analysis.py

   from pydantic import BaseModel, Field
   from typing import Optional, Dict, List

   class FundamentalAnalysis(BaseModel):
       score: float = Field(..., ge=0, le=10)
       valuation: Dict[str, float]  # PE, PB, PS
       profitability: Dict[str, float]  # ROE, ROA, net_margin
       growth: Dict[str, float]  # revenue_growth, profit_growth
       financial_health: Dict[str, float]  # debt_ratio, current_ratio
       summary: str

   class TechnicalAnalysis(BaseModel):
       score: float = Field(..., ge=0, le=10)
       trend: str  # "上涨", "下跌", "震荡"
       support_levels: List[float]
       resistance_levels: List[float]
       indicators: Dict[str, any]  # MA, MACD, RSI, KDJ
       summary: str

   class CapitalFlowAnalysis(BaseModel):
       score: float = Field(..., ge=0, le=10)
       main_net_inflow: float
       main_inflow_ratio: float
       trend: str  # "流入", "流出", "平衡"
       summary: str

   class AnalysisReport(BaseModel):
       stock_code: str
       stock_name: str
       fundamental: FundamentalAnalysis
       technical: TechnicalAnalysis
       capital_flow: CapitalFlowAnalysis
       overall_score: float = Field(..., ge=0, le=10)
       risk_level: str  # "low", "medium", "high"
       recommendation: str  # "buy", "hold", "watch", "sell"
       summary: str
       generated_at: int
   ```

2. **实现分析引擎框架**
   ```python
   # backend/app/engines/analyzer.py

   class StockAnalyzer:
       def __init__(self, db: Session, cache: Redis):
           self.db = db
           self.cache = cache

       async def analyze(
           self,
           stock_code: str,
           report_type: str = 'comprehensive',
           force_refresh: bool = False
       ) -> AnalysisReport:
           # 1. 检查缓存
           cache_key = f"analysis:report:{stock_code}"
           if not force_refresh:
               cached = await self.cache.get(cache_key)
               if cached:
                   return AnalysisReport(**json.loads(cached))

           # 2. 获取数据
           data = await self._fetch_analysis_data(stock_code)

           # 3. 执行分析
           fundamental = await self._analyze_fundamental(data)
           technical = await self._analyze_technical(data)
           capital_flow = await self._analyze_capital_flow(data)

           # 4. 综合评分
           overall_score = self._calculate_overall_score(
               fundamental, technical, capital_flow
           )

           # 5. 生成报告
           report = AnalysisReport(
               stock_code=stock_code,
               stock_name=data['stock_name'],
               fundamental=fundamental,
               technical=technical,
               capital_flow=capital_flow,
               overall_score=overall_score,
               risk_level=self._assess_risk(overall_score),
               recommendation=self._generate_recommendation(overall_score),
               summary=self._generate_summary(fundamental, technical, capital_flow),
               generated_at=int(time.time())
           )

           # 6. 缓存结果
           await self.cache.setex(cache_key, 3600, report.json())

           return report
   ```

3. **提交代码**
   ```bash
   git add backend/app/engines/analyzer.py backend/app/schemas/analysis.py
   git commit -m "feat: add stock analyzer engine architecture"
   ```

---

### ⬜ Task 2: 基本面分析模块
**状态**: 待开始
**文件**:
- 创建: `backend/app/engines/fundamental_analyzer.py`
- 创建: `backend/tests/unit/test_fundamental_analyzer.py`

**步骤**:

1. **实现估值分析**
   ```python
   # backend/app/engines/fundamental_analyzer.py

   class FundamentalAnalyzer:
       async def analyze_valuation(self, stock_data: Dict) -> Dict:
           """估值分析"""
           pe = stock_data.get('pe_ttm')
           pb = stock_data.get('pb')
           ps = stock_data.get('ps')

           # 行业平均对比
           industry_avg_pe = await self._get_industry_avg_pe(stock_data['industry'])

           valuation_score = self._calculate_valuation_score(
               pe, pb, ps, industry_avg_pe
           )

           return {
               'pe_ttm': pe,
               'pb': pb,
               'ps': ps,
               'industry_avg_pe': industry_avg_pe,
               'pe_percentile': self._calculate_percentile(pe, industry_avg_pe),
               'score': valuation_score
           }
   ```

2. **实现盈利能力分析**
   ```python
   async def analyze_profitability(self, financials: List[Dict]) -> Dict:
       """盈利能力分析"""
       latest = financials[0]

       roe = latest.get('roe')
       roa = latest.get('roa')
       net_margin = latest.get('net_margin')
       gross_margin = latest.get('gross_margin')

       # 计算 ROE 稳定性（过去 5 年）
       roe_history = [f.get('roe') for f in financials[:5]]
       roe_std = np.std(roe_history)

       profitability_score = self._calculate_profitability_score(
           roe, roa, net_margin, roe_std
       )

       return {
           'roe': roe,
           'roa': roa,
           'net_margin': net_margin,
           'gross_margin': gross_margin,
           'roe_std': roe_std,
           'score': profitability_score
       }
   ```

3. **实现成长性分析**
   ```python
   async def analyze_growth(self, financials: List[Dict]) -> Dict:
       """成长性分析"""
       # 计算营收增长率（YoY）
       revenue_growth = self._calculate_yoy_growth(
           [f.get('revenue') for f in financials[:2]]
       )

       # 计算净利润增长率（YoY）
       profit_growth = self._calculate_yoy_growth(
           [f.get('net_profit') for f in financials[:2]]
       )

       # 计算 3 年复合增长率
       revenue_cagr = self._calculate_cagr(
           [f.get('revenue') for f in financials[:4]]
       )

       growth_score = self._calculate_growth_score(
           revenue_growth, profit_growth, revenue_cagr
       )

       return {
           'revenue_growth_yoy': revenue_growth,
           'profit_growth_yoy': profit_growth,
           'revenue_cagr_3y': revenue_cagr,
           'score': growth_score
       }
   ```

4. **实现财务健康分析**
   ```python
   async def analyze_financial_health(self, financials: Dict) -> Dict:
       """财务健康分析"""
       debt_ratio = financials.get('debt_ratio')
       current_ratio = financials.get('current_ratio')
       operating_cash_flow = financials.get('operating_cash_flow')
       free_cash_flow = financials.get('free_cash_flow')

       health_score = self._calculate_health_score(
           debt_ratio, current_ratio, operating_cash_flow, free_cash_flow
       )

       return {
           'debt_ratio': debt_ratio,
           'current_ratio': current_ratio,
           'operating_cash_flow': operating_cash_flow,
           'free_cash_flow': free_cash_flow,
           'score': health_score
       }
   ```

5. **综合基本面评分**
   ```python
   async def analyze(self, stock_code: str) -> FundamentalAnalysis:
       """综合基本面分析"""
       # 获取数据
       stock_data = await self._get_stock_data(stock_code)
       financials = await self._get_financials(stock_code)

       # 各维度分析
       valuation = await self.analyze_valuation(stock_data)
       profitability = await self.analyze_profitability(financials)
       growth = await self.analyze_growth(financials)
       health = await self.analyze_financial_health(financials[0])

       # 综合评分（加权平均）
       score = (
           valuation['score'] * 0.25 +
           profitability['score'] * 0.30 +
           growth['score'] * 0.25 +
           health['score'] * 0.20
       )

       # 生成总结
       summary = self._generate_summary(valuation, profitability, growth, health)

       return FundamentalAnalysis(
           score=score,
           valuation=valuation,
           profitability=profitability,
           growth=growth,
           financial_health=health,
           summary=summary
       )
   ```

6. **编写测试**
   ```python
   # backend/tests/unit/test_fundamental_analyzer.py

   @pytest.mark.asyncio
   async def test_valuation_analysis():
       analyzer = FundamentalAnalyzer()
       stock_data = {
           'pe_ttm': 12.5,
           'pb': 1.8,
           'ps': 2.5,
           'industry': '白酒'
       }

       result = await analyzer.analyze_valuation(stock_data)

       assert 'score' in result
       assert 0 <= result['score'] <= 10
   ```

7. **提交代码**
   ```bash
   git add backend/app/engines/fundamental_analyzer.py backend/tests/
   git commit -m "feat: implement fundamental analysis module"
   ```

---

### ⬜ Task 3: 技术面分析模块
**状态**: 待开始
**文件**:
- 创建: `backend/app/engines/technical_analyzer.py`
- 创建: `backend/app/utils/indicators.py`
- 创建: `backend/tests/unit/test_technical_analyzer.py`

**步骤**:

1. **实现技术指标计算工具**
   ```python
   # backend/app/utils/indicators.py

   import talib
   import pandas as pd

   def calculate_ma(prices: pd.Series, periods: List[int]) -> Dict:
       """计算移动平均线"""
       return {
           f'ma{period}': talib.SMA(prices, timeperiod=period)
           for period in periods
       }

   def calculate_macd(prices: pd.Series) -> Dict:
       """计算 MACD"""
       macd, signal, hist = talib.MACD(prices)
       return {
           'dif': macd,
           'dea': signal,
           'bar': hist
       }

   def calculate_rsi(prices: pd.Series, periods: List[int]) -> Dict:
       """计算 RSI"""
       return {
           f'rsi{period}': talib.RSI(prices, timeperiod=period)
           for period in periods
       }

   def calculate_kdj(high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
       """计算 KDJ"""
       k, d = talib.STOCH(high, low, close)
       j = 3 * k - 2 * d
       return {'k': k, 'd': d, 'j': j}

   def calculate_boll(prices: pd.Series, period: int = 20) -> Dict:
       """计算布林带"""
       upper, middle, lower = talib.BBANDS(prices, timeperiod=period)
       return {
           'upper': upper,
           'mid': middle,
           'lower': lower
       }
   ```

2. **实现趋势分析**
   ```python
   # backend/app/engines/technical_analyzer.py

   class TechnicalAnalyzer:
       async def analyze_trend(self, kline_data: pd.DataFrame) -> Dict:
           """趋势分析"""
           close = kline_data['close']

           # 计算均线
           ma_data = calculate_ma(close, [5, 10, 20, 60])

           # 判断趋势
           ma5 = ma_data['ma5'].iloc[-1]
           ma10 = ma_data['ma10'].iloc[-1]
           ma20 = ma_data['ma20'].iloc[-1]
           ma60 = ma_data['ma60'].iloc[-1]

           if ma5 > ma10 > ma20 > ma60:
               trend = "强势上涨"
               trend_score = 9
           elif ma5 > ma10 > ma20:
               trend = "上涨"
               trend_score = 7
           elif ma5 < ma10 < ma20 < ma60:
               trend = "强势下跌"
               trend_score = 2
           elif ma5 < ma10 < ma20:
               trend = "下跌"
               trend_score = 4
           else:
               trend = "震荡"
               trend_score = 5

           return {
               'trend': trend,
               'score': trend_score,
               'ma_data': ma_data
           }

       async def analyze_momentum(self, kline_data: pd.DataFrame) -> Dict:
           """动量分析"""
           close = kline_data['close']

           # MACD
           macd_data = calculate_macd(close)
           macd_signal = self._interpret_macd(macd_data)

           # RSI
           rsi_data = calculate_rsi(close, [6, 12, 24])
           rsi_signal = self._interpret_rsi(rsi_data)

           # KDJ
           kdj_data = calculate_kdj(
               kline_data['high'],
               kline_data['low'],
               kline_data['close']
           )
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
           """寻找支撑位和压力位"""
           high = kline_data['high']
           low = kline_data['low']
           close = kline_data['close']

           # 使用局部极值点
           support_levels = self._find_local_minima(low)
           resistance_levels = self._find_local_maxima(high)

           return {
               'support_levels': support_levels[:3],  # 前3个支撑位
               'resistance_levels': resistance_levels[:3]  # 前3个压力位
           }
   ```

3. **综合技术面评分**
   ```python
   async def analyze(self, stock_code: str) -> TechnicalAnalysis:
       """综合技术面分析"""
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
           score=score,
           trend=trend_result['trend'],
           support_levels=levels['support_levels'],
           resistance_levels=levels['resistance_levels'],
           indicators={
               'ma': trend_result['ma_data'],
               'macd': momentum_result['macd'],
               'rsi': momentum_result['rsi'],
               'kdj': momentum_result['kdj']
           },
           summary=summary
       )
   ```

4. **提交代码**
   ```bash
   git add backend/app/engines/technical_analyzer.py backend/app/utils/indicators.py
   git commit -m "feat: implement technical analysis module"
   ```

---

### ⬜ Task 4: 资金面分析模块
**状态**: 待开始
**文件**:
- 创建: `backend/app/engines/capital_flow_analyzer.py`
- 创建: `backend/tests/unit/test_capital_flow_analyzer.py`

**步骤**:

1. **实现资金流向分析**
   ```python
   # backend/app/engines/capital_flow_analyzer.py

   class CapitalFlowAnalyzer:
       async def analyze(self, stock_code: str) -> CapitalFlowAnalysis:
           """资金流向分析"""
           # 获取资金流向数据（最近 20 天）
           flow_data = await self._get_capital_flow_data(stock_code, days=20)

           # 计算主力资金净流入
           main_net_inflow = flow_data['main_net'].sum()

           # 计算主力资金流入占比
           total_amount = flow_data['amount'].sum()
           main_inflow_ratio = main_net_inflow / total_amount if total_amount > 0 else 0

           # 判断趋势
           recent_5d = flow_data['main_net'].tail(5).sum()
           if recent_5d > 0 and main_inflow_ratio > 0.05:
               trend = "持续流入"
               score = 8
           elif recent_5d > 0:
               trend = "流入"
               score = 6
           elif recent_5d < 0 and main_inflow_ratio < -0.05:
               trend = "持续流出"
               score = 3
           elif recent_5d < 0:
               trend = "流出"
               score = 4
           else:
               trend = "平衡"
               score = 5

           # 生成总结
           summary = self._generate_summary(
               main_net_inflow, main_inflow_ratio, trend
           )

           return CapitalFlowAnalysis(
               score=score,
               main_net_inflow=main_net_inflow,
               main_inflow_ratio=main_inflow_ratio,
               trend=trend,
               summary=summary
           )
   ```

2. **提交代码**
   ```bash
   git add backend/app/engines/capital_flow_analyzer.py
   git commit -m "feat: implement capital flow analysis module"
   ```

---

### ⬜ Task 5: 分析报告 API
**状态**: 待开始
**文件**:
- 创建: `backend/app/api/v1/analysis.py`
- 修改: `backend/main.py`
- 创建: `backend/tests/integration/test_analysis_api.py`

**步骤**:

1. **实现分析 API 端点**
   ```python
   # backend/app/api/v1/analysis.py

   from fastapi import APIRouter, HTTPException, Query
   from app.engines.analyzer import StockAnalyzer
   from app.schemas.analysis import AnalysisReport

   router = APIRouter()

   @router.post("/{stock_code}/analyze", response_model=AnalysisReport)
   async def analyze_stock(
       stock_code: str,
       report_type: str = Query("comprehensive", regex="^(comprehensive|fundamental|technical)$"),
       force_refresh: bool = False
   ):
       """生成个股分析报告"""
       try:
           analyzer = StockAnalyzer(db, cache)
           report = await analyzer.analyze(stock_code, report_type, force_refresh)
           return report
       except Exception as e:
           raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

   @router.get("/{stock_code}/report", response_model=AnalysisReport)
   async def get_analysis_report(stock_code: str):
       """获取缓存的分析报告"""
       cache_key = f"analysis:report:{stock_code}"
       cached = await cache.get(cache_key)

       if not cached:
           raise HTTPException(status_code=404, detail="Report not found")

       return AnalysisReport(**json.loads(cached))
   ```

2. **注册路由**
   ```python
   # backend/main.py
   from app.api.v1 import analysis

   app.include_router(
       analysis.router,
       prefix=f"{settings.API_V1_STR}/stocks",
       tags=["analysis"]
   )
   ```

3. **测试 API**
   ```bash
   # 生成分析报告
   curl -X POST http://localhost:8000/api/v1/stocks/600519/analyze | jq

   # 获取缓存报告
   curl http://localhost:8000/api/v1/stocks/600519/report | jq
   ```

4. **提交代码**
   ```bash
   git add backend/app/api/v1/analysis.py backend/main.py
   git commit -m "feat: add stock analysis API endpoints"
   ```

---

## 完成标准

Phase 2 完成后，分析引擎应具备以下能力：

### 功能完整性
- ✅ 基本面分析（估值、盈利、成长、财务健康）
- ✅ 技术面分析（趋势、动量、支撑压力位）
- ✅ 资金面分析（主力资金流向）
- ✅ 综合评分系统
- ✅ 分析报告生成
- ✅ RESTful API

### 质量标准
- ✅ 测试覆盖率 80%+
- ✅ 分析逻辑准确
- ✅ 报告格式规范

### 性能标准
- ✅ 缓存命中时响应 < 100ms
- ✅ 缓存未命中时响应 < 3s
- ✅ 支持并发分析请求

---

## 下一步

完成 Phase 2 后，进入 **Phase 3: AI 引擎与 Agent 系统**

参考文档: `docs/tasks/phase-3-ai-engine.md`
