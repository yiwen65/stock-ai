# PRD v1.0 vs 当前实施 — 差距分析报告

**生成日期**: 2026-02-14（第二次检查）
**整体完成度**: ≈ 78%（MVP 标准 ≈ 90%）

> 与首次检查相比，5 项 P0 差距已全部修复，完成度从 72% 提升至 78%。

---

## 一、总览评分

| PRD 模块 | 优先级 | 完成度 | 状态 | 变化 |
|----------|--------|--------|------|------|
| §2 数据层 | P0 | 70% | 🟡 | — |
| §3 选股策略 | P0 | 90% | 🟢 | ↑5% |
| §4 个股分析 | P0 | 88% | 🟢 | ↑8% |
| §5 自然语言策略引擎 | P0 | 80% | � | ↑10% |
| §6 AI 分析引擎 | P1 | 75% | 🟡 | — |
| §7 用户交互与界面 | P0 | 80% | � | ↑10% |
| §8 非功能性需求 | P0-P2 | 60% | � | ↑5% |
| §9 合规与风险声明 | P0 | 85% | 🟢 | — |
| §10 技术架构 | P0 | 80% | 🟢 | — |

---

## 二、逐模块详细分析

### §2 数据层 — 70%

#### ✅ 已完成
- **AKShare 主数据源**：行情/K线/财务/资金流向/板块/新闻/同行业对比
- **Redis L1 + 内存 L2 缓存**：两级缓存架构
- **北向资金数据**：`fetch_northbound_flow()` + `fetch_northbound_stock_holding()`
- **板块/概念数据**：申万行业分类、板块行情

#### ❌ 未完成

| 差距项 | PRD 优先级 | 影响 | 建议 |
|--------|-----------|------|------|
| Tushare/BaoStock 备用数据源未接入 | P1 | 数据源单点故障风险 | Phase 2，MVP 可接受 |
| 数据源容错/主备切换机制 | P1 | AKShare 故障时服务不可用 | 建议加 try/except 降级逻辑 |
| L3 InfluxDB 时序缓存未真正使用 | P2 | data_sync.py 引用了但无实际 InfluxDB service | docker-compose.prod.yml 有 InfluxDB 容器但 `get_influxdb()` 可能未实现 |
| 融资融券数据 | P1 | 资金面分析不完整 | 用 `ak.stock_margin_detail_szse` 补充 |
| 龙虎榜数据 | P1 | 事件驱动分析缺失 | 用 `ak.stock_lhb_detail_em` 补充 |
| 股东变动数据 | P1 | 股东增持策略用北向资金代理 | Tushare 有接口，MVP 可接受 |
| 宏观经济数据 | P2 | 风格轮动分析缺失 | Phase 2 |
| 数据质量校验规则 | P1 | 无价格/成交量合理性校验 | 建议加基础校验 |

---

### §3 选股策略 — 90%

#### ✅ 已完成（13/17 策略）

| 策略 | PRD 章节 | 优先级 | 文件 |
|------|---------|--------|------|
| 格雷厄姆价值投资 | §3.1.1 | P0 | `graham.py` |
| 巴菲特护城河 | §3.1.2 | P0 | `buffett.py` |
| PEG 成长策略 | §3.1.3 | P1 | `peg.py` |
| 彼得·林奇成长 | §3.1.3 | P1 | `lynch.py` |
| 均线多头排列 | §3.2.1 | P0 | `ma_breakout.py` |
| MACD 底背离 | §3.2.2 | P1 | `macd_divergence.py` |
| 放量突破平台 | §3.2.3 | P0 | `volume_breakout.py` |
| RS 相对强度动量 | §3.3.1 | P1 | `rs_momentum.py` |
| 双动量策略 | §3.3.2 | P1 | `dual_momentum.py` |
| 质量因子选股 | §3.4.2 | P1 | `quality_factor.py` |
| 业绩预增驱动 | §3.5.1 | P0 | `earnings_surprise.py` |
| 股东增持/回购 | §3.5.2 | P1 | `shareholder_increase.py` |
| 北向资金持续流入 | §3.5.3 | P0 | `northbound.py` |

#### ❌ 未完成（4 策略，均 P2）

| 策略 | PRD 章节 | 优先级 | 说明 |
|------|---------|--------|------|
| 布林带收口突破 | §3.2.4 | P2 | Phase 2 |
| ATR 通道趋势跟踪 | §3.3.3 | P2 | Phase 2 |
| Fama-French 三因子 | §3.4.1 | P2 | Phase 2 |
| 小市值+低估值组合 | §3.4.3 | P2 | Phase 2 |

#### 风控维度 §3.6

| 风控项 | 状态 | 说明 |
|--------|------|------|
| ST/停牌/退市排除 | ✅ | `risk_filter.py` |
| 流动性筛选（成交额/换手率） | ✅ | `stock_filter.py` |
| 市值范围筛选 | ✅ | `stock_filter.py` |
| 行业/板块过滤 | ✅ | `risk_filter.py` + `/industries` API |
| 综合风险评分 1-10 | ✅ | `risk_scorer.py` |
| 次新股排除 | ⚠️ 部分 | 非默认启用 |
| 涨跌停排除 | ⚠️ 部分 | 快照中检查但未强制 |

---

### §4 个股分析 — 88%

#### 分析报告 7 模块对照

| 模块 | PRD 章节 | 状态 | 说明 |
|------|---------|------|------|
| 基本面分析 | §4.2 | ✅ | 盈利/偿债/成长/估值/杜邦分析 |
| 技术面分析 | §4.3 | ✅ | 趋势/支撑压力/MACD/RSI/KDJ/BOLL |
| 资金面分析 | §4.4 | ✅ | 主力资金+北向资金 |
| 消息面分析 | §4.5 | ✅ | `NewsAgent` 公告分类+LLM 影响判断 |
| 同行业对比 | §4.6 | ✅ | `IndustryComparator` PE/PB/ROE 横向对比 |
| AI 综合评估 | §4.7 | ✅ | `EvaluatorAgent` 综合评分+操作建议 |
| 杜邦分析 | §4.2.2 | ✅ | `DuPontAnalysis` 三因子拆解+驱动因子识别 |

#### ❌ 剩余差距

| 差距项 | PRD 章节 | 优先级 | 影响 |
|--------|---------|--------|------|
| ~~综合评分仍用 3 维权重~~ | §4.7.1 | ~~P0~~ | ✅ 已修复：5 维权重 35/25/20/15/5 + `_score_news()` |
| DCF 现金流折现估值缺失 | §4.2.4 | P1 | 估值仅有 PE/PB 分位，无绝对估值 |
| 筹码分布分析 | §4.4.2 | P1 | 获利盘/套牢盘/筹码集中度未实现 |
| 行业政策影响分析 | §4.5.2 | P2 | NewsAgent 只分析个股公告，未分析行业政策 |
| 市场情绪判断 | §4.5.3 | P2 | 未实现涨跌停家数/融资融券/整体情绪指标 |
| 置信度标注 | §6.5.3 | P1 | 分析结论无置信度等级标注 |

---

### §5 自然语言策略引擎 — 80%

#### ✅ 已完成
- NL 解析：35 字段映射、模糊理解、OR 逻辑
- 冲突检测：逻辑冲突/范围冲突/过度筛选
- 策略保存/编辑/删除（后端 CRUD API）
- 策略执行历史记录（后端 API 存在）

#### ❌ 差距

| 差距项 | PRD 章节 | 优先级 | 影响 |
|--------|---------|--------|------|
| ~~前端未展示策略执行历史~~ | §5.4.4 | ~~P1~~ | ✅ 已修复：`ExecutionHistory` 组件 + expandable table + 自动记录 |
| NOT 逻辑 | §5.5.1 | P1 | 仅支持 AND/OR，不支持 NOT |
| 动态参数滑块 | §5.5.2 | P2 | 无 UI 滑块调参 |
| 策略回测 | §5.5.3 | P2 | Phase 3 功能 |
| 策略分享 | §5.4.3 | P2 | Phase 3 功能 |
| T+5/T+10 后续涨跌幅追踪 | §5.4.4 | P1 | 执行历史无后续表现追踪 |

---

### §6 AI 分析引擎 — 75%

#### ✅ 已完成
- **LLM 服务**：多模型支持（OpenAI/DeepSeek/Qwen），主备切换，Token 统计
- **多 Agent 架构**：DataAgent → Fundamental/Technical/CapitalFlow/News (并行) → Evaluator
- **Orchestrator**：任务分解+Agent 调度+结果汇总
- **Prompt 工程**：各 Agent 专业提示词模板
- **结果可解释性**：分析结论附带推理过程和数据依据

#### ❌ 差距

| 差距项 | PRD 章节 | 优先级 | 影响 |
|--------|---------|--------|------|
| **RAG 系统（Qdrant 向量检索）** | §6.3 | P1 | `vector_service.py` / `embedding_service.py` 文件存在但未集成到分析流程 |
| Few-Shot / CoT Prompt 优化 | §6.2.2 | P1 | 未系统实施 Few-Shot 示例 |
| 置信度标注 | §6.5.3 | P1 | 无高/中/低置信度标注 |
| 模型微调/强化学习 | §6.6 | P2 | Phase 3 |

---

### §7 用户交互与界面 — 70%

#### ✅ 已完成的页面

| 页面 | PRD 章节 | 状态 | 组件 |
|------|---------|------|------|
| 选股中心 | §7.1.1 | ✅ | `StockPicker` + `StrategyForm` + `StockTable` |
| 个股分析 | §7.1.1 | ✅ | `StockAnalysis` + `AnalysisReport` + `KLineChart` + `TechIndicatorChart` |
| 我的策略 | §7.1.1 | ✅ | `MyStrategy` (CRUD + 执行) |
| 市场概览 | §7.1.1 | ✅ | `Market` + `SectorHeatmap` + `MarketCapitalFlow` |
| 登录 | - | ✅ | `Login` |
| 合规页面 | §9 | ✅ | `Disclaimer` + `Terms` + `Privacy` |

#### ✅ 已完成的图表

| 图表 | PRD 章节 | 组件 |
|------|---------|------|
| K 线图 (日/周/月 + MA + 成交量 + 缩放) | §7.4.1 | `KLineChart.tsx` |
| MACD + RSI 技术指标 | §7.4.2 | `TechIndicatorChart.tsx` |
| 财务雷达图 | §7.4.3 | `FinancialRadar.tsx` |
| 资金流向图 | §7.4.4 | `CapitalFlowChart.tsx` |
| 杜邦分析图 | §7.4.3 | `DuPontChart.tsx` |
| 板块热力图 | §7.4.5 | `SectorHeatmap.tsx` |
| 行业资金流向 | §7.4.4 | `MarketCapitalFlow.tsx` |

#### ✅ 已完成的 UX 组件

| 组件 | PRD 章节 | 说明 |
|------|---------|------|
| 骨架屏 | §7.6.1 | `PageSkeleton.tsx`（picker/analysis/market 三种） |
| 锚点导航 | §7.2.2 | `AnchorNav.tsx`（分析页右侧） |
| 风险提示弹窗 | §9.1.1 | `RiskDisclaimerModal.tsx` |
| 搜索框 | §7.2.2 | `StockSearch.tsx` |
| 路由守卫 | §8.2.3 | `PrivateRoute.tsx` |

#### ❌ 差距

| 差距项 | PRD 章节 | 优先级 | 说明 |
|--------|---------|--------|------|
| ~~StrategyForm 缺少行业筛选 UI~~ | §2A/§3.6.4 | ~~P0~~ | ✅ 已修复：限定/排除行业多选下拉框 |
| ~~StrategyForm 缺少双动量/股东增持~~ | §3.3.2/§3.5.2 | ~~P1~~ | ✅ 已修复：添加到 STRATEGIES 列表 |
| ~~前端未展示策略执行历史~~ | §5.4.4 | ~~P1~~ | ✅ 已修复：ExecutionHistory 子组件 |
| 自选股功能 | §7.1.1 | P1 | 无自选股页面/功能 |
| 报告导出 PDF | §7.2.2 | P2 | 未实现 |
| KDJ 技术指标图 | §7.4.2 | P1 | MACD/RSI 有，KDJ 未单独展示 |
| 行业对比散点图/气泡图 | §7.4.5 | P1 | 仅有表格对比，无图表 |
| 财务趋势折线图（ROE/毛利率） | §7.4.3 | — | ✅ 已确认集成：`FinancialTrendChart.tsx` 在 StockAnalysis 页面渲染 |
| 深色/浅色主题切换 | §7.3.1 | P1 | 仅深色主题 |
| 响应式平板适配 | §7.5.2 | P1 | 基础响应式有，平板优化不足 |

---

### §8 非功能性需求 — 60%

#### ✅ 已完成

| 需求 | PRD 章节 | 说明 |
|------|---------|------|
| JWT 认证 | §8.2.3 | access_token(2h) + refresh_token(7d) + 前端自动刷新 |
| 密码 bcrypt 哈希 | §8.2.1 | ✅ |
| IP 限流 | §8.2.3 | `rate_limit.py` 100 次/分钟 |
| CI 流程 | §8.3 | `.github/workflows/ci.yml` lint → test → build |
| CD 流程 | §8.3 | `.github/workflows/deploy.yml` SSH 部署 |
| Celery 定时任务 | §2.3.3 | `celery_app.py` + `data_sync.py` + `cache_warmup.py` |
| Docker 生产部署 | §10 | `docker-compose.prod.yml` |
| Nginx 反向代理 | §10 | `nginx/nginx.conf` |
| 结构化日志 | §8.3.4 | `core/logging.py` |
| 告警系统 | §8.3.3 | `core/alerting.py` |
| 性能监控 | §8.3.3 | `core/metrics.py` + `core/profiler.py` |

#### ❌ 差距

| 差距项 | PRD 章节 | 优先级 | 说明 |
|--------|---------|--------|------|
| ~~限流未支持 per-user~~ | §8.2.3 | ~~P0~~ | ✅ 已修复：已登录用户按 user_id，匿名按 IP |
| HTTPS / SSL | §8.2.1 | P0 (生产) | nginx.conf 仅 listen 80，无 SSL 配置 |
| Grafana / Prometheus 监控面板 | §8.3.3 | P2 | docker-compose.prod.yml 无 Grafana 容器 |
| InfluxDB service 未实现 | §2.3.2 | P2 | `data_sync.py` 引用 `get_influxdb()` 但实际 service 可能未完成 |
| 数据备份策略 | §8.2.4 | P1 | 无自动备份脚本 |
| 压力测试 | §8.1.2 | P2 | 无 JMeter/Locust 脚本 |
| WebSocket 实时推送 | §2.3.3 | P2 | nginx.conf 有 /ws 代理但后端无 WebSocket 端点 |
| RBAC 权限控制 | §8.2.3 | P1 | 仅有登录态校验，无角色权限 |

---

### §9 合规与风险声明 — 85%

#### ✅ 已完成
- 首次使用风险提示弹窗（`RiskDisclaimerModal.tsx`）
- 免责声明页面（`/disclaimer`）
- 用户协议页面（`/terms`）
- 隐私政策页面（`/privacy`）
- 分析报告底部风险提示（`RiskDisclaimer.tsx`）
- 数据来源声明
- 无绝对化用语

#### ⚠️ 需检查
- 选股结果页面是否有风险提示（PRD §9.1.1 要求页面顶部或底部）
- 资质声明是否完整展示

---

### §10 技术架构 — 80%

#### ✅ 已完成
- React 18 + Ant Design + ECharts + Vite + CSS Modules
- FastAPI + SQLAlchemy + Alembic + PostgreSQL + Redis
- Zustand 状态管理
- React Router v6 路由
- React Query 数据获取
- Docker + Docker Compose 容器化
- 多 Agent 协作架构

#### ❌ 差距
- 向量数据库 Qdrant 未集成（文件存在但未连接）
- 无 SDK 或 Webhook 扩展
- 无多市场支持预留接口

---

## 三、已修复的 P0 差距（本轮）

以下 **5 项** P0 差距已在本轮全部修复：

| # | 差距项 | 状态 | 修复文件 |
|---|--------|------|----------|
| 1 | ~~综合评分权重从 3 维改为 5 维~~ | ✅ 已修复 | `analyzer.py` — 权重改为 35/25/20/15/5，新增 `_score_news()`，`_fetch_analysis_data` 并发获取新闻 |
| 2 | ~~前端 StrategyForm 添加行业筛选下拉框~~ | ✅ 已修复 | `StrategyForm.tsx` — 添加限定/排除行业 `Select mode="multiple"`，`strategy.ts` 添加 `listIndustries()` |
| 3 | ~~StrategyForm 同步新增策略~~ | ✅ 已修复 | `StrategyForm.tsx` — 添加 dual_momentum 和 shareholder_increase |
| 4 | ~~限流增强为 per-user~~ | ✅ 已修复 | `rate_limit.py` — 已登录用户用 `rate_limit:user:{id}` key，匿名用 `rate_limit:ip:{ip}` |
| 5 | ~~前端策略执行历史展示~~ | ✅ 已修复 | `MyStrategy/index.tsx` — `ExecutionHistory` 子组件 + expandable table + 自动记录执行 |

---

## 四、MVP 可延后功能清单

以下功能标记为 **Phase 2+**，MVP 上线后迭代：

- P2 策略：布林带收口 / ATR 通道 / Fama-French 三因子 / 小市值低估值
- 策略回测（PRD §5.5.3）
- 策略分享（PRD §5.4.3）
- NOT 逻辑 / 嵌套条件（PRD §5.5.1）
- T+5/T+10 后续涨跌幅追踪（PRD §5.4.4）
- DCF 绝对估值（PRD §4.2.4）
- 筹码分布分析（PRD §4.4.2）
- RAG 系统 Qdrant 集成
- 自选股功能（PRD §7.1.1）
- 报告导出 PDF（PRD §7.2.2）
- WebSocket 实时推送
- HTTPS / SSL 证书
- Grafana 监控面板
- 数据备份策略
- 深色/浅色主题切换
- 多市场支持（港股/美股）
- 移动端适配
- 模型微调 / 强化学习

---

## 五、建议下一步行动

**已完成**（Sprint 5）：
- ~~修复 `analyzer.py` 综合评分 5 维权重~~ ✅
- ~~`StrategyForm.tsx` 添加行业筛选 + 新策略~~ ✅
- ~~`rate_limit.py` 增加 per-user 限流~~ ✅
- ~~`MyStrategy` 添加执行历史展示~~ ✅

**下一步 — Sprint 6**（P1 级别，预计 2-3 天）：
1. DCF 简化估值（`analyzer.py` 新增 `_score_dcf`）
2. 自选股功能（后端 watchlist CRUD + 前端页面）
3. KDJ 技术指标图（`TechIndicatorChart.tsx` 补 KDJ 子图）
4. 行业对比散点图/气泡图（`PeerComparison.tsx` 增加 ECharts scatter）
5. 置信度标注（Agent 输出添加 confidence 字段）

**Sprint 7**（P1-P2，预计 2-3 天）：
6. HTTPS / SSL 配置（nginx.conf + certbot）
7. 深色/浅色主题切换
8. NOT 逻辑支持（strategy_parser.py）
9. 数据备份脚本（pg_dump + cron）

**Phase 2 迭代**：
10. RAG 系统 Qdrant 集成
11. Grafana 监控面板
12. 策略回测
13. P2 策略补齐（布林带/ATR/FF3/小市值）
14. 报告导出 PDF
15. 移动端适配
