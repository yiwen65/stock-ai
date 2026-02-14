# A股AI智能分析应用 — 实施计划

**文档版本**: v2.0
**更新日期**: 2026-02-14
**基于**: PRD v1.0 差距分析（当前整体完成度约 45%）
**目标**: 按优先级补齐 PRD 差距，4 周内达到 MVP 上线标准

---

## 一、当前状态摘要

### 已完成模块（无需改动）

| 模块 | 完成度 | 关键已实现内容 |
|------|--------|---------------|
| 基础架构 | 100% | Docker/FastAPI/PostgreSQL/Redis/Alembic |
| 选股策略 | 75% | 11/17 策略已实现（所有 P0 策略已覆盖） |
| 数据服务 | 60% | AKShare 行情/K线/财务/资金流向/板块/新闻/同行业，Redis L1 + 内存 L2 缓存 |
| LLM 服务 | 90% | 多模型支持(OpenAI/DeepSeek/Qwen)、主备切换、Token 统计 |
| Agent 系统 | 70% | DataAgent/FundamentalAgent/TechnicalAgent/CapitalFlowAgent/EvaluatorAgent/Orchestrator |
| NL 策略引擎 | 65% | 35 字段解析、模糊理解、OR 逻辑、冲突检测 |
| 前端核心页面 | 70% | 选股中心/个股分析/策略管理/市场概览/登录/合规页面 |
| 前端图表 | 80% | K 线(MA+成交量+缩放)/MACD+RSI/雷达图/资金流向图/杜邦图 |
| 合规声明 | 85% | 风险弹窗/免责声明/用户协议/隐私政策/数据来源声明 |
| 认证系统 | 60% | JWT 登录/注册/路由守卫/Zustand 状态管理 |

### 核心差距（待实施）

| 差距项 | 优先级 | 影响范围 |
|--------|--------|----------|
| 消息面分析完全缺失 (NewsAgent) | 🔴 P0 | 分析报告 7 模块仅完成 4 个 |
| 同行业对比分析引擎缺失 | 🔴 P0 | 数据接口有但引擎未实现 |
| 估值历史分位 + DCF 缺失 | 🔴 P0 | 估值分析不完整 |
| 杜邦分析后端缺失 | 🟡 P1 | 前端组件有但无后端计算 |
| 行业/板块过滤器 | 🔴 P0 | 风控 P0 要求未实现 |
| 前端策略用 localStorage 未接后端 | 🟡 P1 | 数据不持久/不跨设备 |
| 北向资金独立接口 | 🟡 P1 | 用主力资金代替，数据不准确 |
| Refresh Token | 🟡 P1 | Token 2h 过期后需重新登录 |
| 数据同步定时任务 | 🟢 P2 | 全靠实时拉取，性能瓶颈 |
| RAG 系统 (Qdrant) | 🟢 P2 | 无向量化/检索 |
| WebSocket 实时推送 | 🟢 P2 | 需手动刷新获取最新数据 |
| HTTPS / Grafana / CI/CD | 🟢 P2 | 生产部署需要 |

---

## 二、实施原则

1. **MVP 优先** — 只做 MVP 必须的功能，P2 功能标记为"可延后"
2. **前后端联动** — 每个功能后端 API + 前端 UI 同批交付
3. **可验证** — 每个 Sprint 结束后可独立运行和验证
4. **最小改动** — 复用已有组件和服务，避免不必要重构
5. **测试跟随** — 每个后端模块附带基础单元测试

---

## 三、分 Sprint 实施计划

### Sprint 1：分析引擎补齐（3-4 天）

> **目标**: 补齐 PRD §4 个股分析的 3 个空白模块，使分析报告达到 7 模块完整度

#### 1A. 消息面分析（NewsAgent）

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 1A.1 | 创建 `NewsAgent` | `backend/app/agents/news_agent.py` | 中 |
| | 继承 BaseAgent，Prompt 模板：公告分类（业绩/重大事项/股东变动/分红/风险）+ LLM 影响判断（利好/利空/中性） | | |
| 1A.2 | 注册到 `__init__.py` | `backend/app/agents/__init__.py` | 小 |
| 1A.3 | Orchestrator 集成 | `backend/app/agents/orchestrator.py` | 小 |
| | 并行调度增加 NewsAgent（与 Fundamental/Technical/CapitalFlow 并行），结果合入 EvaluatorAgent 上下文 | | |
| 1A.4 | Schema 扩展 | `backend/app/schemas/analysis.py` | 小 |
| | `AIAnalysisReport` 增加 `news_analysis: Optional[str]` 字段 | | |
| 1A.5 | 前端展示 | `frontend/src/components/AnalysisReport.tsx` | 中 |
| | 增加消息面折叠模块，已有 `NewsPanel.tsx` 可复用 | | |

#### 1B. 同行业对比引擎

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 1B.1 | 行业对比分析引擎 | `backend/app/engines/industry_comparator.py`（新增） | 大 |
| | 输入: stock_code → 获取行业 → 取同行业 Top N → 计算 PE/PB/ROE/增长率排名 → 输出对比表 + 行业排名 | | |
| | 复用 `data_service.fetch_peer_comparison()` 已有的行业数据 | | |
| 1B.2 | 分析报告集成 | `backend/app/engines/analyzer.py` | 小 |
| | `_fetch_analysis_data` 增加 peer comparison 数据获取，报告增加 `industry_comparison` 字段 | | |
| 1B.3 | 前端展示 | `frontend/src/components/AnalysisReport.tsx` | 中 |
| | 增加行业对比折叠模块，已有 `PeerComparison.tsx` 可复用 | | |

#### 1C. 估值分析完善

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 1C.1 | PE/PB 历史分位计算 | `backend/app/engines/analyzer.py` | 中 |
| | 从 K 线历史数据 + 当前 PE/PB 计算近 3 年/5 年百分位 | | |
| 1C.2 | 简化版 DCF 估值 | `backend/app/engines/analyzer.py` | 中 |
| | 假设未来 5 年净利润增长率=近 3 年 CAGR，折现率 10%，计算合理 PE 区间 | | |
| 1C.3 | 前端估值展示增强 | `frontend/src/components/AnalysisReport.tsx` | 小 |
| | PE/PB 历史分位用进度条展示，DCF 估值区间用标尺展示 | | |

#### 1D. 杜邦分析后端

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 1D.1 | 杜邦分析计算 | `backend/app/engines/analyzer.py` | 中 |
| | ROE = 净利率 × 总资产周转率 × 权益乘数，5 年趋势 + 驱动因子识别 | | |
| | 财务数据需补充：总资产周转率、权益乘数（从 `fetch_financial_data` 提取或计算） | | |
| 1D.2 | Schema 增加杜邦字段 | `backend/app/schemas/analysis.py` | 小 |
| | `FundamentalAnalysis` 增加 `dupont: Optional[DuPontAnalysis]` | | |
| 1D.3 | 前端对接 | `frontend/src/components/DuPontChart.tsx` | 小 |
| | 已有组件，改为使用后端返回的真实数据 | | |

**Sprint 1 验收标准**:
- [ ] AI 分析报告包含 7 个完整模块：基本面/技术面/资金面/消息面/同行业对比/杜邦分析/AI 综合评估
- [ ] 消息面展示近期公告 + LLM 影响判断
- [ ] 同行业对比展示至少 3 家公司 PE/PB/ROE 横向对比
- [ ] PE/PB 显示历史分位百分比
- [ ] 杜邦分析使用真实财务数据

---

### Sprint 2：风控补齐 + 策略持久化（3 天）

> **目标**: 补齐 P0 风控缺失 + 前端策略管理对接后端 API

#### 2A. 行业/板块过滤器

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 2A.1 | 行业过滤实现 | `backend/app/engines/risk_filter.py` | 中 |
| | 支持 `include_industries` 和 `exclude_industries` 参数 | | |
| | 通过 `data_service.fetch_peer_comparison` 获取股票所属行业，或从全市场快照中扩展行业字段 | | |
| 2A.2 | 策略执行 API 增加行业参数 | `backend/app/schemas/strategy.py` | 小 |
| | `StrategyExecuteRequest` 增加 `include_industries` / `exclude_industries` 可选参数 | | |
| 2A.3 | 前端行业筛选 UI | `frontend/src/components/StrategyForm.tsx` | 中 |
| | 增加行业多选下拉框（申万一级行业列表） | | |

#### 2B. 前端策略管理对接后端

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 2B.1 | Alembic 迁移检查 | `backend/alembic/versions/` | 小 |
| | 确认 `user_strategies` 和 `strategy_executions` 表的迁移已存在且可执行 | | |
| 2B.2 | 前端 `strategy.ts` 对接后端 API | `frontend/src/services/strategy.ts` | 中 |
| | 替换 localStorage 调用为 `/api/v1/strategy/user/*` 后端 API | | |
| | 已有后端 CRUD API：`/user/list`, `/user/create`, `/user/{id}` (PUT/DELETE) | | |
| 2B.3 | `MyStrategy` 页面适配 | `frontend/src/pages/MyStrategy/index.tsx` | 中 |
| | 登录态：从后端获取策略列表；未登录态：提示登录 | | |
| | 执行策略后调用 `/user/{id}/executions` 记录执行历史 | | |
| 2B.4 | 策略执行历史展示 | `frontend/src/pages/MyStrategy/index.tsx` | 中 |
| | 点击策略展开历史执行记录表格（时间/结果数量/结果快照预览） | | |

#### 2C. 北向资金独立接口

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 2C.1 | 北向资金数据接入 | `backend/app/services/data_service.py` | 中 |
| | 接入 `ak.stock_hsgt_north_net_flow_in_em` 获取沪深港通每日净流入 | | |
| | 接入 `ak.stock_hsgt_hold_stock_em` 获取个股北向持仓数据 | | |
| 2C.2 | 北向资金分析增强 | `backend/app/engines/analyzer.py` | 小 |
| | 资金面分析增加北向持仓变化趋势 | | |

**Sprint 2 验收标准**:
- [ ] 选股支持按行业筛选/排除
- [ ] 登录用户策略保存到数据库，跨设备可用
- [ ] 策略执行历史可查看
- [ ] 北向资金使用独立数据接口（非主力资金代替）

---

### Sprint 3：认证增强 + 市场页升级（2-3 天）

> **目标**: 安全机制闭环 + 市场概览页体验提升

#### 3A. 认证增强

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 3A.1 | Refresh Token 后端 | `backend/app/core/security.py`, `backend/app/api/v1/auth.py` | 中 |
| | 登录返回 access_token (2h) + refresh_token (7d) | | |
| | 新增 `POST /api/v1/auth/refresh` 端点 | | |
| 3A.2 | 前端 Token 自动刷新 | `frontend/src/services/api.ts` | 中 |
| | Axios response interceptor：401 → 自动用 refresh_token 重试 → 失败则跳转登录 | | |
| 3A.3 | 按用户限流 | `backend/app/core/rate_limit.py` | 小 |
| | 从全局 IP 限流增强为 per-user 限流 (100 次/分钟) | | |

#### 3B. 市场概览升级

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 3B.1 | 板块热力图 | `frontend/src/pages/Market/index.tsx` | 大 |
| | 已有 `SectorHeatmap.tsx`，集成到市场页替换/增强板块表格 | | |
| | ECharts Treemap，颜色映射涨跌幅（红涨绿跌），面积映射成交额 | | |
| 3B.2 | 资金流向总览 | `frontend/src/pages/Market/index.tsx` | 中 |
| | 已有 `MarketCapitalFlow.tsx`，集成到市场页 | | |
| | 展示行业资金流向 Top10（流入/流出），复用 `data_service.fetch_market_capital_flow()` | | |

**Sprint 3 验收标准**:
- [ ] Token 过期后自动刷新，用户无感知
- [ ] API 按用户限流生效
- [ ] 市场概览页展示板块热力图（Treemap）
- [ ] 市场概览页展示行业资金流向排行

---

### Sprint 4：P1 策略 + 前端体验优化（2-3 天）

> **目标**: 补齐缺失的 P1 策略 + 前端体验打磨

#### 4A. 补齐缺失策略

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 4A.1 | 股东增持/回购策略 | `backend/app/engines/strategies/shareholder_increase.py`（新增） | 中 |
| | PRD §3.5.2：近 30 日增持公告 + 增持金额>1000 万 + 低位增持 | | |
| 4A.2 | 双动量策略 | `backend/app/engines/strategies/dual_momentum.py`（新增） | 中 |
| | PRD §3.3.2：绝对动量（60 日涨幅>10%）+ 相对动量（跑赢沪深 300）+ 回撤控制 | | |
| 4A.3 | 注册到策略 Registry | `backend/app/api/v1/strategy.py` | 小 |
| | STRATEGY_REGISTRY 增加新策略，Schema 增加策略类型 | | |
| 4A.4 | 前端策略卡片更新 | `frontend/src/components/StrategyForm.tsx` | 小 |
| | 增加新策略的卡片描述和图标 | | |

#### 4B. 前端体验优化

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 4B.1 | 骨架屏集成 | 各页面组件 | 小 |
| | 已有 `PageSkeleton.tsx`，确保所有数据加载页面使用骨架屏 | | |
| 4B.2 | 分析报告锚点导航 | `frontend/src/pages/StockAnalysis/index.tsx` | 小 |
| | 已有 `AnchorNav.tsx`，确认集成到分析页右侧 | | |
| 4B.3 | 综合评分权重调整 | `backend/app/engines/analyzer.py` | 小 |
| | 消息面接入后，恢复 PRD 5 维权重：基本面 35% + 技术面 25% + 资金面 20% + 估值 15% + 消息面 5% | | |
| | 当前简化为 3 维（45%/30%/25%），需拆回 5 维 | | |

**Sprint 4 验收标准**:
- [ ] 新增 2 个选股策略可用
- [ ] 所有页面数据加载有骨架屏
- [ ] 分析报告有锚点导航
- [ ] 综合评分使用 PRD 5 维权重

---

### Sprint 5（可选）：数据同步 + 生产部署（3-4 天）

> **目标**: 生产环境准备，MVP 可延后

#### 5A. 数据同步系统

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 5A.1 | Celery Beat 定时任务 | `backend/app/core/celery_app.py`, `backend/app/tasks/data_sync.py` | 中 |
| | 交易时间每 30s 拉取全市场行情写入 Redis（3s 级别需 WebSocket） | | |
| | 每日 16:00 拉取当日 K 线写入缓存 | | |
| | 每日凌晨 2:00 拉取财务数据 | | |
| 5A.2 | InfluxDB 写入服务 | `backend/app/services/influxdb_service.py`（新增） | 中 |
| | K 线时序数据写入 InfluxDB，替代每次实时拉取 | | |
| 5A.3 | 容错与重试 | `backend/app/tasks/data_sync.py` | 小 |
| | Celery 任务失败重试（max_retries=3, countdown=60） | | |

#### 5B. WebSocket 实时推送

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 5B.1 | FastAPI WebSocket 端点 | `backend/app/core/websocket.py`（新增） | 大 |
| | `/ws/realtime/{stock_code}` 推送实时行情变化 | | |
| 5B.2 | 前端 WebSocket Hook | `frontend/src/hooks/useWebSocket.ts`（新增） | 中 |
| | 连接管理 + 自动重连 + 数据更新到 Zustand store | | |

#### 5C. 生产部署

| # | 任务 | 涉及文件 | 工作量 |
|---|------|----------|--------|
| 5C.1 | 生产 Docker Compose 完善 | `docker-compose.prod.yml` | 中 |
| | 前端 Nginx + 后端 Gunicorn + PostgreSQL + Redis + Celery Worker/Beat | | |
| 5C.2 | HTTPS + Nginx SSL | `nginx/nginx.conf` | 小 |
| 5C.3 | CI/CD 流程 | `.github/workflows/ci.yml`, `.github/workflows/deploy.yml` | 中 |
| | GitHub Actions: lint → test → build Docker → deploy | | |
| 5C.4 | Grafana 监控面板 | `docker-compose.prod.yml`, `grafana/` | 中 |
| | Prometheus + Grafana 基础面板（QPS/响应时间/错误率/CPU/内存） | | |

**Sprint 5 验收标准**:
- [ ] 定时任务自动同步市场数据
- [ ] `docker-compose -f docker-compose.prod.yml up` 一键部署
- [ ] GitHub Actions CI/CD 流程通过
- [ ] HTTPS 可用

---

## 四、时间线总览

```
Sprint 1 (Day 1-4):   分析引擎补齐（消息面/行业对比/估值/杜邦）
Sprint 2 (Day 5-7):   风控补齐 + 策略持久化 + 北向资金
Sprint 3 (Day 8-10):  认证增强 + 市场页升级
Sprint 4 (Day 11-13): P1 策略 + 前端体验优化
Sprint 5 (Day 14-17): [可选] 数据同步 + 生产部署
```

**MVP 核心工期**: Sprint 1-4 ≈ **2.5 周（13 个工作日）**
**完整版工期**: Sprint 1-5 ≈ **3.5 周（17 个工作日）**

---

## 五、依赖关系图

```
Sprint 1A (NewsAgent) ──────┐
Sprint 1B (行业对比) ───────┤
Sprint 1C (估值完善) ───────┼── Sprint 4B.3 (5维权重)
Sprint 1D (杜邦分析) ───────┘
                              
Sprint 2A (行业过滤) ── 独立
Sprint 2B (策略持久化) ── 依赖后端 CRUD API 已存在 (✅)
Sprint 2C (北向资金) ── 独立

Sprint 3A (Refresh Token) ── 独立
Sprint 3B (市场页升级) ── 依赖已有组件 (SectorHeatmap/MarketCapitalFlow)

Sprint 4A (新策略) ── 独立
Sprint 4B (体验优化) ── 依赖 Sprint 1 完成

Sprint 5 (生产部署) ── 依赖 Sprint 1-4 全部完成
```

---

## 六、风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AKShare 公告/行业接口变动 | Sprint 1A/1B 受阻 | 降级方案：使用 `stock_news_em` 替代公告接口；行业数据已有 `fetch_peer_comparison` 可复用 |
| LLM API 成本增加 | NewsAgent 增加 token 消耗 | 新闻数量限制 10 条 + 摘要压缩；使用低成本模型 (DeepSeek) 做消息面分析 |
| 杜邦分析数据不全 | 总资产周转率/权益乘数可能缺失 | 从现有字段计算：周转率=营收/总资产，权益乘数=1/(1-负债率) |
| 前端策略迁移 | localStorage 已有数据丢失 | 前端增加迁移逻辑：首次登录时读取 localStorage → 批量 POST 到后端 → 清空 localStorage |
| Celery 环境复杂性 | Sprint 5 部署困难 | Celery 标记为可选；MVP 阶段继续使用实时拉取 + 缓存方案 |

---

## 七、MVP 上线检查清单

### 功能完整性（Sprint 1-4 完成后）
- [ ] 11+ 选股策略可执行（含自然语言策略）
- [ ] 个股分析报告含 7 个模块（基本面/技术面/资金面/消息面/行业对比/杜邦/AI 评估）
- [ ] K 线图支持日/周/月 + MACD/RSI/KDJ 技术指标
- [ ] PE/PB 历史分位 + DCF 估值区间
- [ ] 策略 CRUD 持久化到数据库 + 执行历史
- [ ] 市场概览：大盘指数 + 板块热力图 + 资金流向
- [ ] 选股支持行业筛选/排除

### 合规检查
- [ ] 首次使用风险提示弹窗 ✅（已实现）
- [ ] 免责声明/用户协议/隐私政策完整 ✅（已实现）
- [ ] 所有操作建议附带"仅供参考" ✅（已实现）
- [ ] 无绝对化用语 ✅（已实现）
- [ ] 数据来源声明 ✅（已实现）

### 安全检查
- [ ] JWT + Refresh Token（Sprint 3 完成）
- [ ] 路由守卫 ✅（已实现）
- [ ] API 按用户限流（Sprint 3 完成）
- [ ] 密码 bcrypt 哈希 ✅（已实现）

### 性能检查
- [ ] 页面加载 <2 秒（骨架屏）
- [ ] 选股执行 <5 秒
- [ ] 分析报告生成 <20 秒
- [ ] TypeScript 编译 0 错误

---

## 八、MVP 可延后功能

以下功能标记为 Phase 2（MVP 后迭代）：

- P2 策略：布林带收口/ATR 通道/Fama-French 三因子/小市值低估值
- 策略回测（PRD §5.5.3）
- 策略分享（PRD §5.4.3）
- NOT 逻辑 / 嵌套条件（PRD §5.5.1）
- T+5/T+10 后续涨跌幅追踪（PRD §5.4.4）
- RAG 系统（Qdrant 向量检索）
- 自选股功能（PRD §7.1.1）
- 报告导出 PDF（PRD §7.2.2）
- WebSocket 实时推送
- 数据备份策略
- 模型微调 / 强化学习
- 多市场支持（港股/美股）
- 移动端适配
