# Phase 3: AI 引擎与 Agent 系统

**优先级**: 🔴 高
**状态**: ⬜ 待开始
**预计工作量**: 大
**依赖**: Phase 2 完成

---

## 任务清单

### ⬜ Task 1: LLM 集成基础设施
**状态**: 待开始
**文件**:
- 创建: `backend/app/services/llm_service.py`
- 创建: `backend/app/core/llm_config.py`
- 修改: `backend/app/core/config.py`
- 修改: `backend/requirements.txt`

**步骤**:

1. **添加 LLM 依赖**
   ```python
   # backend/requirements.txt
   openai==1.12.0
   langchain==0.1.6
   langchain-openai==0.0.5
   tiktoken==0.5.2
   ```

2. **配置 LLM 设置**
   ```python
   # backend/app/core/llm_config.py

   from pydantic_settings import BaseSettings

   class LLMSettings(BaseSettings):
       OPENAI_API_KEY: str
       OPENAI_MODEL: str = "gpt-4-turbo-preview"
       OPENAI_TEMPERATURE: float = 0.7
       OPENAI_MAX_TOKENS: int = 2000

       # DeepSeek 配置（备选）
       DEEPSEEK_API_KEY: str = ""
       DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

       class Config:
           env_file = ".env"
   ```

3. **实现 LLM 服务**
   ```python
   # backend/app/services/llm_service.py

   from openai import AsyncOpenAI
   from typing import List, Dict, Optional

   class LLMService:
       def __init__(self, settings: LLMSettings):
           self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
           self.model = settings.OPENAI_MODEL
           self.temperature = settings.OPENAI_TEMPERATURE
           self.max_tokens = settings.OPENAI_MAX_TOKENS

       async def chat_completion(
           self,
           messages: List[Dict[str, str]],
           temperature: Optional[float] = None,
           max_tokens: Optional[int] = None
       ) -> str:
           """调用 LLM 生成回复"""
           response = await self.client.chat.completions.create(
               model=self.model,
               messages=messages,
               temperature=temperature or self.temperature,
               max_tokens=max_tokens or self.max_tokens
           )
           return response.choices[0].message.content

       async def structured_output(
           self,
           messages: List[Dict[str, str]],
           response_format: Dict
       ) -> Dict:
           """调用 LLM 生成结构化输出（JSON）"""
           response = await self.client.chat.completions.create(
               model=self.model,
               messages=messages,
               response_format={"type": "json_object"},
               temperature=0.3  # 降低温度以提高结构化输出准确性
           )
           import json
           return json.loads(response.choices[0].message.content)
   ```

4. **测试 LLM 连接**
   ```python
   # backend/tests/unit/test_llm_service.py

   @pytest.mark.asyncio
   async def test_llm_chat_completion():
       llm_service = LLMService(settings)
       messages = [
           {"role": "system", "content": "You are a helpful assistant."},
           {"role": "user", "content": "Say hello"}
       ]
       response = await llm_service.chat_completion(messages)
       assert isinstance(response, str)
       assert len(response) > 0
   ```

5. **提交代码**
   ```bash
   git add backend/app/services/llm_service.py backend/app/core/llm_config.py
   git commit -m "feat: add LLM service integration"
   ```

---

### ⬜ Task 2: 自然语言策略解析引擎
**状态**: 待开始
**文件**:
- 创建: `backend/app/engines/strategy_parser.py`
- 创建: `backend/app/schemas/strategy_parse.py`
- 创建: `backend/tests/unit/test_strategy_parser.py`

**步骤**:

1. **设计策略解析 Schema**
   ```python
   # backend/app/schemas/strategy_parse.py

   from pydantic import BaseModel
   from typing import List, Optional

   class StrategyParseRequest(BaseModel):
       description: str  # 用户的自然语言描述

   class ParsedCondition(BaseModel):
       field: str
       operator: str
       value: float | List[float]
       description: str  # 条件的中文描述

   class StrategyParseResponse(BaseModel):
       conditions: List[ParsedCondition]
       logic: str  # "AND" or "OR"
       conflicts: List[str]  # 逻辑冲突提示
       confidence: float  # 解析置信度 (0-1)
       summary: str  # 策略总结
   ```

2. **实现策略解析引擎**
   ```python
   # backend/app/engines/strategy_parser.py

   class StrategyParser:
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
               conditions=parsed['conditions'],
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
   ```

3. **编写测试用例**
   ```python
   # backend/tests/unit/test_strategy_parser.py

   @pytest.mark.asyncio
   async def test_parse_graham_strategy():
       parser = StrategyParser(llm_service)
       description = "寻找市盈率小于15、市净率小于2、资产负债率小于60%的价值股"

       result = await parser.parse(description)

       assert len(result.conditions) == 3
       assert any(c.field == 'pe' and c.operator == '<' and c.value == 15 for c in result.conditions)
       assert result.logic == "AND"
       assert len(result.conflicts) == 0
   ```

4. **创建策略解析 API**
   ```python
   # backend/app/api/v1/strategy.py (添加端点)

   @router.post("/parse", response_model=StrategyParseResponse)
   async def parse_strategy(request: StrategyParseRequest):
       """解析自然语言策略描述"""
       parser = StrategyParser(llm_service)
       result = await parser.parse(request.description)
       return result
   ```

5. **提交代码**
   ```bash
   git add backend/app/engines/strategy_parser.py backend/app/schemas/strategy_parse.py
   git commit -m "feat: add natural language strategy parser"
   ```

---

### ⬜ Task 3: Multi-Agent 架构基础
**状态**: 待开始
**文件**:
- 创建: `backend/app/agents/base_agent.py`
- 创建: `backend/app/agents/orchestrator.py`
- 创建: `backend/tests/unit/test_agents.py`

**步骤**:

1. **设计 Agent 基类**
   ```python
   # backend/app/agents/base_agent.py

   from abc import ABC, abstractmethod
   from typing import Dict, Any

   class BaseAgent(ABC):
       """Agent 基类"""

       def __init__(self, llm_service: LLMService, name: str):
           self.llm_service = llm_service
           self.name = name

       @abstractmethod
       async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
           """执行 Agent 任务"""
           pass

       def _build_prompt(self, context: Dict[str, Any]) -> str:
           """构建提示词"""
           pass

       async def _call_llm(self, prompt: str) -> str:
           """调用 LLM"""
           messages = [
               {"role": "system", "content": self._get_system_prompt()},
               {"role": "user", "content": prompt}
           ]
           return await self.llm_service.chat_completion(messages)

       @abstractmethod
       def _get_system_prompt(self) -> str:
           """获取系统提示词"""
           pass
   ```

2. **实现 Orchestrator Agent**
   ```python
   # backend/app/agents/orchestrator.py

   class OrchestratorAgent:
       """主控 Agent：协调多个专业 Agent"""

       def __init__(
           self,
           llm_service: LLMService,
           data_agent: 'DataAgent',
           fundamental_agent: 'FundamentalAgent',
           technical_agent: 'TechnicalAgent',
           evaluator_agent: 'EvaluatorAgent'
       ):
           self.llm_service = llm_service
           self.data_agent = data_agent
           self.fundamental_agent = fundamental_agent
           self.technical_agent = technical_agent
           self.evaluator_agent = evaluator_agent

       async def analyze_stock(self, stock_code: str) -> Dict:
           """协调多个 Agent 分析股票"""
           # 1. Data Agent 获取数据
           data = await self.data_agent.execute({'stock_code': stock_code})

           # 2. 并行执行分析 Agents
           import asyncio
           fundamental_task = self.fundamental_agent.execute(data)
           technical_task = self.technical_agent.execute(data)

           fundamental_result, technical_result = await asyncio.gather(
               fundamental_task,
               technical_task
           )

           # 3. Evaluator Agent 综合评估
           evaluation = await self.evaluator_agent.execute({
               'stock_code': stock_code,
               'fundamental': fundamental_result,
               'technical': technical_result
           })

           return evaluation
   ```

3. **提交代码**
   ```bash
   git add backend/app/agents/
   git commit -m "feat: add multi-agent architecture foundation"
   ```

---

### ⬜ Task 4: 专业分析 Agents
**状态**: 待开始
**文件**:
- 创建: `backend/app/agents/data_agent.py`
- 创建: `backend/app/agents/fundamental_agent.py`
- 创建: `backend/app/agents/technical_agent.py`
- 创建: `backend/app/agents/evaluator_agent.py`

**步骤**:

1. **实现 Data Agent**
   ```python
   # backend/app/agents/data_agent.py

   class DataAgent(BaseAgent):
       """数据获取 Agent"""

       async def execute(self, context: Dict) -> Dict:
           stock_code = context['stock_code']

           # 并行获取数据
           import asyncio
           realtime_task = self._get_realtime_data(stock_code)
           kline_task = self._get_kline_data(stock_code)
           financial_task = self._get_financial_data(stock_code)

           realtime, kline, financial = await asyncio.gather(
               realtime_task, kline_task, financial_task
           )

           return {
               'stock_code': stock_code,
               'realtime': realtime,
               'kline': kline,
               'financial': financial
           }
   ```

2. **实现 Fundamental Agent**
   ```python
   # backend/app/agents/fundamental_agent.py

   class FundamentalAgent(BaseAgent):
       """基本面分析 Agent"""

       def _get_system_prompt(self) -> str:
           return """你是一个专业的基本面分析师。

   你的任务是分析股票的基本面，包括：
   1. 估值水平（PE、PB、PS）
   2. 盈利能力（ROE、ROA、净利率）
   3. 成长性（营收增长、利润增长）
   4. 财务健康（负债率、流动比率、现金流）

   请给出：
   - 各维度评分（0-10分）
   - 优势和风险点
   - 投资建议
   """

       async def execute(self, context: Dict) -> Dict:
           # 构建分析提示
           prompt = self._build_analysis_prompt(context)

           # 调用 LLM 分析
           analysis = await self._call_llm(prompt)

           return {
               'agent': 'fundamental',
               'analysis': analysis,
               'score': self._extract_score(analysis)
           }
   ```

3. **实现 Technical Agent**
   ```python
   # backend/app/agents/technical_agent.py

   class TechnicalAgent(BaseAgent):
       """技术面分析 Agent"""

       def _get_system_prompt(self) -> str:
           return """你是一个专业的技术分析师。

   你的任务是分析股票的技术面，包括：
   1. 趋势判断（上涨/下跌/震荡）
   2. 技术指标（MA、MACD、RSI、KDJ）
   3. 支撑位和压力位
   4. 买卖时机

   请给出：
   - 技术面评分（0-10分）
   - 关键技术信号
   - 操作建议
   """

       async def execute(self, context: Dict) -> Dict:
           prompt = self._build_analysis_prompt(context)
           analysis = await self._call_llm(prompt)

           return {
               'agent': 'technical',
               'analysis': analysis,
               'score': self._extract_score(analysis)
           }
   ```

4. **实现 Evaluator Agent**
   ```python
   # backend/app/agents/evaluator_agent.py

   class EvaluatorAgent(BaseAgent):
       """综合评估 Agent"""

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
   ```

5. **提交代码**
   ```bash
   git add backend/app/agents/
   git commit -m "feat: implement specialized analysis agents"
   ```

---

### ⬜ Task 5: RAG 系统（向量检索）
**状态**: 待开始
**文件**:
- 创建: `backend/app/services/vector_service.py`
- 创建: `backend/app/services/embedding_service.py`
- 修改: `backend/requirements.txt`

**步骤**:

1. **添加依赖**
   ```python
   # backend/requirements.txt
   qdrant-client==1.7.0
   sentence-transformers==2.3.1
   ```

2. **实现 Embedding 服务**
   ```python
   # backend/app/services/embedding_service.py

   from openai import AsyncOpenAI

   class EmbeddingService:
       def __init__(self, api_key: str):
           self.client = AsyncOpenAI(api_key=api_key)
           self.model = "text-embedding-3-small"

       async def embed_text(self, text: str) -> List[float]:
           """生成文本向量"""
           response = await self.client.embeddings.create(
               model=self.model,
               input=text
           )
           return response.data[0].embedding

       async def embed_batch(self, texts: List[str]) -> List[List[float]]:
           """批量生成向量"""
           response = await self.client.embeddings.create(
               model=self.model,
               input=texts
           )
           return [item.embedding for item in response.data]
   ```

3. **实现向量检索服务**
   ```python
   # backend/app/services/vector_service.py

   from qdrant_client import QdrantClient
   from qdrant_client.models import Distance, VectorParams, PointStruct

   class VectorService:
       def __init__(self, host: str = "localhost", port: int = 6333):
           self.client = QdrantClient(host=host, port=port)
           self.embedding_service = EmbeddingService(settings.OPENAI_API_KEY)

       async def create_collection(self, collection_name: str, vector_size: int = 1536):
           """创建向量集合"""
           self.client.create_collection(
               collection_name=collection_name,
               vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
           )

       async def add_documents(
           self,
           collection_name: str,
           documents: List[Dict]
       ):
           """添加文档到向量库"""
           # 生成向量
           texts = [doc['content'] for doc in documents]
           vectors = await self.embedding_service.embed_batch(texts)

           # 构建 Points
           points = [
               PointStruct(
                   id=i,
                   vector=vector,
                   payload=doc
               )
               for i, (vector, doc) in enumerate(zip(vectors, documents))
           ]

           # 插入向量库
           self.client.upsert(
               collection_name=collection_name,
               points=points
           )

       async def search(
           self,
           collection_name: str,
           query: str,
           limit: int = 10,
           filters: Dict = None
       ) -> List[Dict]:
           """语义搜索"""
           # 生成查询向量
           query_vector = await self.embedding_service.embed_text(query)

           # 向量检索
           results = self.client.search(
               collection_name=collection_name,
               query_vector=query_vector,
               limit=limit,
               query_filter=filters
           )

           return [
               {
                   'score': result.score,
                   'payload': result.payload
               }
               for result in results
           ]
   ```

4. **提交代码**
   ```bash
   git add backend/app/services/vector_service.py backend/app/services/embedding_service.py
   git commit -m "feat: add RAG system with vector search"
   ```

---

### ⬜ Task 6: AI 分析 API 集成
**状态**: 待开始
**文件**:
- 修改: `backend/app/api/v1/analysis.py`
- 创建: `backend/tests/integration/test_ai_analysis.py`

**步骤**:

1. **添加 AI 增强分析端点**
   ```python
   # backend/app/api/v1/analysis.py

   @router.post("/{stock_code}/ai-analyze", response_model=AIAnalysisReport)
   async def ai_analyze_stock(stock_code: str):
       """使用 AI Agent 生成深度分析报告"""
       orchestrator = OrchestratorAgent(
           llm_service=llm_service,
           data_agent=DataAgent(llm_service),
           fundamental_agent=FundamentalAgent(llm_service),
           technical_agent=TechnicalAgent(llm_service),
           evaluator_agent=EvaluatorAgent(llm_service)
       )

       result = await orchestrator.analyze_stock(stock_code)
       return result
   ```

2. **测试 AI 分析**
   ```bash
   curl -X POST http://localhost:8000/api/v1/stocks/600519/ai-analyze | jq
   ```

3. **提交代码**
   ```bash
   git add backend/app/api/v1/analysis.py
   git commit -m "feat: integrate AI agents into analysis API"
   ```

---

## 完成标准

Phase 3 完成后，AI 引擎应具备以下能力：

### 功能完整性
- ✅ LLM 集成（OpenAI/DeepSeek）
- ✅ 自然语言策略解析
- ✅ Multi-Agent 架构
- ✅ 专业分析 Agents（Data, Fundamental, Technical, Evaluator）
- ✅ RAG 向量检索系统
- ✅ AI 增强分析 API

### 质量标准
- ✅ 策略解析准确率 > 85%
- ✅ Agent 分析质量高
- ✅ 向量检索相关性好

### 性能标准
- ✅ 策略解析响应 < 3s
- ✅ AI 分析响应 < 10s
- ✅ 向量检索响应 < 500ms

---

## 下一步

完成 Phase 3 后，进入 **Phase 4: 数据同步系统**

参考文档: `docs/tasks/phase-4-data-sync.md`
