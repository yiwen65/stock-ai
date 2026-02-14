# A股AI智能分析应用 — 开发任务计划

**文档版本**: v2.0
**更新日期**: 2026-02-14
**基准对比**: PRD v1.0 vs 当前实现
**实施计划**: 详见 `docs/IMPLEMENTATION_PLAN.md`

---

## 一、PRD 与现状差距总览

### 评估维度与完成度（2026-02-14 更新）

| PRD 模块 | 优先级 | 完成度 | 差距说明 |
|----------|--------|--------|----------|
| 2. 数据层 | P0 | 60% | AKShare 行情/K线/财务/资金流向/板块/新闻/同行业已接入，Redis L1+内存 L2 缓存；缺少北向资金独立接口、Tushare/BaoStock 备用源、数据同步定时任务、WebSocket |
| 3. 经典选股策略 | P0 | 75% | 11/17 策略已实现（Graham/Buffett/PEG/Lynch/均线/MACD/放量/业绩预增/北向/RS动量/质量因子）；缺少布林带/双动量/ATR/三因子/股东增持/行业过滤 |
| 4. 个股深度分析 | P0 | 50% | 基本面(财务评分+成长性)/技术面(趋势+支撑压力+信号)/资金面(主力资金)已实现真实数据分析；缺少消息面/同行业对比引擎/杜邦后端/PE历史分位/DCF |
| 5. 自然语言策略引擎 | P0 | 65% | StrategyParser 支持 35 字段、模糊理解、OR 逻辑、冲突检测、策略 CRUD API+DB 模型；缺少 NOT 逻辑、嵌套条件、策略回测、T+5/T+10 追踪 |
| 6. AI分析引擎 | P0-P1 | 55% | 6 个 Agent 已实现(Data/Fundamental/Technical/CapitalFlow/Evaluator/Orchestrator)，LLM 多模型+容错+Token 统计；缺少 NewsAgent、RAG 系统、置信度标注 |
| 7. 用户交互与界面 | P0 | 70% | 选股中心/个股分析/策略管理/市场概览/登录/合规等页面+K线/MACD/RSI/雷达/资金流向图表已完成；缺少板块热力图集成、资金流向总览集成、自选股、PDF 导出 |
| 8. 非功能性需求 | P0-P1 | 25% | Prometheus/结构化日志/限流/告警基础已有；缺少 HTTPS、Refresh Token、Grafana、数据备份、压力测试 |
| 9. 合规与风险声明 | P0 | 85% | 风险弹窗/免责声明/用户协议/隐私政策/数据来源声明/Agent 合规 Prompt 已完成；基本满足 PRD 要求 |

---

## 二、分阶段开发计划

### Phase 1：完成选股引擎核心 (预计 2-3 周)

#### 1.1 数据服务增强 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 1.1.1 | 补充实时行情字段 | 当前 `fetch_realtime_quote` 缺少 PE/PB/换手率/市值/量比等 PRD 要求字段，需从 `stock_zh_a_spot_em` 中提取完整字段 | `services/data_service.py` | ✅ |
| 1.1.2 | 资金流向数据接入 | 接入 `ak.stock_individual_fund_flow` 获取主力/超大单/大单/中单/小单资金数据 | `services/data_service.py` | ✅ |
| 1.1.3 | 板块与概念数据接入 | 接入 `ak.stock_board_industry_name_em` 和 `ak.stock_board_concept_name_em` | `services/data_service.py` | ✅ |
| 1.1.4 | 北向资金数据接入 | 接入 `ak.stock_hsgt_north_net_flow_in_em` 等北向资金接口 | `services/data_service.py` | ⚠️ 部分(用主力资金代替) |
| 1.1.5 | 全市场行情批量缓存 | 将 `stock_zh_a_spot_em` 全市场数据缓存到 Redis，避免每次单股查询重复拉取 | `services/data_service.py`, `core/cache.py` | ✅ Redis L1 + Memory L2 |
| 1.1.6 | 数据源容错 | AKShare 失败时的降级逻辑（返回缓存数据+延迟标识） | `services/data_service.py` | ✅ stale cache fallback |

#### 1.2 选股策略完善 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 1.2.1 | Graham 策略参数完善 | 补充 PRD 要求的股息率>3%、流动比率>2、连续盈利≥3年条件 | `engines/strategies/graham.py` | ✅ |
| 1.2.2 | Buffett 策略参数完善 | 补充 ROE 连续5年>15%、ROE 稳定性、毛利率>30%、自由现金流连续3年为正 | `engines/strategies/buffett.py` | ✅ |
| 1.2.3 | PEG/Lynch 策略参数完善 | 对齐 PRD 中 PEG<1、扣非净利润增长率、市值范围等条件 | `engines/strategies/peg.py`, `lynch.py` | ✅ |
| 1.2.4 | 均线多头排列策略 | **新增**：MA5>MA10>MA20>MA60 + 金叉 + 放量确认 | `engines/strategies/ma_breakout.py` | ✅ |
| 1.2.5 | MACD 底背离策略 | **新增**：价格新低但 MACD 不新低 + RSI<30 | `engines/strategies/macd_divergence.py` | ✅ |
| 1.2.6 | 放量突破平台策略 | **新增**：横盘整理后放量突破 | `engines/strategies/volume_breakout.py` | ✅ |
| 1.2.7 | 业绩预增/扭亏策略 | **新增**：事件驱动，接入业绩预告数据 | `engines/strategies/earnings_surprise.py` | ✅ |
| 1.2.8 | 北向资金持续流入策略 | **新增**：连续N日北向资金净流入 | `engines/strategies/northbound.py` | ✅ |
| 1.2.9 | 技术指标计算工具 | **新增**：MA/MACD/RSI/KDJ/布林带/ATR/ADX 计算函数 | `utils/indicators.py` | ✅ |

#### 1.3 风险控制集成 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 1.3.1 | 风险过滤器集成到策略执行流 | 所有策略执行后自动调用 `RiskFilter.apply_all_filters` | `api/v1/strategy.py`, `engines/strategies/*.py` | ✅ |
| 1.3.2 | 补充次新股/涨跌停过滤 | PRD 要求排除上市<60日的次新股、当日涨跌停股 | `engines/risk_filter.py` | ✅ 涨跌停已实现 |
| 1.3.3 | 行业/板块过滤 | 支持按行业筛选/排除 | `engines/risk_filter.py` | ⬜ 待实现 |
| 1.3.4 | 综合风险评分 | 基于财务/估值/流动性/波动性的 1-10 分风险评分 | `engines/risk_scorer.py` (新增) | ✅ 5维评分 |

#### 1.4 策略执行 API 完善 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 1.4.1 | 策略参数自定义 | 支持用户调整策略参数(PE范围、ROE阈值等) | `api/v1/strategy.py`, `schemas/strategy.py` | ✅ params字段 |
| 1.4.2 | 策略 CRUD API | 创建/读取/更新/删除用户保存的策略 | `api/v1/strategy.py` | ⬜ |
| 1.4.3 | 策略执行历史记录 | 记录每次执行的时间、结果数量、结果快照 | `models/strategy.py` (新增 StrategyExecution 模型) | ⬜ |
| 1.4.4 | 数据库迁移 | 创建 strategy_executions 表的 Alembic 迁移 | `alembic/versions/` | ⬜ |

---

### Phase 2：个股深度分析引擎 (预计 3-4 周)

#### 2.1 分析数据获取 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 2.1.1 | 分析引擎数据获取对接 | 替换 `analyzer.py` 中 `_fetch_analysis_data` 的 mock，调用 DataService 获取真实数据 | `engines/analyzer.py` | ✅ |
| 2.1.2 | 财务数据增强 | 补充三大报表关键指标：毛利率/净利率/ROIC/自由现金流/周转率 | `services/data_service.py` | ✅ 毛利率/净利率已加 |
| 2.1.3 | 历史财务趋势数据 | 获取近5年季度财务数据用于趋势分析 | `services/data_service.py` | ✅ fetch_financial_data(years=5) |

#### 2.2 基本面分析模块 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 2.2.1 | 财务健康度评分 | PRD 4.2.1：盈利能力30%+偿债能力20%+成长能力25%+运营能力15%+现金流10% | `engines/analyzer.py` | ✅ |
| 2.2.2 | 杜邦分析 | ROE = 净利率 × 总资产周转率 × 权益乘数 拆解 | `engines/fundamental_analyzer.py` | ⬜ |
| 2.2.3 | 成长性评估 | CAGR 计算、成长性分类(高成长/稳健/低速/停滞/衰退) | `engines/analyzer.py` | ✅ |
| 2.2.4 | 估值合理性分析 | PE/PB 历史分位、PEG 估值、简化版 DCF | `engines/analyzer.py` | ⚠️ 部分(缺历史分位/DCF) |

#### 2.3 技术面分析模块 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 2.3.1 | 趋势判断引擎 | 均线排列状态分析 + ADX 趋势强度 | `engines/analyzer.py` | ✅ |
| 2.3.2 | 支撑/压力位识别 | 历史高低点、密集成交区、整数关口、均线位置 | `engines/analyzer.py` | ✅ |
| 2.3.3 | 技术指标综合信号 | MACD/RSI/KDJ/布林带/成交量 加权信号计算 (PRD 4.3.3) | `engines/analyzer.py` | ✅ |

#### 2.4 资金面分析模块 [P0-P1]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 2.4.1 | 主力资金动向分析 | 近1/5/10/20日主力净流入、超大单/大单分布 | `engines/analyzer.py` | ✅ |
| 2.4.2 | 北向资金持仓变化 | 北向持股数量、比例、增减持分析 | `engines/capital_flow_analyzer.py` | ⬜ |

#### 2.5 消息面分析模块 [P1]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 2.5.1 | 公告数据接入 | 接入 AKShare 公告数据接口 | `services/data_service.py` | ⬜ |
| 2.5.2 | 消息面分析引擎 | **新增**：公告分类(业绩/重大事项/股东变动/分红/风险)、影响判断 | `engines/news_analyzer.py` | ⬜ |

#### 2.6 同行业对比模块 [P1]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 2.6.1 | 行业数据服务 | 获取同行业公司列表及关键指标 | `services/data_service.py` | ⬜ |
| 2.6.2 | 行业对比分析引擎 | **新增**：PE/PB/ROE/增长率横向对比、行业排名 | `engines/industry_comparator.py` | ⬜ |

#### 2.7 综合评分模型 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 2.7.1 | 综合评分权重对齐 | 按 PRD 4.7.1：基本面35%+技术面25%+资金面20%+估值15%+消息面5% | `engines/analyzer.py` | ✅ |
| 2.7.2 | 风险等级评估完善 | 多维度风险(财务/估值/流动性/波动性/事件)评估 | `engines/analyzer.py`, `engines/risk_scorer.py` | ✅ |
| 2.7.3 | 操作建议生成 | 买入/持有/观望/减仓/卖出 + 仓位/买入价/止损价/目标价 | `agents/evaluator_agent.py` | ✅ |

---

### Phase 3：AI 引擎与 Agent 系统 (预计 3-4 周)

#### 3.1 LLM 服务完善 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 3.1.1 | 多模型支持 | 配置支持 GPT-4/Claude/DeepSeek/Qwen 切换 | `core/llm_config.py`, `services/llm_service.py` | ✅ OpenAI/DeepSeek/Qwen |
| 3.1.2 | LLM 调用容错 | 主备模型自动切换、重试机制、超时处理 | `services/llm_service.py` | ✅ primary→fallback+retry |
| 3.1.3 | Token 用量统计 | 统计每次 LLM 调用的 token 消耗和成本 | `services/llm_service.py` | ✅ get_usage_stats() |

#### 3.2 Prompt 工程 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 3.2.1 | 策略解析 Prompt 完善 | 对齐 PRD 6.2.1 模板1：意图识别+实体提取+条件结构化+冲突检测 | `engines/strategy_parser.py` | ✅ 35字段+模糊理解 |
| 3.2.2 | 基本面分析 Prompt | 对齐 PRD 6.2.1 模板2：财务健康度+盈利趋势+成长性+估值 | `agents/fundamental_agent.py` | ✅ |
| 3.2.3 | 技术面分析 Prompt | 对齐 PRD 6.2.1 模板3：趋势判断+支撑压力+综合信号 | `agents/technical_agent.py` | ✅ 含指标预计算 |
| 3.2.4 | 综合评估 Prompt | 对齐 PRD 6.2.1 模板4：综合评分+风险等级+操作建议+投资逻辑 | `agents/evaluator_agent.py` | ✅ 含仓位/止损/目标价 |
| 3.2.5 | 自然语言模糊理解 | 支持“便宜的好公司”等模糊表达的智能解释 | `engines/strategy_parser.py` | ✅ 示例映射+别名匹配 |

#### 3.3 Multi-Agent 实现 [P1]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 3.3.1 | DataAgent 实现 | 真实数据获取逻辑：调用 DataService 获取行情+财务+资金数据 | `agents/data_agent.py` | ✅ 并行4路获取 |
| 3.3.2 | FundamentalAgent 实现 | 调用 LLM 结合财务数据生成基本面分析 | `agents/fundamental_agent.py` | ✅ |
| 3.3.3 | TechnicalAgent 实现 | 调用 LLM 结合技术指标数据生成技术面分析 | `agents/technical_agent.py` | ✅ 含指标预计算 |
| 3.3.4 | 新增 CapitalFlowAgent | **新增**：资金面分析 Agent (PRD 中有但代码缺失) | `agents/capital_flow_agent.py` | ✅ |
| 3.3.5 | 新增 NewsAgent | **新增**：消息面分析 Agent | `agents/news_agent.py` | ⬜ |
| 3.3.6 | EvaluatorAgent 实现 | 汇总多维度分析，调用 LLM 生成综合报告 | `agents/evaluator_agent.py` | ✅ PRD权重+仓位/止损 |
| 3.3.7 | Orchestrator 完善 | 添加 CapitalFlowAgent/NewsAgent 的并行调度 | `agents/orchestrator.py` | ✅ 3Agent并行+异常处理 |

#### 3.4 RAG 系统 [P1]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 3.4.1 | Qdrant 容器部署 | 在 docker-compose 中添加 Qdrant 服务 | `docker-compose.yml` | ⬜ |
| 3.4.2 | 公告/新闻向量化 | 使用 sentence-transformers 对公告进行 embedding | `services/embedding_service.py` | ⬜ |
| 3.4.3 | 向量检索集成 | 分析时检索相关公告/新闻作为 LLM 上下文 | `services/vector_service.py` | ⬜ |
| 3.4.4 | 上下文窗口管理 | 数据压缩、摘要技术，控制传入 LLM 的 token 数量 | `services/llm_service.py` | ⬜ |

#### 3.5 自然语言策略引擎完善 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 3.5.1 | 支持技术指标字段 | 当前仅支持基本面字段，需增加 RSI/MACD/均线/涨幅等 | `engines/strategy_parser.py` | ✅ 35字段 |
| 3.5.2 | 支持资金面/事件字段 | 主力资金、北向资金、业绩预增等条件 | `engines/strategy_parser.py` | ✅ |
| 3.5.3 | 支持 OR/NOT 逻辑 | 当前仅支持 AND，需支持 OR/NOT 组合 | `engines/strategy_parser.py`, `engines/stock_filter.py` | ✅ OR已支持 |
| 3.5.4 | 冲突检测增强 | 范围冲突、过度筛选预警、条件缺失提示 | `engines/strategy_parser.py` | ✅ 范围冲突+>8条件警告 |

---

### Phase 4：前端应用开发 (预计 3-4 周)

#### 4.1 选股中心页面 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 4.1.1 | 经典策略选择 UI | 策略卡片展示(图标+描述)、参数调节滑块 | `pages/StockPicker/`, `components/StrategyForm.tsx` | ✅ 10策略分类 |
| 4.1.2 | 自定义策略输入 UI | 多行文本框 + 示例策略点击填充 + 解析结果确认界面 | `pages/StockPicker/`, `components/StrategyInput.tsx` (新增) | ✅ TextArea+条件输入 |
| 4.1.3 | 选股结果表格增强 | 排序(涨跌幅/市值/PE)、AI评分/风险等级列、点击跳转分析 | `components/StockTable.tsx` | ✅ 评分/风险/换手率列 |
| 4.1.4 | 股票搜索框 | 支持代码/名称/拼音首字母模糊搜索 | `components/StockSearch.tsx` (新增) | ✅ AutoComplete+实时行情 |

#### 4.2 个股分析页面 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 4.2.1 | 核心指标卡片 | 最新价/涨跌幅/市值/PE/PB/AI评分/风险等级/操作建议 | `pages/StockAnalysis/index.tsx` | ✅ metricsBar内联 |
| 4.2.2 | 分析报告完整展示 | 7 个分析模块按 PRD 结构展示：基本面/技术面/资金面/消息面/同行业/AI评估 | `components/AnalysisReport.tsx` | ✅ 3维度+风险Tag |
| 4.2.3 | K 线图增强 | 叠加均线(MA5/10/20/60)、成交量、支撑压力位标注、缩放拖拽 | `components/KLineChart.tsx` | ✅ MA+成交量+缩放 |
| 4.2.4 | 技术指标子图 | MACD/RSI/KDJ 副图，与 K 线联动 | `components/TechIndicatorChart.tsx` (新增) | ✅ MACD+RSI联动 |
| 4.2.5 | 财务图表 | ROE/毛利率趋势折线图、营收/净利润柱状图、雷达图 | `components/FinancialRadar.tsx` (新增) | ✅ 6维度雷达图 |
| 4.2.6 | 资金流向图 | 主力资金瀑布图、北向资金持仓变化折线图 | `components/CapitalFlowChart.tsx` (新增) | ✅ 柱状图+趋势标签 |
| 4.2.7 | AI 分析进度展示 | "正在分析基本面..."→"正在分析技术面..."分步骤进度 | `pages/StockAnalysis/index.tsx` | ✅ 5步动画进度 |

#### 4.3 策略管理页面 [P0]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 4.3.1 | 我的策略列表 | 展示已保存策略(名称/描述/创建时间/执行次数) | `pages/MyStrategy/index.tsx` | ✅ localStorage持久化 |
| 4.3.2 | 策略保存/编辑/删除 | 策略 CRUD 操作前端实现 | `pages/MyStrategy/`, `services/strategy.ts` | ✅ 新建/执行/删除 |
| 4.3.3 | 策略执行历史 | 历史执行记录表格(时间/结果数/后续涨跌幅) | `pages/MyStrategy/` | ⚠️ 显示上次执行,缺完整历史 |

#### 4.4 市场概览页面 [P1]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 4.4.1 | 大盘指数展示 | 沪深300/上证指数/创业板指实时数据+走势图 | `pages/Market/index.tsx` | ✅ 4卡片+30s刷新 |
| 4.4.2 | 板块行情热力图 | 行业板块涨跌幅热力图 | `pages/Market/` | ⚠️ 板块表格+排序,缺热力图 |
| 4.4.3 | 资金流向总览 | 北向资金/主力资金流向概览 | `pages/Market/` | ⬜ |

#### 4.5 UI/UX 通用 [P0-P1]

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 4.5.1 | 深色/浅色主题 | PRD 7.3.1 配色方案实现 | `main.tsx`, `index.css` | ✅ AntD darkAlgorithm+自定义token |
| 4.5.2 | 响应式布局 | 桌面端(左侧导航+主内容+右侧信息栏) + 平板适配 | `components/Layout/` | ✅ 1024/768断点 |
| 4.5.3 | 骨架屏加载 | 数据加载时展示页面骨架 | 各页面组件 | ⬜ |
| 4.5.4 | 错误/成功反馈 | 全局 Toast 提示优化 | `main.tsx` AntApp | ✅ maxCount+duration配置 |

---

### Phase 5：用户认证与权限 (预计 1-2 周)

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 5.1 | JWT 路由保护 | 为策略管理等需认证的 API 添加 `get_current_active_user` 依赖 | `api/v1/strategy.py`, `api/v1/analysis.py` | ⚠️ 后端已有,前端待接 |
| 5.2 | 登录/注册前端页面 | 登录表单、注册表单、Token 管理 | `pages/Login/` (新增) | ✅ Login+Register合并页 |
| 5.3 | 用户状态管理 | Zustand store 管理登录状态、用户信息 | `components/Layout/` | ✅ Header登录/登出按钮 |
| 5.4 | 路由守卫 | 未登录用户重定向到登录页 | `App.tsx`, `components/PrivateRoute.tsx` (新增) | ✅ 策略页已保护 |
| 5.5 | Refresh Token 机制 | Access Token 2h + Refresh Token 7d | `core/security.py`, `api/v1/auth.py` | ⬜ |
| 5.6 | API 限流按用户 | 每用户每分钟100次请求限制 | `core/rate_limit.py` | ⬜ |

---

### Phase 6：数据同步系统 (预计 2 周)

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 6.1 | 实时行情同步任务 | 交易时间每3秒拉取全市场行情写入 Redis | `tasks/data_sync.py` | ⬜ |
| 6.2 | 日 K 线同步任务 | 每日16:00拉取当日所有股票日K线写入 InfluxDB | `tasks/data_sync.py` | ⬜ |
| 6.3 | 财务数据同步任务 | 每日凌晨2:00拉取最新财务数据写入 PostgreSQL | `tasks/data_sync.py` | ⬜ |
| 6.4 | Celery Beat 配置 | 配置定时任务调度 | `core/celery_app.py` | ⬜ |
| 6.5 | InfluxDB 写入服务 | K 线和实时行情的时序数据写入 | `services/influxdb_service.py` (新增) | ⬜ |
| 6.6 | 容错与重试 | 任务失败重试、异常告警 | `tasks/data_sync.py` | ⬜ |
| 6.7 | WebSocket 实时推送 | 实时行情变化推送给前端 | `core/websocket.py` (新增), 前端 `hooks/useWebSocket.ts` | ⬜ |

---

### Phase 7：合规与风险声明 (预计 1 周)

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 7.1 | 风险提示组件 | 首次使用弹窗 + 分析报告底部风险提示 | `components/RiskDisclaimer.tsx` (新增) | ✅ compact+full模式 |
| 7.2 | 免责声明页面 | 完整免责声明内容 (PRD 9.2) | `pages/Disclaimer/` (新增) | ✅ 7节完整声明 |
| 7.3 | 用户协议页面 | 用户协议内容 (PRD 9.5.1) | `pages/Terms/` (新增) | ✅ 8节完整协议 |
| 7.4 | 隐私政策页面 | 隐私政策内容 (PRD 9.5.2) | `pages/Privacy/` (新增) | ✅ 8节完整政策 |
| 7.5 | 合规表达检查 | 确保所有操作建议附带"仅供参考"，不使用绝对化用语 | 全局审查 | ✅ Agent Prompt已含合规 |
| 7.6 | 数据来源声明 | 页面底部数据来源标注 | `components/Layout/Footer.tsx` | ✅ Layout Footer |

---

### Phase 8：性能优化与监控 (预计 1-2 周)

| # | 任务 | 说明 | 涉及文件 | 状态 |
|---|------|------|----------|------|
| 8.1 | L2 本地内存缓存 | 股票基础信息、板块映射的内存缓存层 | `core/cache_manager.py` | ⬜ |
| 8.2 | 缓存预热 | 服务启动时预加载热数据 | `core/cache_manager.py` | ⬜ |
| 8.3 | 数据库索引优化 | 为常用查询字段添加索引 | `alembic/versions/` | ⬜ |
| 8.4 | Grafana 监控面板 | 配置 Prometheus + Grafana 可视化面板 | `docker-compose.yml`, `grafana/` | ⬜ |
| 8.5 | 告警规则配置 | P0/P1/P2 告警规则 (PRD 8.3.3) | `core/alerting.py` | ⬜ |
| 8.6 | HTTPS 配置 | Nginx SSL 证书配置 | `nginx/` | ⬜ |
| 8.7 | 生产 Docker Compose 完善 | 添加前端/后端/Qdrant 到生产部署配置 | `docker-compose.prod.yml` | ⬜ |
| 8.8 | CI/CD 流程 | GitHub Actions：测试→构建→部署 | `.github/workflows/` | ⬜ |

---

## 三、MVP 最小可用版本范围

**MVP 目标**：用户可以使用经典策略选股、查看个股分析报告、用自然语言自定义策略。

**MVP 必须完成的任务**：

| 阶段 | 关键任务 | 优先级 |
|------|---------|--------|
| Phase 1 | 1.1.1, 1.1.5, 1.2.1-1.2.3, 1.3.1, 1.4.1 | 🔴 最高 |
| Phase 2 | 2.1.1, 2.2.1-2.2.4, 2.3.1-2.3.3, 2.4.1, 2.7.1-2.7.3 | 🔴 最高 |
| Phase 3 | 3.1.1, 3.2.1-3.2.4, 3.5.1 | 🔴 最高 |
| Phase 4 | 4.1.1-4.1.4, 4.2.1-4.2.3, 4.2.7, 4.3.1 | 🔴 最高 |
| Phase 7 | 7.1, 7.5 | 🔴 最高 |

**MVP 可延后的功能**：
- 消息面分析 (Phase 2.5)
- 同行业对比 (Phase 2.6)
- RAG 系统 (Phase 3.4)
- 数据同步系统 (Phase 6)
- 深色主题 (Phase 4.5.1)
- 策略回测
- 策略分享
- WebSocket 实时推送
- CI/CD 流程

---

## 四、建议执行顺序

```
Week 1-2:  Phase 1.1 (数据服务增强) + Phase 1.2 (前3个策略完善)
Week 3:    Phase 1.2 (技术策略) + Phase 1.3 (风险控制) + Phase 1.4 (策略API)
Week 4-5:  Phase 2.1-2.4 (分析引擎核心)
Week 6:    Phase 2.7 (综合评分) + Phase 3.1-3.2 (LLM + Prompt)
Week 7-8:  Phase 3.3 (Agent 实现) + Phase 3.5 (NL 策略完善)
Week 9-10: Phase 4.1-4.2 (选股中心 + 个股分析前端)
Week 11:   Phase 4.3 (策略管理) + Phase 5 (认证)
Week 12:   Phase 7 (合规) + Phase 8 (优化) + 集成测试
```

**总预计工期**：约 12 周（3 个月）
