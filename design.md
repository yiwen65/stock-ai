# A股股票AI智能分析应用 技术设计文档

**文档版本**: v1.0
**创建日期**: 2026-02-12
**基于**: PRD v1.0
**目标**: MVP阶段技术实现方案

---

## 目录

1. [系统架构设计](#1-系统架构设计)
2. [数据库设计](#2-数据库设计)
3. [API设计](#3-api设计)
4. [核心模块设计](#4-核心模块设计)
5. [AI引擎设计](#5-ai引擎设计)
6. [数据同步设计](#6-数据同步设计)
7. [缓存策略设计](#7-缓存策略设计)
8. [安全设计](#8-安全设计)
9. [部署架构](#9-部署架构)
10. [监控与日志](#10-监控与日志)

---

## 1. 系统架构设计

### 1.1 整体架构

采用**分层架构 + 微服务化**设计，确保系统可扩展、可维护。

```
┌─────────────────────────────────────────────────────────┐
│                    客户端层                              │
│  Web浏览器 (React + Ant Design + ECharts)               │
└─────────────────┬───────────────────────────────────────┘
                  ↓ HTTPS
┌─────────────────────────────────────────────────────────┐
│                  接入层                                  │
│  Nginx (负载均衡 + 反向代理 + 静态资源)                 │
└─────────────────┬───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│                  应用层 (FastAPI)                        │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │选股服务  │  │分析服务  │  │策略服务  │  │用户服务││
│  │StockPick │  │Analysis  │  │Strategy  │  │User    ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└─────────────────┬───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│                  业务逻辑层                              │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │ 选股引擎         │  │ 分析引擎         │           │
│  │ - 经典策略       │  │ - 基本面分析     │           │
│  │ - 自定义策略     │  │ - 技术面分析     │           │
│  │ - 条件筛选       │  │ - 资金面分析     │           │
│  └──────────────────┘  └──────────────────┘           │
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │ AI引擎           │  │ 数据服务         │           │
│  │ - LLM集成        │  │ - 数据获取       │           │
│  │ - Agent编排      │  │ - 数据清洗       │           │
│  │ - RAG检索        │  │ - 指标计算       │           │
│  └──────────────────┘  └──────────────────┘           │
└─────────────────┬───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│                  数据访问层                              │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │PostgreSQL│  │InfluxDB  │  │Redis     │  │Qdrant  ││
│  │关系数据  │  │时序数据  │  │缓存      │  │向量    ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└─────────────────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│                  外部数据源                              │
│  AKShare / Tushare Pro / BaoStock / LLM API             │
└─────────────────────────────────────────────────────────┘
```

**架构特点**：
- **分层解耦**：各层职责清晰，便于维护和测试
- **服务化**：核心服务独立部署，支持水平扩展
- **缓存优先**：多级缓存减少数据库压力
- **异步处理**：长时间任务异步执行，提升响应速度

### 1.2 技术栈选型

**前端技术栈**：
```yaml
框架: React 18.2+
语言: TypeScript 5.0+
UI组件库: Ant Design 5.x
图表库: Apache ECharts 5.x
状态管理: Zustand 4.x
数据获取: TanStack Query (React Query) 5.x
路由: React Router 6.x
构建工具: Vite 5.x
CSS方案: Tailwind CSS 3.x
HTTP客户端: Axios 1.x
```

**后端技术栈**：
```yaml
框架: FastAPI 0.110+
语言: Python 3.11+
异步运行时: uvicorn + asyncio
ORM: SQLAlchemy 2.0+
数据验证: Pydantic 2.x
任务队列: Celery 5.x + Redis
定时任务: APScheduler 3.x
数据分析: Pandas 2.x + NumPy 1.x
技术指标: TA-Lib 0.4.x
LLM集成: LangChain 0.1.x + OpenAI SDK
HTTP客户端: httpx (异步)
```

**数据库技术栈**：
```yaml
关系数据库: PostgreSQL 15+
时序数据库: InfluxDB 2.7+
缓存数据库: Redis 7.2+
向量数据库: Qdrant 1.7+
```

**基础设施**：
```yaml
容器化: Docker 24+ / Docker Compose
Web服务器: Nginx 1.24+
监控: Prometheus + Grafana
日志: ELK Stack (Elasticsearch + Logstash + Kibana)
CI/CD: GitHub Actions
云服务: 阿里云ECS / 腾讯云CVM
```

### 1.3 模块划分

**后端模块结构**：
```
backend/
├── app/
│   ├── api/                    # API路由层
│   │   └── v1/
│   │       ├── stock.py        # 股票相关API
│   │       ├── strategy.py     # 策略相关API
│   │       ├── analysis.py     # 分析相关API
│   │       └── user.py         # 用户相关API
│   │
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 配置管理
│   │   ├── security.py         # 安全认证
│   │   ├── database.py         # 数据库连接
│   │   └── cache.py            # 缓存管理
│   │
│   ├── models/                 # 数据模型 (ORM)
│   │   ├── user.py             # 用户模型
│   │   ├── stock.py            # 股票模型
│   │   └── strategy.py         # 策略模型
│   │
│   ├── schemas/                # Pydantic Schema
│   │   ├── stock.py            # 股票Schema
│   │   ├── strategy.py         # 策略Schema
│   │   └── analysis.py         # 分析Schema
│   │
│   ├── services/               # 业务逻辑层
│   │   ├── data_service.py     # 数据获取服务
│   │   ├── stock_service.py    # 选股服务
│   │   ├── analysis_service.py # 分析服务
│   │   ├── strategy_service.py # 策略服务
│   │   └── ai_service.py       # AI服务
│   │
│   ├── engines/                # 核心引擎
│   │   ├── stock_picker.py     # 选股引擎
│   │   ├── analyzer.py         # 分析引擎
│   │   ├── strategy_parser.py  # 策略解析引擎
│   │   └── indicator.py        # 指标计算引擎
│   │
│   ├── agents/                 # AI Agent
│   │   ├── orchestrator.py     # 主控Agent
│   │   ├── data_agent.py       # 数据获取Agent
│   │   ├── fundamental_agent.py# 基本面分析Agent
│   │   ├── technical_agent.py  # 技术面分析Agent
│   │   └── evaluator_agent.py  # 综合评估Agent
│   │
│   ├── utils/                  # 工具函数
│   │   ├── indicators.py       # 技术指标计算
│   │   ├── financial.py        # 财务指标计算
│   │   ├── validators.py       # 数据验证
│   │   └── formatters.py       # 数据格式化
│   │
│   └── tasks/                  # 异步任务
│       ├── data_sync.py        # 数据同步任务
│       ├── strategy_exec.py    # 策略执行任务
│       └── report_gen.py       # 报告生成任务
│
├── tests/                      # 测试
│   ├── unit/                   # 单元测试
│   └── integration/            # 集成测试
│
├── alembic/                    # 数据库迁移
├── requirements.txt            # 依赖
└── main.py                     # 入口文件
```

**前端模块结构**：
```
frontend/
├── src/
│   ├── components/             # 通用组件
│   │   ├── StockCard/          # 股票卡片
│   │   ├── Chart/              # 图表组件
│   │   ├── StrategyForm/       # 策略表单
│   │   └── Layout/             # 布局组件
│   │
│   ├── pages/                  # 页面组件
│   │   ├── StockPicker/        # 选股中心
│   │   ├── StockAnalysis/      # 个股分析
│   │   ├── MyStrategy/         # 我的策略
│   │   └── Market/             # 市场概览
│   │
│   ├── services/               # API服务
│   │   ├── api.ts              # API封装
│   │   ├── stock.ts            # 股票API
│   │   ├── strategy.ts         # 策略API
│   │   └── analysis.ts         # 分析API
│   │
│   ├── stores/                 # 状态管理
│   │   ├── userStore.ts        # 用户状态
│   │   ├── stockStore.ts       # 股票状态
│   │   └── strategyStore.ts    # 策略状态
│   │
│   ├── hooks/                  # 自定义Hooks
│   │   ├── useStock.ts         # 股票数据Hook
│   │   ├── useStrategy.ts      # 策略Hook
│   │   └── useWebSocket.ts     # WebSocket Hook
│   │
│   ├── utils/                  # 工具函数
│   │   ├── format.ts           # 格式化
│   │   ├── calculate.ts        # 计算函数
│   │   └── validators.ts       # 验证函数
│   │
│   └── types/                  # TypeScript类型
│       ├── stock.ts
│       ├── strategy.ts
│       └── analysis.ts
│
├── public/                     # 静态资源
└── package.json                # 依赖配置
```

### 1.4 数据流设计

**1.4.1 选股流程数据流**：
```
用户输入策略条件
    ↓
前端: 发送POST /api/v1/strategies/execute
    ↓
API层: 接收请求，验证参数
    ↓
选股服务: 调用选股引擎
    ↓
选股引擎:
    1. 从Redis获取股票列表缓存
    2. 如缓存未命中，从PostgreSQL查询
    3. 应用筛选条件
    4. 计算衍生指标
    5. 排序并分页
    ↓
返回结果: 股票列表 + 元数据
    ↓
前端: 展示结果，支持排序/筛选
```

**1.4.2 个股分析流程数据流**：
```
用户输入股票代码
    ↓
前端: 发送POST /api/v1/stocks/{code}/analyze
    ↓
API层: 接收请求，验证股票代码
    ↓
分析服务: 调用分析引擎
    ↓
分析引擎:
    1. 检查Redis缓存（TTL: 1小时）
    2. 如缓存未命中，启动分析流程
    3. 并行获取数据:
       - 实时行情 (Redis/AKShare)
       - K线数据 (InfluxDB)
       - 财务数据 (PostgreSQL)
       - 资金流向 (Redis/AKShare)
    4. 调用AI Agent编排器
    5. 并行执行分析Agent:
       - 基本面分析Agent
       - 技术面分析Agent
       - 资金面分析Agent
    6. 综合评估Agent汇总结果
    7. 生成分析报告
    8. 写入Redis缓存
    ↓
返回结果: 分析报告JSON
    ↓
前端: 渲染分析报告
```

**1.4.3 自然语言策略解析数据流**：
```
用户输入自然语言描述
    ↓
前端: 发送POST /api/v1/strategies/parse
    ↓
API层: 接收请求
    ↓
策略服务: 调用策略解析引擎
    ↓
策略解析引擎:
    1. 构建Prompt (包含示例和规则)
    2. 调用LLM API (GPT-4/DeepSeek)
    3. 解析LLM返回的JSON
    4. 验证条件合法性
    5. 检测逻辑冲突
    6. 生成结构化条件
    ↓
返回结果: 结构化条件JSON + 冲突提示
    ↓
前端: 展示结构化条件，用户确认
    ↓
用户确认后: 执行选股流程
```

**1.4.4 实时行情更新数据流**：
```
定时任务 (每3秒，交易时间)
    ↓
数据同步任务:
    1. 调用AKShare API获取全市场行情
    2. 数据清洗与验证
    3. 批量写入Redis (TTL: 5秒)
    4. 批量写入InfluxDB (当日K线)
    5. 通过WebSocket推送给在线用户
    ↓
前端: WebSocket接收实时数据
    ↓
前端: 更新UI (股票列表、K线图)
```

---

## 2. 数据库设计

### 2.1 PostgreSQL表设计

**2.1.1 用户相关表**

```sql
-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- 用户自选股表
CREATE TABLE user_watchlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, stock_code)
);

CREATE INDEX idx_watchlist_user ON user_watchlist(user_id);
CREATE INDEX idx_watchlist_stock ON user_watchlist(stock_code);
```

**2.1.2 策略相关表**

```sql
-- 策略表
CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(20) NOT NULL, -- 'classic' or 'custom'
    conditions JSONB NOT NULL,           -- 策略条件JSON
    risk_filters JSONB,                  -- 风险过滤条件
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_strategies_user ON strategies(user_id);
CREATE INDEX idx_strategies_type ON strategies(strategy_type);
CREATE INDEX idx_strategies_conditions ON strategies USING GIN(conditions);

-- 策略执行历史表
CREATE TABLE strategy_executions (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result_count INTEGER,
    result_snapshot JSONB,               -- 筛选结果快照
    execution_time_ms INTEGER,           -- 执行耗时(毫秒)
    status VARCHAR(20) DEFAULT 'success' -- 'success', 'failed', 'timeout'
);

CREATE INDEX idx_executions_strategy ON strategy_executions(strategy_id);
CREATE INDEX idx_executions_user ON strategy_executions(user_id);
CREATE INDEX idx_executions_time ON strategy_executions(executed_at DESC);

-- 策略效果追踪表
CREATE TABLE strategy_performance (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER REFERENCES strategy_executions(id) ON DELETE CASCADE,
    stock_code VARCHAR(10) NOT NULL,
    entry_price DECIMAL(10, 2),
    entry_date DATE,
    price_t5 DECIMAL(10, 2),             -- T+5价格
    price_t10 DECIMAL(10, 2),            -- T+10价格
    price_t20 DECIMAL(10, 2),            -- T+20价格
    return_t5 DECIMAL(8, 4),             -- T+5收益率
    return_t10 DECIMAL(8, 4),            -- T+10收益率
    return_t20 DECIMAL(8, 4),            -- T+20收益率
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_performance_execution ON strategy_performance(execution_id);
CREATE INDEX idx_performance_stock ON strategy_performance(stock_code);
```

**2.1.3 股票基础信息表**

```sql
-- 股票基础信息表
CREATE TABLE stocks (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) UNIQUE NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    market VARCHAR(10) NOT NULL,         -- 'SH', 'SZ', 'BJ'
    industry VARCHAR(50),                -- 申万一级行业
    industry_l2 VARCHAR(50),             -- 申万二级行业
    sector VARCHAR(50),                  -- 板块
    list_date DATE,                      -- 上市日期
    is_st BOOLEAN DEFAULT FALSE,         -- 是否ST股
    is_suspended BOOLEAN DEFAULT FALSE,  -- 是否停牌
    total_shares BIGINT,                 -- 总股本(股)
    float_shares BIGINT,                 -- 流通股本(股)
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stocks_code ON stocks(stock_code);
CREATE INDEX idx_stocks_industry ON stocks(industry);
CREATE INDEX idx_stocks_sector ON stocks(sector);
CREATE INDEX idx_stocks_st ON stocks(is_st) WHERE is_st = TRUE;

-- 股票财务数据表
CREATE TABLE stock_financials (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    report_date DATE NOT NULL,           -- 报告期
    report_type VARCHAR(10) NOT NULL,    -- 'Q1', 'Q2', 'Q3', 'annual'

    -- 资产负债表
    total_assets BIGINT,                 -- 总资产
    total_liabilities BIGINT,            -- 总负债
    net_assets BIGINT,                   -- 净资产
    debt_ratio DECIMAL(8, 4),            -- 资产负债率
    current_ratio DECIMAL(8, 4),         -- 流动比率

    -- 利润表
    revenue BIGINT,                      -- 营业收入
    net_profit BIGINT,                   -- 净利润
    net_profit_deducted BIGINT,          -- 扣非净利润
    gross_margin DECIMAL(8, 4),          -- 毛利率
    net_margin DECIMAL(8, 4),            -- 净利率

    -- 现金流量表
    operating_cash_flow BIGINT,          -- 经营现金流
    investing_cash_flow BIGINT,          -- 投资现金流
    financing_cash_flow BIGINT,          -- 筹资现金流
    free_cash_flow BIGINT,               -- 自由现金流

    -- 关键指标
    roe DECIMAL(8, 4),                   -- 净资产收益率
    roa DECIMAL(8, 4),                   -- 总资产收益率
    eps DECIMAL(10, 4),                  -- 每股收益
    bps DECIMAL(10, 4),                  -- 每股净资产

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, report_date, report_type)
);

CREATE INDEX idx_financials_stock ON stock_financials(stock_code);
CREATE INDEX idx_financials_date ON stock_financials(report_date DESC);
CREATE INDEX idx_financials_roe ON stock_financials(roe DESC);
```

**2.1.4 分析报告表**

```sql
-- 分析报告表
CREATE TABLE analysis_reports (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    report_type VARCHAR(20) DEFAULT 'comprehensive', -- 'comprehensive', 'fundamental', 'technical'

    -- 分析结果
    fundamental_score DECIMAL(4, 2),     -- 基本面评分(0-10)
    technical_score DECIMAL(4, 2),       -- 技术面评分(0-10)
    capital_score DECIMAL(4, 2),         -- 资金面评分(0-10)
    overall_score DECIMAL(4, 2),         -- 综合评分(0-10)
    risk_level VARCHAR(10),              -- 'low', 'medium', 'high'
    recommendation VARCHAR(20),          -- 'buy', 'hold', 'watch', 'sell'

    -- 完整报告JSON
    report_data JSONB NOT NULL,

    -- 元数据
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation_time_ms INTEGER,          -- 生成耗时
    model_version VARCHAR(50),           -- AI模型版本

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reports_stock ON analysis_reports(stock_code);
CREATE INDEX idx_reports_user ON analysis_reports(user_id);
CREATE INDEX idx_reports_time ON analysis_reports(generated_at DESC);
CREATE INDEX idx_reports_score ON analysis_reports(overall_score DESC);
```

### 2.2 InfluxDB数据结构

**2.2.1 K线数据**

```
measurement: stock_kline
tags:
  - stock_code: 股票代码
  - period: 周期 (1d, 1w, 1m, 1min, 5min, 15min, 30min, 60min)
  - adjust: 复权类型 (qfq前复权, hfq后复权, none不复权)
fields:
  - open: 开盘价 (float)
  - high: 最高价 (float)
  - low: 最低价 (float)
  - close: 收盘价 (float)
  - volume: 成交量 (int)
  - amount: 成交额 (float)
  - turnover: 换手率 (float)
  - amplitude: 振幅 (float)
time: 时间戳

示例查询:
SELECT open, high, low, close, volume
FROM stock_kline
WHERE stock_code='600519' AND period='1d' AND adjust='qfq'
AND time >= now() - 90d
ORDER BY time DESC
```

**2.2.2 实时行情数据**

```
measurement: stock_realtime
tags:
  - stock_code: 股票代码
  - market: 市场 (SH, SZ, BJ)
fields:
  - price: 最新价 (float)
  - change: 涨跌额 (float)
  - pct_change: 涨跌幅 (float)
  - volume: 成交量 (int)
  - amount: 成交额 (float)
  - turnover: 换手率 (float)
  - amplitude: 振幅 (float)
  - high: 最高价 (float)
  - low: 最低价 (float)
  - open: 开盘价 (float)
  - pre_close: 昨收价 (float)
  - volume_ratio: 量比 (float)
  - bid_ratio: 委比 (float)
  - pe_ttm: 市盈率TTM (float)
  - pb: 市净率 (float)
  - market_cap: 总市值 (float)
  - float_market_cap: 流通市值 (float)
time: 时间戳

保留策略: 1天 (自动过期)
```

**2.2.3 技术指标数据**

```
measurement: stock_indicators
tags:
  - stock_code: 股票代码
  - indicator: 指标名称 (ma, macd, rsi, kdj, boll)
fields:
  # 均线
  - ma5: 5日均线 (float)
  - ma10: 10日均线 (float)
  - ma20: 20日均线 (float)
  - ma60: 60日均线 (float)

  # MACD
  - macd_dif: DIF (float)
  - macd_dea: DEA (float)
  - macd_bar: 柱状图 (float)

  # RSI
  - rsi_6: 6日RSI (float)
  - rsi_12: 12日RSI (float)
  - rsi_24: 24日RSI (float)

  # KDJ
  - kdj_k: K值 (float)
  - kdj_d: D值 (float)
  - kdj_j: J值 (float)

  # 布林带
  - boll_upper: 上轨 (float)
  - boll_mid: 中轨 (float)
  - boll_lower: 下轨 (float)
time: 时间戳
```

**2.2.4 资金流向数据**

```
measurement: capital_flow
tags:
  - stock_code: 股票代码
fields:
  - main_inflow: 主力资金流入 (float)
  - main_outflow: 主力资金流出 (float)
  - main_net: 主力资金净流入 (float)
  - super_large_inflow: 超大单流入 (float)
  - super_large_outflow: 超大单流出 (float)
  - super_large_net: 超大单净流入 (float)
  - large_inflow: 大单流入 (float)
  - large_outflow: 大单流出 (float)
  - large_net: 大单净流入 (float)
  - medium_inflow: 中单流入 (float)
  - medium_outflow: 中单流出 (float)
  - medium_net: 中单净流入 (float)
  - small_inflow: 小单流入 (float)
  - small_outflow: 小单流出 (float)
  - small_net: 小单净流入 (float)
time: 时间戳

保留策略: 90天
```

### 2.3 Redis缓存设计

**2.3.1 缓存Key设计规范**

```
命名规范: {业务模块}:{数据类型}:{唯一标识}:{可选参数}

示例:
stock:realtime:600519                    # 实时行情
stock:kline:600519:1d:qfq               # K线数据
stock:info:600519                        # 股票基础信息
stock:financial:600519:latest           # 最新财务数据
analysis:report:600519                   # 分析报告
strategy:result:123                      # 策略结果
user:session:abc123                      # 用户会话
market:index:sh                          # 市场指数
```

**2.3.2 缓存数据结构**

```python
# 1. 实时行情 (String, TTL: 5秒)
key: stock:realtime:{stock_code}
value: JSON
{
    "code": "600519",
    "name": "贵州茅台",
    "price": 1875.00,
    "change": 45.00,
    "pct_change": 2.46,
    "volume": 8520000,
    "amount": 15980000000,
    "turnover": 0.68,
    "pe_ttm": 35.2,
    "pb": 12.5,
    "market_cap": 2350000000000,
    "timestamp": 1707753600
}

# 2. K线数据 (String, TTL: 1小时)
key: stock:kline:{stock_code}:{period}:{adjust}
value: JSON (数组)
[
    {
        "date": "2026-02-12",
        "open": 1850.00,
        "high": 1890.00,
        "low": 1845.00,
        "close": 1875.00,
        "volume": 8520000,
        "amount": 15980000000
    },
    ...
]

# 3. 股票列表 (Sorted Set, TTL: 1小时)
key: stock:list:all
score: 股票代码数值
member: 股票代码
ZADD stock:list:all 600519 "600519"

# 4. 分析报告 (String, TTL: 1小时)
key: analysis:report:{stock_code}
value: JSON (完整报告)

# 5. 策略结果 (String, TTL: 30分钟)
key: strategy:result:{strategy_id}:{timestamp}
value: JSON
{
    "strategy_id": 123,
    "executed_at": 1707753600,
    "result_count": 35,
    "stocks": [
        {"code": "600519", "name": "贵州茅台", "score": 8.5},
        ...
    ]
}

# 6. 用户会话 (Hash, TTL: 7天)
key: user:session:{session_id}
fields:
  user_id: 123
  username: "user@example.com"
  login_at: 1707753600
  expires_at: 1708358400

# 7. 市场概览 (Hash, TTL: 5秒)
key: market:overview
fields:
  sh_index: 3250.50
  sh_change: 1.25
  sz_index: 10850.30
  sz_change: 0.85
  cyb_index: 2150.80
  cyb_change: 1.50
  up_count: 2850
  down_count: 1520
  limit_up_count: 85
  limit_down_count: 12
```

**2.3.3 缓存更新策略**

```python
# Cache-Aside模式 (读取时)
def get_stock_realtime(stock_code: str):
    # 1. 尝试从缓存读取
    cache_key = f"stock:realtime:{stock_code}"
    cached = redis.get(cache_key)

    if cached:
        return json.loads(cached)

    # 2. 缓存未命中，从数据源获取
    data = fetch_from_akshare(stock_code)

    # 3. 写入缓存
    redis.setex(cache_key, 5, json.dumps(data))

    return data

# Write-Through模式 (更新时)
def update_stock_realtime(stock_code: str, data: dict):
    # 1. 更新数据库
    influxdb.write(data)

    # 2. 同步更新缓存
    cache_key = f"stock:realtime:{stock_code}"
    redis.setex(cache_key, 5, json.dumps(data))

# 批量预热
def warmup_cache():
    # 预热热门股票数据
    hot_stocks = ["600519", "000858", "601318", ...]
    for code in hot_stocks:
        data = fetch_from_akshare(code)
        cache_key = f"stock:realtime:{code}"
        redis.setex(cache_key, 5, json.dumps(data))
```

### 2.4 Qdrant向量库设计

**2.4.1 Collection设计**

```python
# 公告向量Collection
collection_name: "stock_announcements"
vector_size: 1536  # OpenAI text-embedding-3-small
distance: Cosine

payload_schema:
{
    "stock_code": str,        # 股票代码
    "stock_name": str,        # 股票名称
    "title": str,             # 公告标题
    "content": str,           # 公告内容
    "ann_date": str,          # 公告日期
    "ann_type": str,          # 公告类型
    "url": str,               # 公告链接
    "importance": int         # 重要性(1-5)
}

# 新闻向量Collection
collection_name: "stock_news"
vector_size: 1536
distance: Cosine

payload_schema:
{
    "stock_code": str,        # 相关股票代码
    "title": str,             # 新闻标题
    "content": str,           # 新闻内容
    "source": str,            # 新闻来源
    "publish_date": str,      # 发布日期
    "sentiment": str,         # 情感倾向(positive/neutral/negative)
    "url": str                # 新闻链接
}
```

**2.4.2 向量检索示例**

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

client = QdrantClient(host="localhost", port=6333)

# 语义搜索公告
def search_announcements(query: str, stock_code: str = None, limit: int = 10):
    # 1. 生成查询向量
    query_vector = openai.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding

    # 2. 构建过滤条件
    filter_conditions = []
    if stock_code:
        filter_conditions.append(
            FieldCondition(
                key="stock_code",
                match=MatchValue(value=stock_code)
            )
        )

    # 3. 向量检索
    results = client.search(
        collection_name="stock_announcements",
        query_vector=query_vector,
        query_filter=Filter(must=filter_conditions) if filter_conditions else None,
        limit=limit
    )

    return results
```

---

## 3. API设计

### 3.1 RESTful API规范

**3.1.1 基础规范**

```yaml
协议: HTTPS
基础URL: https://api.stock-ai.com/api/v1
认证方式: JWT Bearer Token
请求格式: application/json
响应格式: application/json
字符编码: UTF-8
```

**3.1.2 统一响应格式**

```typescript
// 成功响应
{
  "code": 200,
  "message": "success",
  "data": {
    // 实际数据
  },
  "timestamp": 1707753600
}

// 错误响应
{
  "code": 400,
  "message": "Invalid parameters",
  "error": {
    "type": "ValidationError",
    "details": [
      {
        "field": "stock_code",
        "message": "Stock code is required"
      }
    ]
  },
  "timestamp": 1707753600
}

// 分页响应
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5
    }
  },
  "timestamp": 1707753600
}
```

**3.1.3 HTTP状态码规范**

```
200 OK: 请求成功
201 Created: 资源创建成功
204 No Content: 请求成功但无返回内容
400 Bad Request: 请求参数错误
401 Unauthorized: 未认证
403 Forbidden: 无权限
404 Not Found: 资源不存在
422 Unprocessable Entity: 请求格式正确但语义错误
429 Too Many Requests: 请求过于频繁
500 Internal Server Error: 服务器内部错误
503 Service Unavailable: 服务暂时不可用
```

### 3.2 核心API接口

**3.2.1 用户认证API**

```python
# 用户注册
POST /api/v1/auth/register
Request:
{
  "username": "user123",
  "email": "user@example.com",
  "password": "SecurePass123!"
}
Response:
{
  "code": 201,
  "message": "User registered successfully",
  "data": {
    "user_id": 123,
    "username": "user123",
    "email": "user@example.com"
  }
}

# 用户登录
POST /api/v1/auth/login
Request:
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
Response:
{
  "code": 200,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "id": 123,
      "username": "user123",
      "email": "user@example.com"
    }
  }
}

# 刷新Token
POST /api/v1/auth/refresh
Headers:
  Authorization: Bearer {refresh_token}
Response:
{
  "code": 200,
  "message": "Token refreshed",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 7200
  }
}

# 登出
POST /api/v1/auth/logout
Headers:
  Authorization: Bearer {access_token}
Response:
{
  "code": 200,
  "message": "Logout successful"
}
```

**3.2.2 股票数据API**

```python
# 获取股票列表
GET /api/v1/stocks?page=1&page_size=20&market=SH&industry=白酒
Headers:
  Authorization: Bearer {access_token}
Query Parameters:
  - page: 页码 (默认1)
  - page_size: 每页数量 (默认20, 最大100)
  - market: 市场 (SH/SZ/BJ)
  - industry: 行业
  - sector: 板块
  - keyword: 搜索关键词
Response:
{
  "code": 200,
  "data": {
    "items": [
      {
        "code": "600519",
        "name": "贵州茅台",
        "market": "SH",
        "industry": "白酒",
        "price": 1875.00,
        "change": 45.00,
        "pct_change": 2.46,
        "market_cap": 2350000000000
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 5000,
      "total_pages": 250
    }
  }
}

# 获取股票详情
GET /api/v1/stocks/{stock_code}
Headers:
  Authorization: Bearer {access_token}
Response:
{
  "code": 200,
  "data": {
    "code": "600519",
    "name": "贵州茅台",
    "market": "SH",
    "industry": "白酒",
    "sector": "消费",
    "list_date": "2001-08-27",
    "is_st": false,
    "is_suspended": false,
    "total_shares": 1256197800,
    "float_shares": 1256197800,
    "realtime": {
      "price": 1875.00,
      "change": 45.00,
      "pct_change": 2.46,
      "volume": 8520000,
      "amount": 15980000000,
      "pe_ttm": 35.2,
      "pb": 12.5
    }
  }
}

# 获取实时行情
GET /api/v1/stocks/{stock_code}/realtime
Headers:
  Authorization: Bearer {access_token}
Response:
{
  "code": 200,
  "data": {
    "code": "600519",
    "name": "贵州茅台",
    "price": 1875.00,
    "change": 45.00,
    "pct_change": 2.46,
    "volume": 8520000,
    "amount": 15980000000,
    "turnover": 0.68,
    "amplitude": 2.5,
    "high": 1890.00,
    "low": 1845.00,
    "open": 1850.00,
    "pre_close": 1830.00,
    "timestamp": 1707753600
  }
}

# 获取K线数据
GET /api/v1/stocks/{stock_code}/kline?period=1d&adjust=qfq&limit=90
Headers:
  Authorization: Bearer {access_token}
Query Parameters:
  - period: 周期 (1d/1w/1m/1min/5min/15min/30min/60min)
  - adjust: 复权类型 (qfq前复权/hfq后复权/none不复权)
  - start_date: 开始日期 (YYYY-MM-DD)
  - end_date: 结束日期 (YYYY-MM-DD)
  - limit: 返回数量 (默认90)
Response:
{
  "code": 200,
  "data": {
    "stock_code": "600519",
    "period": "1d",
    "adjust": "qfq",
    "klines": [
      {
        "date": "2026-02-12",
        "open": 1850.00,
        "high": 1890.00,
        "low": 1845.00,
        "close": 1875.00,
        "volume": 8520000,
        "amount": 15980000000,
        "turnover": 0.68,
        "amplitude": 2.5
      }
    ]
  }
}

# 获取财务数据
GET /api/v1/stocks/{stock_code}/financials?limit=8
Headers:
  Authorization: Bearer {access_token}
Query Parameters:
  - limit: 返回季度数 (默认8)
Response:
{
  "code": 200,
  "data": {
    "stock_code": "600519",
    "financials": [
      {
        "report_date": "2025-09-30",
        "report_type": "Q3",
        "revenue": 125000000000,
        "net_profit": 65000000000,
        "roe": 0.223,
        "gross_margin": 0.912,
        "net_margin": 0.521,
        "debt_ratio": 0.285
      }
    ]
  }
}
```

**3.2.3 选股策略API**

```python
# 获取经典策略列表
GET /api/v1/strategies/classic
Headers:
  Authorization: Bearer {access_token}
Response:
{
  "code": 200,
  "data": {
    "strategies": [
      {
        "id": "graham_value",
        "name": "格雷厄姆价值投资",
        "description": "低PE、低PB、高股息率的价值股",
        "category": "value",
        "default_params": {
          "pe_max": 15,
          "pb_max": 2,
          "dividend_yield_min": 0.02
        }
      }
    ]
  }
}

# 执行经典策略
POST /api/v1/strategies/classic/{strategy_id}/execute
Headers:
  Authorization: Bearer {access_token}
Request:
{
  "params": {
    "pe_max": 15,
    "pb_max": 2,
    "dividend_yield_min": 0.02
  },
  "risk_filters": {
    "exclude_st": true,
    "min_market_cap": 5000000000
  }
}
Response:
{
  "code": 200,
  "data": {
    "strategy_id": "graham_value",
    "execution_id": 12345,
    "executed_at": 1707753600,
    "result_count": 35,
    "execution_time_ms": 2500,
    "stocks": [
      {
        "code": "600519",
        "name": "贵州茅台",
        "price": 1875.00,
        "pe": 35.2,
        "pb": 12.5,
        "dividend_yield": 0.032,
        "score": 8.5
      }
    ]
  }
}

# 解析自然语言策略
POST /api/v1/strategies/parse
Headers:
  Authorization: Bearer {access_token}
Request:
{
  "description": "找出PE低于15，ROE连续3年大于15%，且近5日主力资金净流入的股票"
}
Response:
{
  "code": 200,
  "data": {
    "parsed_conditions": [
      {
        "type": "valuation",
        "field": "pe_ttm",
        "operator": "<",
        "value": 15,
        "description": "市盈率低于15倍"
      },
      {
        "type": "profitability",
        "field": "roe",
        "operator": ">",
        "value": 0.15,
        "duration": "3_years",
        "description": "ROE连续3年大于15%"
      },
      {
        "type": "capital_flow",
        "field": "main_capital_inflow",
        "operator": ">",
        "value": 0,
        "period": "5_days",
        "description": "近5日主力资金净流入"
      }
    ],
    "conflicts": [],
    "suggestions": []
  }
}

# 执行自定义策略
POST /api/v1/strategies/custom/execute
Headers:
  Authorization: Bearer {access_token}
Request:
{
  "conditions": [
    {
      "type": "valuation",
      "field": "pe_ttm",
      "operator": "<",
      "value": 15
    }
  ],
  "risk_filters": {
    "exclude_st": true
  }
}
Response:
{
  "code": 200,
  "data": {
    "execution_id": 12346,
    "executed_at": 1707753600,
    "result_count": 42,
    "stocks": [...]
  }
}

# 保存策略
POST /api/v1/strategies
Headers:
  Authorization: Bearer {access_token}
Request:
{
  "name": "我的价值策略",
  "description": "低估值高ROE策略",
  "strategy_type": "custom",
  "conditions": [...]
}
Response:
{
  "code": 201,
  "data": {
    "strategy_id": 123,
    "name": "我的价值策略",
    "created_at": 1707753600
  }
}

# 获取用户策略列表
GET /api/v1/strategies?page=1&page_size=20
Headers:
  Authorization: Bearer {access_token}
Response:
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 123,
        "name": "我的价值策略",
        "strategy_type": "custom",
        "created_at": 1707753600,
        "execution_count": 15,
        "last_executed_at": 1707753600
      }
    ],
    "pagination": {...}
  }
}

# 删除策略
DELETE /api/v1/strategies/{strategy_id}
Headers:
  Authorization: Bearer {access_token}
Response:
{
  "code": 200,
  "message": "Strategy deleted successfully"
}
```

**3.2.4 个股分析API**

```python
# 生成分析报告
POST /api/v1/stocks/{stock_code}/analyze
Headers:
  Authorization: Bearer {access_token}
Request:
{
  "report_type": "comprehensive",  # comprehensive/fundamental/technical
  "force_refresh": false            # 是否强制刷新缓存
}
Response:
{
  "code": 200,
  "data": {
    "stock_code": "600519",
    "stock_name": "贵州茅台",
    "report_type": "comprehensive",
    "generated_at": 1707753600,
    "generation_time_ms": 8500,

    "scores": {
      "fundamental": 8.5,
      "technical": 9.0,
      "capital": 8.5,
      "overall": 8.7
    },

    "risk_level": "medium",
    "recommendation": "buy",

    "fundamental_analysis": {
      "financial_health_score": 85,
      "profitability_trend": "improving",
      "growth_assessment": "steady",
      "valuation_judgment": "fair",
      "details": {...}
    },

    "technical_analysis": {
      "trend": "strong_uptrend",
      "support_levels": [1850, 1820, 1780],
      "resistance_levels": [1900, 1950, 2000],
      "indicators": {
        "macd": "buy",
        "rsi": "neutral",
        "kdj": "buy"
      },
      "signal_strength": 0.90
    },

    "capital_analysis": {
      "main_capital_flow": {
        "today": 850000000,
        "5d": 2230000000,
        "10d": 3570000000
      },
      "northbound_capital": {
        "holding_shares": 235000000,
        "holding_ratio": 0.0482,
        "recent_change": 42000000
      }
    },

    "ai_evaluation": {
      "investment_logic": [
        "基本面扎实：ROE连续5年>20%，盈利能力强",
        "技术面强势：多头排列，技术指标买入信号",
        "资金面支持：主力+北向持续流入"
      ],
      "risk_warnings": [
        "估值不便宜：PE处于历史62%分位",
        "成长性放缓：增速低于行业平均"
      ],
      "operation_strategy": {
        "position": "20%-30%",
        "entry_price": "1850-1875",
        "stop_loss": 1780,
        "target_price": "1950-2000",
        "holding_period": "3-6个月"
      }
    }
  }
}

# 获取历史分析报告
GET /api/v1/stocks/{stock_code}/reports?limit=10
Headers:
  Authorization: Bearer {access_token}
Response:
{
  "code": 200,
  "data": {
    "reports": [
      {
        "id": 12345,
        "generated_at": 1707753600,
        "overall_score": 8.7,
        "recommendation": "buy"
      }
    ]
  }
}
```

**3.2.5 市场概览API**

```python
# 获取市场概览
GET /api/v1/market/overview
Headers:
  Authorization: Bearer {access_token}
Response:
{
  "code": 200,
  "data": {
    "indices": [
      {
        "code": "000001",
        "name": "上证指数",
        "value": 3250.50,
        "change": 40.25,
        "pct_change": 1.25
      },
      {
        "code": "399001",
        "name": "深证成指",
        "value": 10850.30,
        "change": 91.50,
        "pct_change": 0.85
      }
    ],
    "market_stats": {
      "up_count": 2850,
      "down_count": 1520,
      "limit_up_count": 85,
      "limit_down_count": 12,
      "total_amount": 850000000000
    },
    "timestamp": 1707753600
  }
}

# 获取板块行情
GET /api/v1/market/sectors?type=industry
Headers:
  Authorization: Bearer {access_token}
Query Parameters:
  - type: 板块类型 (industry行业/concept概念)
Response:
{
  "code": 200,
  "data": {
    "sectors": [
      {
        "code": "BK0896",
        "name": "白酒",
        "pct_change": 2.5,
        "up_count": 15,
        "down_count": 3,
        "leader": {
          "code": "600519",
          "name": "贵州茅台",
          "pct_change": 2.46
        }
      }
    ]
  }
}
```

### 3.3 WebSocket接口

**3.3.1 连接建立**

```javascript
// 连接URL
ws://api.stock-ai.com/ws?token={access_token}

// 连接成功
{
  "type": "connected",
  "message": "WebSocket connected",
  "timestamp": 1707753600
}
```

**3.3.2 订阅实时行情**

```javascript
// 订阅请求
{
  "action": "subscribe",
  "channel": "realtime",
  "stocks": ["600519", "000858", "601318"]
}

// 订阅确认
{
  "type": "subscribed",
  "channel": "realtime",
  "stocks": ["600519", "000858", "601318"]
}

// 实时数据推送
{
  "type": "realtime",
  "data": {
    "code": "600519",
    "price": 1875.00,
    "change": 45.00,
    "pct_change": 2.46,
    "volume": 8520000,
    "timestamp": 1707753600
  }
}

// 取消订阅
{
  "action": "unsubscribe",
  "channel": "realtime",
  "stocks": ["600519"]
}
```

**3.3.3 心跳机制**

```javascript
// 客户端发送心跳 (每30秒)
{
  "action": "ping"
}

// 服务端响应
{
  "type": "pong",
  "timestamp": 1707753600
}
```

### 3.4 错误处理

**3.4.1 错误码定义**

```python
# 业务错误码
class ErrorCode:
    # 通用错误 (1000-1999)
    INVALID_PARAMS = 1001          # 参数错误
    RESOURCE_NOT_FOUND = 1002      # 资源不存在
    DUPLICATE_RESOURCE = 1003      # 资源已存在

    # 认证错误 (2000-2999)
    UNAUTHORIZED = 2001            # 未认证
    TOKEN_EXPIRED = 2002           # Token过期
    TOKEN_INVALID = 2003           # Token无效
    PERMISSION_DENIED = 2004       # 无权限

    # 业务错误 (3000-3999)
    STOCK_NOT_FOUND = 3001         # 股票不存在
    STRATEGY_EXECUTION_FAILED = 3002  # 策略执行失败
    ANALYSIS_GENERATION_FAILED = 3003 # 分析报告生成失败
    DATA_SOURCE_UNAVAILABLE = 3004    # 数据源不可用

    # 限流错误 (4000-4999)
    RATE_LIMIT_EXCEEDED = 4001     # 请求过于频繁

    # 系统错误 (5000-5999)
    INTERNAL_ERROR = 5001          # 内部错误
    SERVICE_UNAVAILABLE = 5002     # 服务不可用
    DATABASE_ERROR = 5003          # 数据库错误
```

**3.4.2 错误响应示例**

```json
{
  "code": 3001,
  "message": "Stock not found",
  "error": {
    "type": "StockNotFoundError",
    "details": {
      "stock_code": "999999",
      "message": "Stock code 999999 does not exist"
    }
  },
  "timestamp": 1707753600
}
```

**3.4.3 FastAPI错误处理实现**

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()

# 自定义异常类
class BusinessException(Exception):
    def __init__(self, code: int, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details

# 业务异常处理器
@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=400,
        content={
            "code": exc.code,
            "message": exc.message,
            "error": {
                "type": exc.__class__.__name__,
                "details": exc.details
            },
            "timestamp": int(time.time())
        }
    )

# 参数验证异常处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "code": 1001,
            "message": "Invalid parameters",
            "error": {
                "type": "ValidationError",
                "details": exc.errors()
            },
            "timestamp": int(time.time())
        }
    )

# 通用异常处理器
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "code": 5001,
            "message": "Internal server error",
            "error": {
                "type": exc.__class__.__name__,
                "details": str(exc) if app.debug else None
            },
            "timestamp": int(time.time())
        }
    )
```

---

## 4. 核心模块设计

### 4.1 选股引擎

**4.1.1 选股引擎架构**

```python
# engines/stock_picker.py

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.schemas.strategy import StrategyCondition, StockPickResult

class StockPickerEngine:
    """选股引擎：执行选股策略，筛选符合条件的股票"""

    def __init__(self, db: Session, cache: Redis):
        self.db = db
        self.cache = cache
        self.indicator_engine = IndicatorEngine()

    async def execute_strategy(
        self,
        conditions: List[StrategyCondition],
        risk_filters: Dict[str, Any] = None
    ) -> StockPickResult:
        """
        执行选股策略

        Args:
            conditions: 筛选条件列表
            risk_filters: 风险过滤条件

        Returns:
            StockPickResult: 筛选结果
        """
        # 1. 获取股票池
        stock_pool = await self._get_stock_pool(risk_filters)

        # 2. 应用筛选条件
        filtered_stocks = await self._apply_conditions(stock_pool, conditions)

        # 3. 计算评分
        scored_stocks = await self._calculate_scores(filtered_stocks, conditions)

        # 4. 排序
        sorted_stocks = self._sort_stocks(scored_stocks)

        return StockPickResult(
            stocks=sorted_stocks,
            total_count=len(sorted_stocks),
            execution_time_ms=...
        )

    async def _get_stock_pool(self, risk_filters: Dict) -> List[str]:
        """获取股票池（应用风险过滤）"""
        # 1. 尝试从缓存获取
        cache_key = f"stock:pool:{hash(str(risk_filters))}"
        cached = await self.cache.get(cache_key)
        if cached:
            return json.loads(cached)

        # 2. 从数据库查询
        query = self.db.query(Stock.stock_code)

        # 应用风险过滤
        if risk_filters.get('exclude_st'):
            query = query.filter(Stock.is_st == False)

        if risk_filters.get('exclude_suspended'):
            query = query.filter(Stock.is_suspended == False)

        if risk_filters.get('min_market_cap'):
            query = query.filter(
                Stock.float_shares * Stock.latest_price >= risk_filters['min_market_cap']
            )

        stock_codes = [row.stock_code for row in query.all()]

        # 3. 写入缓存
        await self.cache.setex(cache_key, 3600, json.dumps(stock_codes))

        return stock_codes

    async def _apply_conditions(
        self,
        stock_pool: List[str],
        conditions: List[StrategyCondition]
    ) -> List[str]:
        """应用筛选条件"""
        filtered = stock_pool

        for condition in conditions:
            if condition.type == 'valuation':
                filtered = await self._filter_by_valuation(filtered, condition)
            elif condition.type == 'profitability':
                filtered = await self._filter_by_profitability(filtered, condition)
            elif condition.type == 'growth':
                filtered = await self._filter_by_growth(filtered, condition)
            elif condition.type == 'technical':
                filtered = await self._filter_by_technical(filtered, condition)
            elif condition.type == 'capital_flow':
                filtered = await self._filter_by_capital_flow(filtered, condition)

        return filtered

    async def _filter_by_valuation(
        self,
        stocks: List[str],
        condition: StrategyCondition
    ) -> List[str]:
        """按估值指标筛选"""
        field = condition.field  # pe_ttm, pb, ps
        operator = condition.operator  # <, >, <=, >=, ==
        value = condition.value

        # 从Redis获取实时数据
        filtered = []
        for code in stocks:
            data = await self._get_stock_realtime(code)
            if data and self._compare(data.get(field), operator, value):
                filtered.append(code)

        return filtered

    async def _filter_by_profitability(
        self,
        stocks: List[str],
        condition: StrategyCondition
    ) -> List[str]:
        """按盈利能力筛选"""
        field = condition.field  # roe, roa, net_margin
        operator = condition.operator
        value = condition.value
        duration = condition.duration  # 持续年限

        # 从PostgreSQL获取财务数据
        filtered = []
        for code in stocks:
            financials = await self._get_stock_financials(code, duration)
            if self._check_continuous(financials, field, operator, value, duration):
                filtered.append(code)

        return filtered

    def _compare(self, actual: float, operator: str, expected: float) -> bool:
        """比较运算"""
        if actual is None:
            return False

        if operator == '<':
            return actual < expected
        elif operator == '>':
            return actual > expected
        elif operator == '<=':
            return actual <= expected
        elif operator == '>=':
            return actual >= expected
        elif operator == '==':
            return actual == expected

        return False
```

**4.1.2 经典策略实现**

```python
# engines/classic_strategies.py

class GrahamValueStrategy:
    """格雷厄姆价值投资策略"""

    def __init__(self):
        self.default_params = {
            'pe_max': 15,
            'pb_max': 2,
            'dividend_yield_min': 0.02,
            'debt_ratio_max': 0.6,
            'current_ratio_min': 1.5,
            'min_market_cap': 5000000000
        }

    def get_conditions(self, params: Dict = None) -> List[StrategyCondition]:
        """生成筛选条件"""
        p = {**self.default_params, **(params or {})}

        return [
            StrategyCondition(
                type='valuation',
                field='pe_ttm',
                operator='<',
                value=p['pe_max']
            ),
            StrategyCondition(
                type='valuation',
                field='pb',
                operator='<',
                value=p['pb_max']
            ),
            StrategyCondition(
                type='profitability',
                field='dividend_yield',
                operator='>',
                value=p['dividend_yield_min']
            ),
            StrategyCondition(
                type='financial_health',
                field='debt_ratio',
                operator='<',
                value=p['debt_ratio_max']
            ),
            StrategyCondition(
                type='financial_health',
                field='current_ratio',
                operator='>',
                value=p['current_ratio_min']
            )
        ]

class BuffettMoatStrategy:
    """巴菲特护城河策略"""

    def __init__(self):
        self.default_params = {
            'roe_min': 0.15,
            'roe_years': 5,
            'roe_std_max': 0.05,
            'gross_margin_min': 0.30,
            'fcf_positive_years': 3,
            'debt_ratio_max': 0.50,
            'min_market_cap': 10000000000
        }

    def get_conditions(self, params: Dict = None) -> List[StrategyCondition]:
        """生成筛选条件"""
        p = {**self.default_params, **(params or {})}

        return [
            StrategyCondition(
                type='profitability',
                field='roe',
                operator='>',
                value=p['roe_min'],
                duration=f"{p['roe_years']}_years"
            ),
            StrategyCondition(
                type='profitability',
                field='roe_std',
                operator='<',
                value=p['roe_std_max']
            ),
            StrategyCondition(
                type='profitability',
                field='gross_margin',
                operator='>',
                value=p['gross_margin_min']
            ),
            StrategyCondition(
                type='cash_flow',
                field='free_cash_flow',
                operator='>',
                value=0,
                duration=f"{p['fcf_positive_years']}_years"
            )
        ]
```

### 4.2 分析引擎

**4.2.1 分析引擎架构**

```python
# engines/analyzer.py

class StockAnalyzer:
    """股票分析引擎：生成多维度分析报告"""

    def __init__(self, db: Session, cache: Redis, ai_service: AIService):
        self.db = db
        self.cache = cache
        self.ai_service = ai_service
        self.indicator_engine = IndicatorEngine()

    async def analyze(
        self,
        stock_code: str,
        report_type: str = 'comprehensive',
        force_refresh: bool = False
    ) -> AnalysisReport:
        """
        生成分析报告

        Args:
            stock_code: 股票代码
            report_type: 报告类型 (comprehensive/fundamental/technical)
            force_refresh: 是否强制刷新缓存

        Returns:
            AnalysisReport: 分析报告
        """
        # 1. 检查缓存
        if not force_refresh:
            cached = await self._get_cached_report(stock_code)
            if cached:
                return cached

        # 2. 并行获取数据
        data = await self._fetch_data_parallel(stock_code)

        # 3. 调用AI Agent编排器
        report = await self.ai_service.generate_analysis_report(
            stock_code=stock_code,
            data=data,
            report_type=report_type
        )

        # 4. 写入缓存
        await self._cache_report(stock_code, report)

        # 5. 保存到数据库
        await self._save_report(report)

        return report

    async def _fetch_data_parallel(self, stock_code: str) -> Dict:
        """并行获取所有需要的数据"""
        tasks = [
            self._get_stock_info(stock_code),
            self._get_realtime_quote(stock_code),
            self._get_kline_data(stock_code),
            self._get_financial_data(stock_code),
            self._get_capital_flow(stock_code),
            self._get_technical_indicators(stock_code)
        ]

        results = await asyncio.gather(*tasks)

        return {
            'stock_info': results[0],
            'realtime': results[1],
            'kline': results[2],
            'financials': results[3],
            'capital_flow': results[4],
            'indicators': results[5]
        }
```

**4.2.2 基本面分析模块**

```python
# engines/fundamental_analyzer.py

class FundamentalAnalyzer:
    """基本面分析器"""

    def analyze_financial_health(self, financials: List[Dict]) -> Dict:
        """分析财务健康度"""
        latest = financials[0]

        # 盈利能力评分 (30分)
        profitability_score = self._score_profitability(financials)

        # 偿债能力评分 (20分)
        solvency_score = self._score_solvency(latest)

        # 成长能力评分 (25分)
        growth_score = self._score_growth(financials)

        # 运营能力评分 (15分)
        operation_score = self._score_operation(latest)

        # 现金流评分 (10分)
        cashflow_score = self._score_cashflow(latest)

        total_score = (
            profitability_score +
            solvency_score +
            growth_score +
            operation_score +
            cashflow_score
        )

        return {
            'total_score': total_score,
            'profitability_score': profitability_score,
            'solvency_score': solvency_score,
            'growth_score': growth_score,
            'operation_score': operation_score,
            'cashflow_score': cashflow_score,
            'details': {
                'roe': latest['roe'],
                'debt_ratio': latest['debt_ratio'],
                'revenue_growth': self._calculate_cagr(financials, 'revenue', 3),
                'net_profit_growth': self._calculate_cagr(financials, 'net_profit', 3)
            }
        }

    def _score_profitability(self, financials: List[Dict]) -> float:
        """盈利能力评分 (0-30分)"""
        latest = financials[0]
        roe = latest['roe']
        net_margin = latest['net_margin']
        gross_margin = latest['gross_margin']

        # ROE评分 (15分)
        roe_score = min(roe / 0.20 * 15, 15)  # ROE>=20%得满分

        # 净利率评分 (8分)
        margin_score = min(net_margin / 0.15 * 8, 8)  # 净利率>=15%得满分

        # 毛利率评分 (7分)
        gross_score = min(gross_margin / 0.40 * 7, 7)  # 毛利率>=40%得满分

        return roe_score + margin_score + gross_score

    def _calculate_cagr(self, financials: List[Dict], field: str, years: int) -> float:
        """计算复合增长率"""
        if len(financials) < years * 4:  # 季度数据
            return None

        start_value = financials[-years*4][field]
        end_value = financials[0][field]

        if start_value <= 0:
            return None

        cagr = (end_value / start_value) ** (1 / years) - 1
        return cagr
```

**4.2.3 技术面分析模块**

```python
# engines/technical_analyzer.py

class TechnicalAnalyzer:
    """技术面分析器"""

    def analyze_trend(self, kline: List[Dict], indicators: Dict) -> Dict:
        """分析趋势"""
        latest = kline[0]
        ma5 = indicators['ma5'][-1]
        ma10 = indicators['ma10'][-1]
        ma20 = indicators['ma20'][-1]
        ma60 = indicators['ma60'][-1]

        # 判断多头/空头排列
        is_bullish = ma5 > ma10 > ma20 > ma60
        is_bearish = ma5 < ma10 < ma20 < ma60

        # 计算ADX (趋势强度)
        adx = self._calculate_adx(kline)

        if is_bullish and adx > 25:
            trend = 'strong_uptrend'
        elif is_bullish:
            trend = 'weak_uptrend'
        elif is_bearish and adx > 25:
            trend = 'strong_downtrend'
        elif is_bearish:
            trend = 'weak_downtrend'
        else:
            trend = 'sideways'

        return {
            'trend': trend,
            'adx': adx,
            'ma_alignment': {
                'ma5': ma5,
                'ma10': ma10,
                'ma20': ma20,
                'ma60': ma60
            }
        }

    def identify_support_resistance(self, kline: List[Dict]) -> Dict:
        """识别支撑/压力位"""
        # 使用近60日数据
        recent_kline = kline[:60]

        # 找出局部高点和低点
        highs = self._find_local_peaks([k['high'] for k in recent_kline])
        lows = self._find_local_valleys([k['low'] for k in recent_kline])

        # 聚类相近的价格位
        resistance_levels = self._cluster_prices(highs, threshold=0.03)
        support_levels = self._cluster_prices(lows, threshold=0.03)

        return {
            'resistance_levels': sorted(resistance_levels, reverse=True)[:3],
            'support_levels': sorted(support_levels, reverse=True)[:3]
        }

    def analyze_indicators(self, indicators: Dict) -> Dict:
        """综合技术指标分析"""
        signals = {}

        # MACD信号
        macd_dif = indicators['macd_dif'][-1]
        macd_dea = indicators['macd_dea'][-1]
        if macd_dif > macd_dea and macd_dif > 0:
            signals['macd'] = 'buy'
        elif macd_dif < macd_dea and macd_dif < 0:
            signals['macd'] = 'sell'
        else:
            signals['macd'] = 'neutral'

        # RSI信号
        rsi = indicators['rsi_14'][-1]
        if rsi < 30:
            signals['rsi'] = 'oversold'
        elif rsi > 70:
            signals['rsi'] = 'overbought'
        else:
            signals['rsi'] = 'neutral'

        # KDJ信号
        kdj_k = indicators['kdj_k'][-1]
        kdj_d = indicators['kdj_d'][-1]
        if kdj_k > kdj_d and kdj_k < 80:
            signals['kdj'] = 'buy'
        elif kdj_k < kdj_d and kdj_k > 20:
            signals['kdj'] = 'sell'
        else:
            signals['kdj'] = 'neutral'

        # 计算综合信号强度
        buy_count = sum(1 for s in signals.values() if s == 'buy')
        sell_count = sum(1 for s in signals.values() if s == 'sell')

        if buy_count >= 2:
            overall_signal = 'buy'
            signal_strength = buy_count / len(signals)
        elif sell_count >= 2:
            overall_signal = 'sell'
            signal_strength = sell_count / len(signals)
        else:
            overall_signal = 'neutral'
            signal_strength = 0.5

        return {
            'signals': signals,
            'overall_signal': overall_signal,
            'signal_strength': signal_strength
        }
```

### 4.3 策略解析引擎

**4.3.1 自然语言策略解析**

```python
# engines/strategy_parser.py

class StrategyParser:
    """策略解析引擎：将自然语言转换为结构化条件"""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.validator = ConditionValidator()

    async def parse(self, description: str) -> ParseResult:
        """
        解析自然语言策略描述

        Args:
            description: 自然语言描述

        Returns:
            ParseResult: 解析结果
        """
        # 1. 构建Prompt
        prompt = self._build_parse_prompt(description)

        # 2. 调用LLM
        response = await self.llm_service.complete(prompt)

        # 3. 解析LLM返回的JSON
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            raise ParseError("Failed to parse LLM response")

        # 4. 验证条件合法性
        conditions = [StrategyCondition(**c) for c in parsed['conditions']]
        validation_result = self.validator.validate(conditions)

        # 5. 检测逻辑冲突
        conflicts = self._detect_conflicts(conditions)

        # 6. 生成建议
        suggestions = self._generate_suggestions(conditions, validation_result)

        return ParseResult(
            conditions=conditions,
            conflicts=conflicts,
            suggestions=suggestions,
            confidence=parsed.get('confidence', 0.8)
        )

    def _build_parse_prompt(self, description: str) -> str:
        """构建解析Prompt"""
        return f"""你是一位资深的量化投资专家，擅长将自然语言描述转化为结构化的选股条件。

用户输入：{description}

任务：
1. 识别用户意图（选股/分析/对比）
2. 提取关键实体（财务指标、技术指标、数值范围、时间范围、行业板块）
3. 将条件转化为结构化JSON格式
4. 检测逻辑冲突并给出建议

输出格式（JSON）：
{{
  "intent": "选股",
  "conditions": [
    {{
      "type": "valuation",
      "field": "pe_ttm",
      "operator": "<",
      "value": 15,
      "description": "市盈率低于15倍"
    }}
  ],
  "confidence": 0.9
}}

注意事项：
- 对于模糊表达（如"便宜的好公司"），给出合理的默认解释并标注
- 自动添加风险控制条件（排除ST股、停牌股）
- 时间表达式转换：近5日→5个交易日，连续3年→12个季度

请解析上述用户输入并返回JSON："""

    def _detect_conflicts(self, conditions: List[StrategyCondition]) -> List[str]:
        """检测逻辑冲突"""
        conflicts = []

        # 检查同一字段的矛盾条件
        field_conditions = {}
        for cond in conditions:
            key = f"{cond.type}:{cond.field}"
            if key not in field_conditions:
                field_conditions[key] = []
            field_conditions[key].append(cond)

        for key, conds in field_conditions.items():
            if len(conds) > 1:
                # 检查是否存在矛盾
                # 例如: PE < 10 AND PE > 20
                if self._is_contradictory(conds):
                    conflicts.append(
                        f"条件冲突：{conds[0].description} 与 {conds[1].description} 矛盾"
                    )

        return conflicts
```

### 4.4 数据服务层

**4.4.1 数据获取服务**

```python
# services/data_service.py

class DataService:
    """数据获取服务：统一的数据访问接口"""

    def __init__(self, db: Session, cache: Redis, influxdb: InfluxDBClient):
        self.db = db
        self.cache = cache
        self.influxdb = influxdb
        self.akshare_client = AKShareClient()
        self.tushare_client = TushareClient()

    async def get_stock_realtime(self, stock_code: str) -> Dict:
        """获取实时行情（优先从缓存）"""
        # 1. 尝试从Redis获取
        cache_key = f"stock:realtime:{stock_code}"
        cached = await self.cache.get(cache_key)
        if cached:
            return json.loads(cached)

        # 2. 从AKShare获取
        try:
            data = self.akshare_client.get_realtime_quote(stock_code)
        except Exception as e:
            # 3. 降级到Tushare
            logger.warning(f"AKShare failed, fallback to Tushare: {e}")
            data = self.tushare_client.get_realtime_quote(stock_code)

        # 4. 写入缓存
        await self.cache.setex(cache_key, 5, json.dumps(data))

        return data

    async def get_stock_kline(
        self,
        stock_code: str,
        period: str = '1d',
        adjust: str = 'qfq',
        limit: int = 90
    ) -> List[Dict]:
        """获取K线数据"""
        # 1. 尝试从Redis获取
        cache_key = f"stock:kline:{stock_code}:{period}:{adjust}"
        cached = await self.cache.get(cache_key)
        if cached:
            return json.loads(cached)

        # 2. 从InfluxDB查询
        query = f"""
        SELECT open, high, low, close, volume, amount
        FROM stock_kline
        WHERE stock_code='{stock_code}' AND period='{period}' AND adjust='{adjust}'
        ORDER BY time DESC
        LIMIT {limit}
        """
        result = self.influxdb.query(query)
        klines = list(result.get_points())

        # 3. 如果InfluxDB没有数据，从数据源获取
        if not klines:
            klines = self.akshare_client.get_kline(stock_code, period, adjust, limit)
            # 写入InfluxDB
            await self._write_kline_to_influxdb(stock_code, period, adjust, klines)

        # 4. 写入缓存
        await self.cache.setex(cache_key, 3600, json.dumps(klines))

        return klines

    async def get_stock_financials(
        self,
        stock_code: str,
        limit: int = 8
    ) -> List[Dict]:
        """获取财务数据"""
        # 从PostgreSQL查询
        financials = self.db.query(StockFinancial).filter(
            StockFinancial.stock_code == stock_code
        ).order_by(
            StockFinancial.report_date.desc()
        ).limit(limit).all()

        return [f.to_dict() for f in financials]
```

---

## 5. AI引擎设计

### 5.1 LLM集成方案

**5.1.1 多模型支持架构**

```python
# services/ai_service.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class LLMProvider(ABC):
    """LLM提供商抽象基类"""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """文本补全"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """对话补全"""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4提供商"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    async def complete(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 2000)
        )
        return response.choices[0].message.content

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 2000)
        )
        return response.choices[0].message.content

class DeepSeekProvider(LLMProvider):
    """DeepSeek提供商"""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = model

    async def complete(self, prompt: str, **kwargs) -> str:
        # 实现与OpenAI类似
        pass

class AIService:
    """AI服务：统一的LLM访问接口"""

    def __init__(self, config: Dict):
        self.providers = {
            'openai': OpenAIProvider(
                api_key=config['openai_api_key'],
                model=config.get('openai_model', 'gpt-4-turbo')
            ),
            'deepseek': DeepSeekProvider(
                api_key=config['deepseek_api_key'],
                model=config.get('deepseek_model', 'deepseek-chat')
            )
        }
        self.default_provider = config.get('default_provider', 'openai')
        self.cache = Redis()

    async def complete(
        self,
        prompt: str,
        provider: Optional[str] = None,
        use_cache: bool = True,
        **kwargs
    ) -> str:
        """
        文本补全（支持缓存）

        Args:
            prompt: 提示词
            provider: 指定提供商 (openai/deepseek)
            use_cache: 是否使用缓存

        Returns:
            str: 生成的文本
        """
        # 1. 检查缓存
        if use_cache:
            cache_key = f"llm:complete:{hashlib.md5(prompt.encode()).hexdigest()}"
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        # 2. 选择提供商
        provider_name = provider or self.default_provider
        llm_provider = self.providers[provider_name]

        # 3. 调用LLM
        try:
            result = await llm_provider.complete(prompt, **kwargs)
        except Exception as e:
            # 4. 失败时切换到备用提供商
            logger.error(f"LLM call failed: {e}")
            if provider_name == 'openai':
                logger.info("Fallback to DeepSeek")
                result = await self.providers['deepseek'].complete(prompt, **kwargs)
            else:
                raise

        # 5. 写入缓存
        if use_cache:
            await self.cache.setex(cache_key, 3600, result)

        return result
```

### 5.2 Prompt工程

**5.2.1 Prompt模板管理**

```python
# prompts/templates.py

class PromptTemplate:
    """Prompt模板基类"""

    def __init__(self, template: str):
        self.template = template

    def format(self, **kwargs) -> str:
        """格式化模板"""
        return self.template.format(**kwargs)

# 策略解析Prompt
STRATEGY_PARSE_PROMPT = PromptTemplate("""
你是一位资深的量化投资专家，擅长将自然语言描述转化为结构化的选股条件。

用户输入：{user_input}

任务：
1. 识别用户意图（选股/分析/对比）
2. 提取关键实体（财务指标、技术指标、数值范围、时间范围、行业板块）
3. 将条件转化为结构化JSON格式
4. 检测逻辑冲突并给出建议

输出格式（JSON）：
{{
  "intent": "选股",
  "conditions": [
    {{
      "type": "valuation",
      "field": "pe_ttm",
      "operator": "<",
      "value": 15,
      "description": "市盈率低于15倍"
    }}
  ],
  "conflicts": [],
  "suggestions": [],
  "confidence": 0.9
}}

字段映射规则：
- PE、市盈率 → pe_ttm
- PB、市净率 → pb
- ROE、净资产收益率 → roe
- 负债率 → debt_ratio
- 主力资金 → main_capital_inflow
- 北向资金 → northbound_capital

时间表达式转换：
- "近5日" → 5个交易日
- "近一个月" → 20个交易日
- "连续3年" → 12个季度

注意事项：
- 对于模糊表达（如"便宜的好公司"），给出合理的默认解释
- 自动添加风险控制条件（排除ST股、停牌股）
- 检测逻辑冲突（如PE<10且PE>20）

请解析上述用户输入并返回JSON：
""")

# 基本面分析Prompt
FUNDAMENTAL_ANALYSIS_PROMPT = PromptTemplate("""
你是一位资深的价值投资分析师，擅长分析上市公司的基本面。

股票信息：
- 股票代码：{stock_code}
- 股票名称：{stock_name}
- 所属行业：{industry}

财务数据：
{financial_data}

任务：
1. 评估财务健康度（盈利能力、偿债能力、成长能力、运营能力、现金流）
2. 分析盈利能力趋势（ROE、毛利率、净利率）
3. 评估成长性（营收/净利润CAGR）
4. 判断估值合理性（PE/PB分位、PEG、DCF）

输出格式（JSON）：
{{
  "financial_health_score": 85,
  "profitability_trend": "improving",
  "growth_assessment": "steady",
  "valuation_judgment": "fair",
  "analysis": "详细分析文本...",
  "risk_warnings": ["风险点1", "风险点2"]
}}

注意事项：
- 使用专业术语但保持通俗易懂
- 每个结论必须附带数据依据
- 指出潜在风险点
- 与行业平均水平对比

请分析上述财务数据并返回JSON：
""")

# 技术面分析Prompt
TECHNICAL_ANALYSIS_PROMPT = PromptTemplate("""
你是一位资深的技术分析师，擅长解读K线图和技术指标。

股票信息：
- 股票代码：{stock_code}
- 当前价：{current_price}

技术数据：
- 均线系统：{ma_data}
- 技术指标：{indicators}
- 成交量：{volume_data}

任务：
1. 判断当前趋势（强势上涨/弱势上涨/横盘整理/弱势下跌/强势下跌）
2. 识别关键支撑/压力位
3. 综合技术指标给出买卖信号
4. 提供操作建议

输出格式（JSON）：
{{
  "trend": "strong_uptrend",
  "support_levels": [1850, 1820, 1780],
  "resistance_levels": [1900, 1950, 2000],
  "technical_signal": "buy",
  "signal_strength": 0.90,
  "analysis": "详细分析文本...",
  "operation_advice": "操作建议..."
}}

注意事项：
- 技术分析不是绝对的，需结合基本面
- 标注信号强度和可信度
- 给出具体的支撑/压力位

请分析上述技术数据并返回JSON：
""")

# 综合评估Prompt
COMPREHENSIVE_EVALUATION_PROMPT = PromptTemplate("""
你是一位资深的投资顾问，需要综合基本面、技术面、资金面给出投资建议。

股票信息：{stock_info}
基本面分析：{fundamental_analysis}
技术面分析：{technical_analysis}
资金面分析：{capital_flow_analysis}

任务：
1. 计算综合评分（1-10分）
2. 评估风险等级（低/中/高）
3. 给出操作建议（买入/持有/观望/卖出）
4. 总结投资逻辑
5. 列出风险提示
6. 提供操作策略（仓位、买入价、止损价、目标价）

输出格式（JSON）：
{{
  "overall_score": 8.2,
  "risk_level": "medium",
  "recommendation": "buy",
  "investment_logic": ["逻辑1", "逻辑2", "逻辑3"],
  "risk_warnings": ["风险1", "风险2"],
  "operation_strategy": {{
    "position": "20%-30%",
    "entry_price": "1850-1875",
    "stop_loss": 1780,
    "target_price": "1950-2000",
    "holding_period": "3-6个月"
  }}
}}

评分维度（总分10分）：
- 基本面：35%
- 技术面：25%
- 资金面：20%
- 估值：15%
- 消息面：5%

注意事项：
- 必须包含免责声明：本分析仅供参考，不构成投资建议
- 风险提示必须明确具体
- 操作策略需考虑风险收益比

请综合分析并返回JSON：
""")
```

**5.2.2 Few-Shot Learning示例**

```python
# prompts/few_shot_examples.py

STRATEGY_PARSE_EXAMPLES = [
    {
        "input": "找出PE低于15，ROE连续3年大于15%的股票",
        "output": {
            "intent": "选股",
            "conditions": [
                {
                    "type": "valuation",
                    "field": "pe_ttm",
                    "operator": "<",
                    "value": 15,
                    "description": "市盈率低于15倍"
                },
                {
                    "type": "profitability",
                    "field": "roe",
                    "operator": ">",
                    "value": 0.15,
                    "duration": "3_years",
                    "description": "ROE连续3年大于15%"
                }
            ],
            "conflicts": [],
            "suggestions": [],
            "confidence": 0.95
        }
    },
    {
        "input": "筛选市值在100-500亿之间，近一个月涨幅超过10%的科技股",
        "output": {
            "intent": "选股",
            "conditions": [
                {
                    "type": "market_cap",
                    "field": "market_cap",
                    "operator": "between",
                    "value": [10000000000, 50000000000],
                    "description": "市值在100-500亿之间"
                },
                {
                    "type": "price_change",
                    "field": "pct_change",
                    "operator": ">",
                    "value": 0.10,
                    "period": "20_days",
                    "description": "近20日涨幅超过10%"
                },
                {
                    "type": "industry",
                    "field": "industry",
                    "operator": "in",
                    "value": ["电子", "计算机", "通信"],
                    "description": "科技行业"
                }
            ],
            "conflicts": [],
            "suggestions": [],
            "confidence": 0.90
        }
    }
]

def build_few_shot_prompt(user_input: str) -> str:
    """构建包含Few-Shot示例的Prompt"""
    examples_text = "\n\n".join([
        f"示例{i+1}：\n输入：{ex['input']}\n输出：{json.dumps(ex['output'], ensure_ascii=False, indent=2)}"
        for i, ex in enumerate(STRATEGY_PARSE_EXAMPLES)
    ])

    return f"""
{examples_text}

现在请解析以下用户输入：
输入：{user_input}
输出：
"""
```

### 5.3 Agent架构

**5.3.1 Agent编排器**

```python
# agents/orchestrator.py

class AgentOrchestrator:
    """Agent编排器：协调多个Agent完成复杂任务"""

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self.agents = {
            'data': DataAgent(ai_service),
            'fundamental': FundamentalAnalysisAgent(ai_service),
            'technical': TechnicalAnalysisAgent(ai_service),
            'capital': CapitalFlowAgent(ai_service),
            'evaluator': EvaluatorAgent(ai_service)
        }

    async def generate_analysis_report(
        self,
        stock_code: str,
        data: Dict,
        report_type: str = 'comprehensive'
    ) -> AnalysisReport:
        """
        生成分析报告（编排多个Agent）

        Args:
            stock_code: 股票代码
            data: 股票数据
            report_type: 报告类型

        Returns:
            AnalysisReport: 分析报告
        """
        start_time = time.time()

        # 1. 并行执行分析Agent
        tasks = []

        if report_type in ['comprehensive', 'fundamental']:
            tasks.append(
                self.agents['fundamental'].analyze(stock_code, data)
            )

        if report_type in ['comprehensive', 'technical']:
            tasks.append(
                self.agents['technical'].analyze(stock_code, data)
            )

        if report_type in ['comprehensive', 'capital']:
            tasks.append(
                self.agents['capital'].analyze(stock_code, data)
            )

        # 2. 等待所有Agent完成
        results = await asyncio.gather(*tasks)

        # 3. 综合评估Agent汇总结果
        evaluation = await self.agents['evaluator'].evaluate(
            stock_code=stock_code,
            fundamental_analysis=results[0] if len(results) > 0 else None,
            technical_analysis=results[1] if len(results) > 1 else None,
            capital_analysis=results[2] if len(results) > 2 else None
        )

        # 4. 构建完整报告
        report = AnalysisReport(
            stock_code=stock_code,
            stock_name=data['stock_info']['name'],
            report_type=report_type,
            fundamental_analysis=results[0] if len(results) > 0 else None,
            technical_analysis=results[1] if len(results) > 1 else None,
            capital_analysis=results[2] if len(results) > 2 else None,
            ai_evaluation=evaluation,
            generated_at=int(time.time()),
            generation_time_ms=int((time.time() - start_time) * 1000)
        )

        return report
```

**5.3.2 基本面分析Agent**

```python
# agents/fundamental_agent.py

class FundamentalAnalysisAgent:
    """基本面分析Agent"""

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self.analyzer = FundamentalAnalyzer()

    async def analyze(self, stock_code: str, data: Dict) -> Dict:
        """
        执行基本面分析

        Args:
            stock_code: 股票代码
            data: 股票数据

        Returns:
            Dict: 基本面分析结果
        """
        # 1. 计算财务指标
        financial_health = self.analyzer.analyze_financial_health(
            data['financials']
        )

        # 2. 构建Prompt
        prompt = FUNDAMENTAL_ANALYSIS_PROMPT.format(
            stock_code=stock_code,
            stock_name=data['stock_info']['name'],
            industry=data['stock_info']['industry'],
            financial_data=json.dumps(data['financials'], ensure_ascii=False, indent=2)
        )

        # 3. 调用LLM
        response = await self.ai_service.complete(
            prompt=prompt,
            temperature=0.3,  # 降低温度以提高准确性
            max_tokens=2000
        )

        # 4. 解析LLM返回
        try:
            ai_analysis = json.loads(response)
        except json.JSONDecodeError:
            # 如果LLM返回的不是有效JSON，使用正则提取
            ai_analysis = self._extract_json_from_text(response)

        # 5. 合并结果
        return {
            **financial_health,
            **ai_analysis
        }
```

**5.3.3 技术面分析Agent**

```python
# agents/technical_agent.py

class TechnicalAnalysisAgent:
    """技术面分析Agent"""

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self.analyzer = TechnicalAnalyzer()

    async def analyze(self, stock_code: str, data: Dict) -> Dict:
        """执行技术面分析"""
        # 1. 计算技术指标
        trend = self.analyzer.analyze_trend(data['kline'], data['indicators'])
        support_resistance = self.analyzer.identify_support_resistance(data['kline'])
        indicator_signals = self.analyzer.analyze_indicators(data['indicators'])

        # 2. 构建Prompt
        prompt = TECHNICAL_ANALYSIS_PROMPT.format(
            stock_code=stock_code,
            current_price=data['realtime']['price'],
            ma_data=json.dumps(trend['ma_alignment'], ensure_ascii=False),
            indicators=json.dumps(indicator_signals, ensure_ascii=False),
            volume_data=json.dumps(data['realtime']['volume'], ensure_ascii=False)
        )

        # 3. 调用LLM
        response = await self.ai_service.complete(prompt, temperature=0.3)
        ai_analysis = json.loads(response)

        # 4. 合并结果
        return {
            'trend': trend['trend'],
            'support_levels': support_resistance['support_levels'],
            'resistance_levels': support_resistance['resistance_levels'],
            'indicators': indicator_signals,
            **ai_analysis
        }
```

### 5.4 RAG实现

**5.4.1 向量化与检索**

```python
# services/rag_service.py

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class RAGService:
    """RAG服务：检索增强生成"""

    def __init__(self, qdrant_client: QdrantClient, openai_client: OpenAI):
        self.qdrant = qdrant_client
        self.openai = openai_client
        self._ensure_collections()

    def _ensure_collections(self):
        """确保Collection存在"""
        collections = ['stock_announcements', 'stock_news']

        for collection in collections:
            if not self.qdrant.collection_exists(collection):
                self.qdrant.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(
                        size=1536,  # text-embedding-3-small
                        distance=Distance.COSINE
                    )
                )

    async def index_announcement(self, announcement: Dict):
        """索引公告"""
        # 1. 生成向量
        text = f"{announcement['title']}\n{announcement['content']}"
        embedding = await self._generate_embedding(text)

        # 2. 写入Qdrant
        self.qdrant.upsert(
            collection_name='stock_announcements',
            points=[
                PointStruct(
                    id=announcement['id'],
                    vector=embedding,
                    payload={
                        'stock_code': announcement['stock_code'],
                        'stock_name': announcement['stock_name'],
                        'title': announcement['title'],
                        'content': announcement['content'],
                        'ann_date': announcement['ann_date'],
                        'ann_type': announcement['ann_type'],
                        'importance': announcement['importance']
                    }
                )
            ]
        )

    async def search_announcements(
        self,
        query: str,
        stock_code: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """搜索相关公告"""
        # 1. 生成查询向量
        query_embedding = await self._generate_embedding(query)

        # 2. 构建过滤条件
        filter_conditions = None
        if stock_code:
            filter_conditions = {
                "must": [
                    {
                        "key": "stock_code",
                        "match": {"value": stock_code}
                    }
                ]
            }

        # 3. 向量检索
        results = self.qdrant.search(
            collection_name='stock_announcements',
            query_vector=query_embedding,
            query_filter=filter_conditions,
            limit=limit
        )

        return [
            {
                'score': result.score,
                **result.payload
            }
            for result in results
        ]

    async def _generate_embedding(self, text: str) -> List[float]:
        """生成文本向量"""
        response = await self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    async def augment_analysis_with_announcements(
        self,
        stock_code: str,
        analysis_context: str
    ) -> str:
        """用公告信息增强分析"""
        # 1. 检索相关公告
        announcements = await self.search_announcements(
            query=analysis_context,
            stock_code=stock_code,
            limit=5
        )

        # 2. 构建增强上下文
        if not announcements:
            return analysis_context

        announcement_text = "\n\n".join([
            f"【{ann['ann_date']}】{ann['title']}\n{ann['content'][:200]}..."
            for ann in announcements
        ])

        augmented_context = f"""
{analysis_context}

相关公告信息：
{announcement_text}
"""

        return augmented_context
```

**5.4.2 RAG增强的分析流程**

```python
# agents/rag_enhanced_agent.py

class RAGEnhancedAnalysisAgent:
    """RAG增强的分析Agent"""

    def __init__(self, ai_service: AIService, rag_service: RAGService):
        self.ai_service = ai_service
        self.rag_service = rag_service

    async def analyze_with_context(
        self,
        stock_code: str,
        data: Dict
    ) -> Dict:
        """
        使用RAG增强的分析

        流程：
        1. 基础分析
        2. 检索相关公告/新闻
        3. 用检索结果增强Prompt
        4. 生成最终分析
        """
        # 1. 构建基础分析上下文
        base_context = f"""
股票代码：{stock_code}
股票名称：{data['stock_info']['name']}
所属行业：{data['stock_info']['industry']}
当前价格：{data['realtime']['price']}
"""

        # 2. 检索相关公告
        announcements = await self.rag_service.search_announcements(
            query="业绩 重大事项 分红",
            stock_code=stock_code,
            limit=5
        )

        # 3. 构建增强Prompt
        announcement_context = "\n".join([
            f"- {ann['ann_date']}: {ann['title']}"
            for ann in announcements
        ])

        enhanced_prompt = f"""
{base_context}

近期重要公告：
{announcement_context}

请基于以上信息进行分析...
"""

        # 4. 调用LLM生成分析
        response = await self.ai_service.complete(enhanced_prompt)

        return {
            'analysis': response,
            'referenced_announcements': announcements
        }
```

---

## 6. 数据同步设计

### 6.1 实时行情同步

**6.1.1 同步架构**

```python
# tasks/realtime_sync.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class RealtimeSyncTask:
    """实时行情同步任务"""

    def __init__(self, data_service: DataService, cache: Redis, influxdb: InfluxDBClient):
        self.data_service = data_service
        self.cache = cache
        self.influxdb = influxdb
        self.scheduler = AsyncIOScheduler()
        self.is_trading_time = False

    def start(self):
        """启动同步任务"""
        # 交易时间：周一至周五 9:30-11:30, 13:00-15:00
        self.scheduler.add_job(
            self.sync_realtime_quotes,
            trigger='interval',
            seconds=3,
            id='realtime_sync',
            max_instances=1
        )

        # 检查交易时间
        self.scheduler.add_job(
            self.check_trading_time,
            trigger='interval',
            minutes=1,
            id='check_trading_time'
        )

        self.scheduler.start()

    async def check_trading_time(self):
        """检查是否交易时间"""
        now = datetime.now()
        weekday = now.weekday()  # 0=周一, 6=周日

        # 周末不交易
        if weekday >= 5:
            self.is_trading_time = False
            return

        # 检查时间段
        current_time = now.time()
        morning_start = time(9, 30)
        morning_end = time(11, 30)
        afternoon_start = time(13, 0)
        afternoon_end = time(15, 0)

        self.is_trading_time = (
            (morning_start <= current_time <= morning_end) or
            (afternoon_start <= current_time <= afternoon_end)
        )

    async def sync_realtime_quotes(self):
        """同步实时行情"""
        if not self.is_trading_time:
            return

        try:
            # 1. 获取股票列表
            stock_codes = await self._get_active_stocks()

            # 2. 批量获取行情（分批处理，每批500只）
            batch_size = 500
            for i in range(0, len(stock_codes), batch_size):
                batch = stock_codes[i:i+batch_size]
                await self._sync_batch(batch)

            logger.info(f"Synced {len(stock_codes)} stocks")

        except Exception as e:
            logger.error(f"Realtime sync failed: {e}")

    async def _sync_batch(self, stock_codes: List[str]):
        """同步一批股票"""
        # 1. 从AKShare批量获取
        quotes = await self.data_service.akshare_client.get_realtime_quotes_batch(
            stock_codes
        )

        # 2. 并行写入Redis和InfluxDB
        tasks = []
        for code, quote in quotes.items():
            tasks.append(self._write_quote(code, quote))

        await asyncio.gather(*tasks)

    async def _write_quote(self, stock_code: str, quote: Dict):
        """写入单个行情数据"""
        # 1. 写入Redis（实时缓存）
        cache_key = f"stock:realtime:{stock_code}"
        await self.cache.setex(cache_key, 5, json.dumps(quote))

        # 2. 写入InfluxDB（时序存储）
        point = {
            "measurement": "stock_realtime",
            "tags": {
                "stock_code": stock_code,
                "market": quote['market']
            },
            "fields": {
                "price": quote['price'],
                "change": quote['change'],
                "pct_change": quote['pct_change'],
                "volume": quote['volume'],
                "amount": quote['amount'],
                "turnover": quote['turnover']
            },
            "time": datetime.now()
        }
        await self.influxdb.write_points([point])

        # 3. 推送WebSocket（如果有订阅）
        await self._push_to_websocket(stock_code, quote)
```

### 6.2 历史数据同步

**6.2.1 日K线同步**

```python
# tasks/kline_sync.py

class KlineSyncTask:
    """K线数据同步任务"""

    def __init__(self, data_service: DataService, influxdb: InfluxDBClient):
        self.data_service = data_service
        self.influxdb = influxdb
        self.scheduler = AsyncIOScheduler()

    def start(self):
        """启动同步任务"""
        # 每日16:00同步当日K线
        self.scheduler.add_job(
            self.sync_daily_kline,
            trigger=CronTrigger(hour=16, minute=0),
            id='daily_kline_sync'
        )

        self.scheduler.start()

    async def sync_daily_kline(self):
        """同步日K线"""
        try:
            # 1. 获取所有股票
            stock_codes = await self._get_all_stocks()

            # 2. 并发同步（限制并发数）
            semaphore = asyncio.Semaphore(10)  # 最多10个并发
            tasks = [
                self._sync_stock_kline(code, semaphore)
                for code in stock_codes
            ]
            await asyncio.gather(*tasks)

            logger.info(f"Synced kline for {len(stock_codes)} stocks")

        except Exception as e:
            logger.error(f"Kline sync failed: {e}")

    async def _sync_stock_kline(self, stock_code: str, semaphore: asyncio.Semaphore):
        """同步单个股票K线"""
        async with semaphore:
            try:
                # 1. 获取最新K线数据
                klines = await self.data_service.akshare_client.get_kline(
                    stock_code=stock_code,
                    period='1d',
                    adjust='qfq',
                    limit=1  # 只获取最新一条
                )

                if not klines:
                    return

                # 2. 写入InfluxDB
                points = []
                for kline in klines:
                    point = {
                        "measurement": "stock_kline",
                        "tags": {
                            "stock_code": stock_code,
                            "period": "1d",
                            "adjust": "qfq"
                        },
                        "fields": {
                            "open": kline['open'],
                            "high": kline['high'],
                            "low": kline['low'],
                            "close": kline['close'],
                            "volume": kline['volume'],
                            "amount": kline['amount']
                        },
                        "time": datetime.strptime(kline['date'], '%Y-%m-%d')
                    }
                    points.append(point)

                await self.influxdb.write_points(points)

            except Exception as e:
                logger.error(f"Failed to sync kline for {stock_code}: {e}")
```

**6.2.2 财务数据同步**

```python
# tasks/financial_sync.py

class FinancialSyncTask:
    """财务数据同步任务"""

    def __init__(self, data_service: DataService, db: Session):
        self.data_service = data_service
        self.db = db
        self.scheduler = AsyncIOScheduler()

    def start(self):
        """启动同步任务"""
        # 每日凌晨2:00同步财务数据
        self.scheduler.add_job(
            self.sync_financials,
            trigger=CronTrigger(hour=2, minute=0),
            id='financial_sync'
        )

        self.scheduler.start()

    async def sync_financials(self):
        """同步财务数据"""
        try:
            # 1. 获取需要更新的股票（最近发布财报的）
            stocks_to_update = await self._get_stocks_with_new_reports()

            # 2. 同步财务数据
            for stock_code in stocks_to_update:
                await self._sync_stock_financials(stock_code)

            logger.info(f"Synced financials for {len(stocks_to_update)} stocks")

        except Exception as e:
            logger.error(f"Financial sync failed: {e}")

    async def _sync_stock_financials(self, stock_code: str):
        """同步单个股票财务数据"""
        try:
            # 1. 从Tushare获取财务数据
            financials = await self.data_service.tushare_client.get_financials(
                stock_code=stock_code,
                limit=8  # 最近8个季度
            )

            # 2. 写入PostgreSQL（使用upsert）
            for financial in financials:
                stmt = insert(StockFinancial).values(
                    stock_code=stock_code,
                    report_date=financial['report_date'],
                    report_type=financial['report_type'],
                    **financial
                ).on_conflict_do_update(
                    index_elements=['stock_code', 'report_date', 'report_type'],
                    set_=financial
                )
                self.db.execute(stmt)

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to sync financials for {stock_code}: {e}")
            self.db.rollback()
```

### 6.3 任务调度

**6.3.1 调度器配置**

```python
# core/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

def create_scheduler() -> AsyncIOScheduler:
    """创建调度器"""
    jobstores = {
        'default': RedisJobStore(
            host='localhost',
            port=6379,
            db=1
        )
    }

    executors = {
        'default': ThreadPoolExecutor(20),
        'processpool': ProcessPoolExecutor(5)
    }

    job_defaults = {
        'coalesce': False,  # 不合并错过的任务
        'max_instances': 1,  # 同一任务最多1个实例
        'misfire_grace_time': 60  # 错过60秒内的任务仍执行
    }

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone='Asia/Shanghai'
    )

    return scheduler

# 注册所有任务
def register_tasks(scheduler: AsyncIOScheduler):
    """注册所有定时任务"""
    # 实时行情同步（交易时间每3秒）
    realtime_task = RealtimeSyncTask(...)
    realtime_task.start()

    # 日K线同步（每日16:00）
    kline_task = KlineSyncTask(...)
    kline_task.start()

    # 财务数据同步（每日凌晨2:00）
    financial_task = FinancialSyncTask(...)
    financial_task.start()

    # 策略自动执行（每日9:00）
    scheduler.add_job(
        auto_execute_strategies,
        trigger=CronTrigger(hour=9, minute=0),
        id='auto_execute_strategies'
    )
```

### 6.4 容错机制

**6.4.1 重试机制**

```python
# utils/retry.py

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError))
)
async def fetch_with_retry(url: str):
    """带重试的HTTP请求"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
```

**6.4.2 数据源切换**

```python
# services/data_source_manager.py

class DataSourceManager:
    """数据源管理器：自动切换数据源"""

    def __init__(self):
        self.sources = {
            'akshare': AKShareClient(),
            'tushare': TushareClient()
        }
        self.primary = 'akshare'
        self.fallback = 'tushare'
        self.failure_count = {}

    async def get_realtime_quote(self, stock_code: str) -> Dict:
        """获取实时行情（自动切换数据源）"""
        # 1. 尝试主数据源
        try:
            return await self.sources[self.primary].get_realtime_quote(stock_code)
        except Exception as e:
            logger.warning(f"Primary source failed: {e}")
            self.failure_count[self.primary] = self.failure_count.get(self.primary, 0) + 1

            # 2. 切换到备用数据源
            try:
                return await self.sources[self.fallback].get_realtime_quote(stock_code)
            except Exception as e2:
                logger.error(f"Fallback source also failed: {e2}")
                raise

    async def check_health(self):
        """检查数据源健康状态"""
        for name, source in self.sources.items():
            try:
                await source.ping()
                self.failure_count[name] = 0
            except Exception:
                self.failure_count[name] = self.failure_count.get(name, 0) + 1

        # 如果主数据源失败次数过多，切换主备
        if self.failure_count.get(self.primary, 0) > 10:
            logger.warning(f"Switching primary source from {self.primary} to {self.fallback}")
            self.primary, self.fallback = self.fallback, self.primary
```

**6.4.3 数据校验**

```python
# utils/data_validator.py

class DataValidator:
    """数据校验器"""

    @staticmethod
    def validate_realtime_quote(quote: Dict) -> bool:
        """校验实时行情数据"""
        # 1. 必填字段检查
        required_fields = ['code', 'price', 'volume', 'amount']
        if not all(field in quote for field in required_fields):
            return False

        # 2. 数值合理性检查
        if quote['price'] <= 0:
            return False

        if quote['volume'] < 0 or quote['amount'] < 0:
            return False

        # 3. 涨跌幅合理性检查
        if 'pct_change' in quote:
            # ST股涨跌幅限制±5%，普通股±10%
            max_change = 0.05 if quote.get('is_st') else 0.10
            if abs(quote['pct_change']) > max_change + 0.01:  # 允许1%误差
                logger.warning(f"Abnormal pct_change: {quote['pct_change']}")
                return False

        return True

    @staticmethod
    def validate_kline(kline: Dict) -> bool:
        """校验K线数据"""
        # 1. OHLC关系检查
        if not (kline['low'] <= kline['open'] <= kline['high'] and
                kline['low'] <= kline['close'] <= kline['high']):
            return False

        # 2. 成交量成交额一致性
        if kline['volume'] > 0 and kline['amount'] <= 0:
            return False

        return True
```

---

## 7. 缓存策略设计

### 7.1 多级缓存架构

```
┌─────────────────────────────────────────┐
│  L1: 本地内存缓存 (LRU Cache)           │
│  - 股票基础信息                         │
│  - 板块映射关系                         │
│  - TTL: 24小时                          │
│  - 容量: 1GB                            │
└─────────────────┬───────────────────────┘
                  ↓ Miss
┌─────────────────────────────────────────┐
│  L2: Redis缓存                          │
│  - 实时行情 (TTL: 5秒)                  │
│  - K线数据 (TTL: 1小时)                 │
│  - 分析报告 (TTL: 1小时)                │
│  - 策略结果 (TTL: 30分钟)               │
└─────────────────┬───────────────────────┘
                  ↓ Miss
┌─────────────────────────────────────────┐
│  L3: 数据库                             │
│  - PostgreSQL (关系数据)                │
│  - InfluxDB (时序数据)                  │
└─────────────────────────────────────────┘
```

**7.1.1 本地内存缓存实现**

```python
# core/cache.py

from cachetools import LRUCache, TTLCache
from threading import Lock

class LocalCache:
    """本地内存缓存"""

    def __init__(self, maxsize: int = 10000, ttl: int = 86400):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = Lock()

    def get(self, key: str):
        """获取缓存"""
        with self.lock:
            return self.cache.get(key)

    def set(self, key: str, value: any):
        """设置缓存"""
        with self.lock:
            self.cache[key] = value

    def delete(self, key: str):
        """删除缓存"""
        with self.lock:
            self.cache.pop(key, None)

    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()

# 全局本地缓存实例
local_cache = LocalCache()
```

### 7.2 缓存更新策略

**7.2.1 Cache-Aside模式**

```python
async def get_stock_info(stock_code: str) -> Dict:
    """获取股票信息（Cache-Aside模式）"""
    # 1. L1缓存
    cache_key = f"stock:info:{stock_code}"
    cached = local_cache.get(cache_key)
    if cached:
        return cached

    # 2. L2缓存
    cached = await redis.get(cache_key)
    if cached:
        data = json.loads(cached)
        local_cache.set(cache_key, data)
        return data

    # 3. 数据库
    stock = db.query(Stock).filter(Stock.stock_code == stock_code).first()
    if not stock:
        raise StockNotFoundError(stock_code)

    data = stock.to_dict()

    # 4. 回写缓存
    await redis.setex(cache_key, 3600, json.dumps(data))
    local_cache.set(cache_key, data)

    return data
```

**7.2.2 Write-Through模式**

```python
async def update_stock_realtime(stock_code: str, quote: Dict):
    """更新实时行情（Write-Through模式）"""
    # 1. 写入数据库
    await influxdb.write_points([{
        "measurement": "stock_realtime",
        "tags": {"stock_code": stock_code},
        "fields": quote,
        "time": datetime.now()
    }])

    # 2. 同步更新缓存
    cache_key = f"stock:realtime:{stock_code}"
    await redis.setex(cache_key, 5, json.dumps(quote))
```

### 7.3 缓存失效处理

**7.3.1 主动失效**

```python
async def invalidate_stock_cache(stock_code: str):
    """主动失效股票相关缓存"""
    patterns = [
        f"stock:info:{stock_code}",
        f"stock:realtime:{stock_code}",
        f"stock:kline:{stock_code}:*",
        f"analysis:report:{stock_code}"
    ]

    for pattern in patterns:
        if '*' in pattern:
            # 模糊匹配删除
            keys = await redis.keys(pattern)
            if keys:
                await redis.delete(*keys)
        else:
            await redis.delete(pattern)

    # 清除本地缓存
    local_cache.delete(f"stock:info:{stock_code}")
```

**7.3.2 缓存预热**

```python
async def warmup_cache():
    """缓存预热"""
    # 1. 预热热门股票
    hot_stocks = ["600519", "000858", "601318", "600036", "000001"]

    for code in hot_stocks:
        try:
            # 预热实时行情
            quote = await data_service.get_stock_realtime(code)

            # 预热K线数据
            kline = await data_service.get_stock_kline(code, period='1d', limit=90)

            # 预热股票信息
            info = await get_stock_info(code)

        except Exception as e:
            logger.error(f"Failed to warmup cache for {code}: {e}")

    logger.info(f"Cache warmed up for {len(hot_stocks)} stocks")
```

---

## 8. 安全设计

### 8.1 认证授权

**8.1.1 JWT认证实现**

```python
# core/security.py

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key-here"  # 从环境变量读取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """密码哈希"""
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    """创建访问Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """创建刷新Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """验证Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise InvalidTokenError()
```

**8.1.2 认证依赖**

```python
# api/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    token = credentials.credentials

    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user
```

### 8.2 数据加密

**8.2.1 敏感数据加密**

```python
# utils/encryption.py

from cryptography.fernet import Fernet
import base64

class Encryptor:
    """数据加密器"""

    def __init__(self, key: str):
        self.cipher = Fernet(key.encode())

    def encrypt(self, data: str) -> str:
        """加密"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """解密"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# 全局加密器
encryptor = Encryptor(os.getenv('ENCRYPTION_KEY'))
```

### 8.3 API安全

**8.3.1 速率限制**

```python
# middleware/rate_limit.py

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"]
)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "code": 4001,
            "message": "Rate limit exceeded",
            "error": {
                "type": "RateLimitExceeded",
                "details": str(exc)
            }
        }
    )
```

### 8.4 合规设计

**8.4.1 风险提示中间件**

```python
# middleware/compliance.py

@app.middleware("http")
async def add_risk_warning(request: Request, call_next):
    """添加风险提示响应头"""
    response = await call_next(request)

    # 分析报告相关接口添加风险提示
    if '/analyze' in request.url.path or '/strategies' in request.url.path:
        response.headers["X-Risk-Warning"] = "股市有风险，投资需谨慎。本分析仅供参考，不构成投资建议。"

    return response
```

---

## 9. 部署架构

### 9.1 开发环境

**docker-compose.yml**

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://stock_ai:password@postgres:5432/stock_ai
      - REDIS_URL=redis://redis:6379/0
      - INFLUXDB_URL=http://influxdb:8086
    depends_on:
      - postgres
      - redis
      - influxdb

  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=stock_ai
      - POSTGRES_USER=stock_ai
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  influxdb:
    image: influxdb:2.7
    ports:
      - "8086:8086"
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=password
      - DOCKER_INFLUXDB_INIT_ORG=stock_ai
      - DOCKER_INFLUXDB_INIT_BUCKET=stock_data
    volumes:
      - influxdb_data:/var/lib/influxdb2

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  redis_data:
  influxdb_data:
  qdrant_data:
```

### 9.2 生产环境

**9.2.1 服务器配置**

```yaml
# MVP阶段服务器配置
应用服务器 × 2:
  - 规格: 2核4G
  - 系统: Ubuntu 22.04
  - 软件: Docker, Nginx
  - 成本: 约400元/月/台

数据库服务器 × 1:
  - 规格: 4核8G
  - 系统: Ubuntu 22.04
  - 软件: PostgreSQL 15, Redis 7
  - 成本: 约800元/月

时序数据库服务器 × 1:
  - 规格: 4核8G
  - 系统: Ubuntu 22.04
  - 软件: InfluxDB 2.7
  - 成本: 约800元/月

总成本: 约2400元/月
```

### 9.3 CI/CD流程

**.github/workflows/deploy.yml**

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          ssh user@server "cd /app && git pull && docker-compose up -d"
```

---

## 10. 监控与日志

### 10.1 监控指标

**10.1.1 Prometheus配置**

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'stock-ai-backend'
    static_configs:
      - targets: ['localhost:8000']
```

### 10.2 日志规范

**10.2.1 日志格式**

```python
# core/logging.py

import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON格式日志"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "stock-ai-backend",
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id

        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)
```

### 10.3 告警机制

**10.3.1 告警规则**

```yaml
# alerts.yml
groups:
  - name: stock_ai_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 10
        for: 5m
        annotations:
          summary: "High response time detected"
```

---

## 附录

### A. 开发规范

**A.1 代码规范**
- Python: PEP 8
- TypeScript: ESLint + Prettier
- 提交信息: Conventional Commits

**A.2 分支策略**
- main: 生产环境
- develop: 开发环境
- feature/*: 功能分支

### B. 性能指标

| 指标 | 目标值 | 监控方式 |
|------|--------|---------|
| API响应时间(P95) | <2秒 | Prometheus |
| 选股执行时间 | <5秒 | 应用日志 |
| 分析报告生成 | <10秒 | 应用日志 |
| 系统可用性 | >99.5% | Uptime监控 |

---

**文档版本**: v1.0
**创建日期**: 2026-02-12
**状态**: 已完成
**下一步**: 开始MVP开发
