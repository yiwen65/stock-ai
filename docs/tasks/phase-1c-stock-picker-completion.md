# Phase 1C: 完成选股引擎核心功能

**优先级**: 🔴 高
**状态**: ⏳ 进行中
**预计工作量**: 中等
**依赖**: Phase 1B (60% 完成)

---

## 任务清单

### ⏳ Task 1: 完成 Strategy Execution API
**状态**: 待开始
**文件**:
- 修改: `backend/app/api/v1/strategy.py`
- 修改: `backend/main.py`
- 创建: `backend/tests/integration/test_strategy_api.py`

**步骤**:

1. **完善 Strategy API 端点**
   ```python
   # backend/app/api/v1/strategy.py

   @router.post("/execute", response_model=StrategyExecuteResponse)
   async def execute_strategy(request: StrategyExecuteRequest):
       """执行选股策略"""
       # 添加参数验证
       # 添加缓存检查
       # 执行策略
       # 返回结果

   @router.get("/strategies", response_model=List[StrategyInfo])
   async def list_strategies():
       """列出所有可用策略"""
       return [
           {"name": "graham", "description": "格雷厄姆价值投资"},
           {"name": "buffett", "description": "巴菲特护城河"},
           {"name": "peg", "description": "PEG成长策略"},
           {"name": "custom", "description": "自定义策略"}
       ]
   ```

2. **注册路由到 main.py**
   ```python
   # backend/main.py
   from app.api.v1 import strategy

   app.include_router(
       strategy.router,
       prefix=f"{settings.API_V1_STR}/strategies",
       tags=["strategies"]
   )
   ```

3. **编写集成测试**
   ```python
   # backend/tests/integration/test_strategy_api.py

   @pytest.mark.asyncio
   async def test_execute_graham_strategy():
       response = client.post("/api/v1/strategies/execute", json={
           "strategy_type": "graham",
           "limit": 10
       })
       assert response.status_code == 200
       assert len(response.json()["data"]) <= 10
   ```

4. **测试 API 端点**
   ```bash
   # 启动服务器
   cd backend && python3 -m uvicorn main:app --reload &

   # 测试端点
   curl -X POST http://localhost:8000/api/v1/strategies/execute \
     -H "Content-Type: application/json" \
     -d '{"strategy_type": "graham", "limit": 10}'

   # 停止服务器
   pkill -f "uvicorn main:app"
   ```

5. **提交代码**
   ```bash
   git add backend/app/api/v1/strategy.py backend/main.py backend/tests/
   git commit -m "feat: complete strategy execution API with tests"
   ```

**验证标准**:
- ✅ API 端点返回正确的 JSON 格式
- ✅ 参数验证正常工作
- ✅ 集成测试通过
- ✅ API 文档自动生成（FastAPI Swagger）

---

### ⏳ Task 2: 实现并集成 Risk Filters
**状态**: 待开始
**文件**:
- 创建: `backend/app/engines/risk_filter.py`
- 创建: `backend/tests/unit/test_risk_filter.py`
- 修改: `backend/app/engines/stock_filter.py`

**步骤**:

1. **创建 Risk Filter 模块**（已在 Phase 1B Task 5 中定义）
   - 实现 ST 股票过滤
   - 实现停牌股票过滤
   - 实现低流动性过滤
   - 实现市值过滤

2. **集成到 StockFilter**
   ```python
   # backend/app/engines/stock_filter.py

   class StockFilter:
       def __init__(self):
           self.data_service = DataService()
           self.risk_filter = RiskFilter()

       async def apply_filter(
           self,
           conditions: List[FilterCondition],
           apply_risk_filters: bool = True
       ) -> List[Dict]:
           stocks = await self.data_service.fetch_stock_list()

           # 先应用风险过滤
           if apply_risk_filters:
               stocks = await self.risk_filter.apply_all_filters(stocks)

           # 再应用条件过滤
           df = pd.DataFrame(stocks)
           for condition in conditions:
               df = self._apply_condition(df, condition)

           return df.to_dict('records')
   ```

3. **编写单元测试**
   - 测试 ST 股票过滤
   - 测试停牌股票过滤
   - 测试低流动性过滤
   - 测试组合过滤

4. **运行测试**
   ```bash
   pytest backend/tests/unit/test_risk_filter.py -v
   ```

5. **提交代码**
   ```bash
   git add backend/app/engines/ backend/tests/
   git commit -m "feat: integrate risk filters into stock filtering engine"
   ```

**验证标准**:
- ✅ 所有风险过滤器单元测试通过
- ✅ 集成到 StockFilter 后测试通过
- ✅ 过滤结果符合预期（无 ST、无停牌、有流动性）

---

### ⬜ Task 3: 添加更多经典策略
**状态**: 待开始
**文件**:
- 创建: `backend/app/engines/strategies/buffett.py`
- 创建: `backend/app/engines/strategies/peg.py`
- 创建: `backend/app/engines/strategies/lynch.py`
- 创建: `backend/tests/unit/test_buffett_strategy.py`
- 创建: `backend/tests/unit/test_peg_strategy.py`
- 创建: `backend/tests/unit/test_lynch_strategy.py`

**步骤**:

1. **实现 Buffett 护城河策略**
   ```python
   # backend/app/engines/strategies/buffett.py

   class BuffettStrategy:
       """巴菲特护城河策略

       条件:
       - ROE > 15% 且连续 5 年
       - ROE 标准差 < 5%
       - 毛利率 > 30%
       - 自由现金流连续 3 年为正
       - 资产负债率 < 50%
       - 市值 > 100 亿
       """

       async def execute(self, params: Dict = None) -> List[Dict]:
           # 实现逻辑
           pass
   ```

2. **实现 PEG 成长策略**
   ```python
   # backend/app/engines/strategies/peg.py

   class PEGStrategy:
       """PEG 成长策略

       条件:
       - PEG < 1
       - 营收增长率 > 20%
       - 净利润增长率 > 20%
       - ROE > 10%
       - 市值 > 50 亿
       """

       async def execute(self, params: Dict = None) -> List[Dict]:
           # 实现逻辑
           pass
   ```

3. **实现 Lynch 成长策略**
   ```python
   # backend/app/engines/strategies/lynch.py

   class LynchStrategy:
       """彼得·林奇成长策略

       条件:
       - PE < 行业平均
       - 营收增长率 > 15%
       - 净利润增长率 > 15%
       - 负债率 < 60%
       - 市值 > 30 亿
       """

       async def execute(self, params: Dict = None) -> List[Dict]:
           # 实现逻辑
           pass
   ```

4. **为每个策略编写测试**
   - 使用 mock 数据
   - 验证筛选条件
   - 验证结果数量和质量

5. **更新 Strategy API**
   ```python
   # backend/app/api/v1/strategy.py

   @router.post("/execute")
   async def execute_strategy(request: StrategyExecuteRequest):
       if request.strategy_type == "graham":
           strategy = GrahamStrategy()
       elif request.strategy_type == "buffett":
           strategy = BuffettStrategy()
       elif request.strategy_type == "peg":
           strategy = PEGStrategy()
       elif request.strategy_type == "lynch":
           strategy = LynchStrategy()
       # ...
   ```

6. **提交代码**
   ```bash
   git add backend/app/engines/strategies/ backend/tests/
   git commit -m "feat: add Buffett, PEG, and Lynch strategies"
   ```

**验证标准**:
- ✅ 每个策略的单元测试通过
- ✅ 策略逻辑符合投资理论
- ✅ API 可以正确调用所有策略

---

### ⬜ Task 4: 策略结果缓存优化
**状态**: 待开始
**文件**:
- 修改: `backend/app/api/v1/strategy.py`
- 修改: `backend/app/core/cache.py`

**步骤**:

1. **设计缓存 Key 策略**
   ```python
   # 缓存 Key 格式: strategy:result:{strategy_type}:{params_hash}
   # TTL: 30 分钟

   def generate_cache_key(strategy_type: str, params: Dict) -> str:
       params_str = json.dumps(params, sort_keys=True)
       params_hash = hashlib.md5(params_str.encode()).hexdigest()
       return f"strategy:result:{strategy_type}:{params_hash}"
   ```

2. **实现缓存逻辑**
   ```python
   # backend/app/api/v1/strategy.py

   @router.post("/execute")
   async def execute_strategy(request: StrategyExecuteRequest):
       # 1. 生成缓存 Key
       cache_key = generate_cache_key(
           request.strategy_type,
           request.dict()
       )

       # 2. 尝试从缓存获取
       cached = await redis.get(cache_key)
       if cached and not request.force_refresh:
           return json.loads(cached)

       # 3. 执行策略
       results = await strategy.execute()

       # 4. 写入缓存
       await redis.setex(cache_key, 1800, json.dumps(results))

       return results
   ```

3. **添加缓存统计**
   ```python
   # 记录缓存命中率
   cache_hits = await redis.incr("stats:cache:hits")
   cache_misses = await redis.incr("stats:cache:misses")
   ```

4. **测试缓存功能**
   ```bash
   # 第一次请求（缓存未命中）
   time curl -X POST http://localhost:8000/api/v1/strategies/execute \
     -d '{"strategy_type": "graham"}'

   # 第二次请求（缓存命中，应该更快）
   time curl -X POST http://localhost:8000/api/v1/strategies/execute \
     -d '{"strategy_type": "graham"}'
   ```

5. **提交代码**
   ```bash
   git add backend/app/api/v1/strategy.py backend/app/core/cache.py
   git commit -m "feat: add caching for strategy execution results"
   ```

**验证标准**:
- ✅ 缓存命中时响应时间显著减少
- ✅ 缓存 Key 生成正确
- ✅ TTL 设置正确（30 分钟）
- ✅ force_refresh 参数可以绕过缓存

---

### ⬜ Task 5: 完善测试覆盖率
**状态**: 待开始
**文件**:
- 创建: `backend/tests/integration/test_stock_picker_flow.py`
- 修改: 所有测试文件

**步骤**:

1. **编写端到端集成测试**
   ```python
   # backend/tests/integration/test_stock_picker_flow.py

   @pytest.mark.asyncio
   async def test_complete_stock_picking_flow():
       """测试完整的选股流程"""
       # 1. 执行 Graham 策略
       response = client.post("/api/v1/strategies/execute", json={
           "strategy_type": "graham",
           "limit": 10
       })
       assert response.status_code == 200
       results = response.json()["data"]

       # 2. 验证结果符合 Graham 条件
       for stock in results:
           assert stock["pe"] < 15
           assert stock["pb"] < 2
           assert stock["debt_ratio"] < 60

       # 3. 测试自定义策略
       response = client.post("/api/v1/strategies/execute", json={
           "strategy_type": "custom",
           "conditions": {
               "conditions": [
                   {"field": "pe", "operator": "<", "value": 20},
                   {"field": "roe", "operator": ">", "value": 10}
               ],
               "logic": "AND"
           },
           "limit": 20
       })
       assert response.status_code == 200
   ```

2. **运行测试覆盖率检查**
   ```bash
   pytest backend/tests/ --cov=backend/app --cov-report=term-missing
   ```

3. **目标覆盖率**: 80%+
   - 核心引擎: 90%+
   - API 层: 80%+
   - 工具函数: 70%+

4. **补充缺失的测试**
   - 边界条件测试
   - 错误处理测试
   - 异常情况测试

5. **提交代码**
   ```bash
   git add backend/tests/
   git commit -m "test: improve test coverage to 80%+"
   ```

**验证标准**:
- ✅ 测试覆盖率达到 80%+
- ✅ 所有核心功能有测试
- ✅ 边界条件和错误处理有测试
- ✅ 集成测试通过

---

## 完成标准

Phase 1C 完成后，选股引擎应具备以下能力：

### 功能完整性
- ✅ 支持 4 种经典策略（Graham, Buffett, PEG, Lynch）
- ✅ 支持自定义条件筛选
- ✅ 风险过滤自动应用
- ✅ 结果缓存优化
- ✅ RESTful API 完整

### 质量标准
- ✅ 测试覆盖率 80%+
- ✅ 所有单元测试通过
- ✅ 所有集成测试通过
- ✅ API 文档完整（Swagger）

### 性能标准
- ✅ 缓存命中时响应 < 100ms
- ✅ 缓存未命中时响应 < 2s
- ✅ 支持并发请求

---

## 下一步

完成 Phase 1C 后，进入 **Phase 2: 个股分析引擎**

参考文档: `docs/tasks/phase-2-analysis-engine.md`
