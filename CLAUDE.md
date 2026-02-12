# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-driven A-share stock analysis application for individual investors. Provides intelligent stock picking, deep analysis, and natural language strategy customization.

**Current Status**: Planning phase - architecture and requirements defined, implementation pending.

## Architecture

### Tech Stack

**Backend**:
- FastAPI 0.110+ (Python 3.11+)
- PostgreSQL 15+ (relational data: users, strategies, stock info, financials)
- InfluxDB 2.7+ (time-series data: K-lines, real-time quotes, indicators)
- Redis 7.2+ (caching, sessions)
- Qdrant 1.7+ (vector search for announcements/news)
- Celery 5.x + Redis (async task queue)
- LangChain 0.1.x (LLM integration)

**Frontend**:
- React 18.2+ with TypeScript 5.0+
- Ant Design 5.x (UI components)
- Apache ECharts 5.x (charts)
- Zustand 4.x (state management)
- TanStack Query 5.x (data fetching)
- Vite 5.x (build tool)

**Infrastructure**:
- Docker 24+ / Docker Compose
- Nginx 1.24+ (reverse proxy, load balancing)

### Layered Architecture

```
Client Layer (React + Ant Design + ECharts)
    ↓
Access Layer (Nginx)
    ↓
Application Layer (FastAPI Services)
  - StockPick Service
  - Analysis Service
  - Strategy Service
  - User Service
    ↓
Business Logic Layer
  - Stock Picker Engine (classic + custom strategies)
  - Analysis Engine (fundamental + technical + capital flow)
  - AI Engine (LLM integration, Agent orchestration, RAG)
  - Data Service (fetch, clean, calculate indicators)
    ↓
Data Access Layer (PostgreSQL, InfluxDB, Redis, Qdrant)
    ↓
External Data Sources (AKShare, Tushare Pro, BaoStock)
```

### Module Structure

**Backend** (`backend/`):
- `app/api/v1/` - API routes (stock, strategy, analysis, user)
- `app/core/` - Configuration, security, database, cache
- `app/models/` - SQLAlchemy ORM models
- `app/schemas/` - Pydantic validation schemas
- `app/services/` - Business logic layer
- `app/engines/` - Core engines (stock_picker, analyzer, strategy_parser, indicator)
- `app/agents/` - AI Agents (orchestrator, data_agent, fundamental_agent, technical_agent, evaluator_agent)
- `app/utils/` - Utility functions (indicators, financial calculations, validators)
- `app/tasks/` - Celery async tasks (data sync, strategy execution, report generation)

**Frontend** (`frontend/src/`):
- `components/` - Reusable components (StockCard, Chart, StrategyForm, Layout)
- `pages/` - Page components (StockPicker, StockAnalysis, MyStrategy, Market)
- `services/` - API client wrappers
- `stores/` - Zustand state management
- `hooks/` - Custom React hooks
- `types/` - TypeScript type definitions

## Key Architectural Decisions

### Data Flow Patterns

**Stock Picking Flow**:
1. User inputs strategy conditions → API validates
2. Stock picker engine queries Redis cache (fallback to PostgreSQL)
3. Apply filters, calculate indicators, sort and paginate
4. Return results with metadata

**Individual Stock Analysis Flow**:
1. Check Redis cache (TTL: 1 hour)
2. If cache miss: parallel data fetch (real-time quotes, K-lines, financials, capital flow)
3. AI Agent orchestrator dispatches parallel analysis agents
4. Evaluator agent synthesizes comprehensive report
5. Cache result and return JSON

**Natural Language Strategy Parsing**:
1. User describes strategy in Chinese
2. LLM (GPT-4/DeepSeek) parses to structured JSON conditions
3. Validate conditions and detect logical conflicts
4. User confirms → execute stock picking

### Caching Strategy

**Redis Key Naming**: `{module}:{type}:{id}:{params}`
- `stock:realtime:{code}` - Real-time quotes (TTL: 5s)
- `stock:kline:{code}:{period}:{adjust}` - K-line data (TTL: 1h)
- `analysis:report:{code}` - Analysis reports (TTL: 1h)
- `strategy:result:{id}:{timestamp}` - Strategy results (TTL: 30min)

**Cache Patterns**:
- Cache-Aside for reads (check cache → fetch on miss → populate cache)
- Write-Through for updates (update DB → sync update cache)

### Database Design Principles

**PostgreSQL**: Users, strategies, stock metadata, financials, analysis reports
**InfluxDB**: Time-series data (K-lines, real-time quotes, technical indicators, capital flow)
**Qdrant**: Vector embeddings for semantic search of announcements and news

### AI Agent Architecture

Multi-agent system with orchestrator pattern:
- **Orchestrator Agent**: Coordinates analysis workflow
- **Data Agent**: Fetches and prepares data
- **Fundamental Agent**: Analyzes financials, valuation, growth
- **Technical Agent**: Analyzes price patterns, indicators, trends
- **Evaluator Agent**: Synthesizes multi-dimensional analysis into comprehensive report

## API Design

**Base URL**: `/api/v1`
**Auth**: JWT Bearer Token
**Response Format**:
```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "timestamp": 1707753600
}
```

**Core Endpoints**:
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /strategies/execute` - Execute stock picking strategy
- `POST /strategies/parse` - Parse natural language to structured conditions
- `POST /stocks/{code}/analyze` - Generate comprehensive stock analysis
- `GET /stocks/{code}/kline` - Get K-line data
- `GET /stocks/{code}/realtime` - Get real-time quote

## Development Principles

**Risk Control Priority**: All strategies must include risk filters (ST stocks, delisting risk, liquidity, market cap thresholds)

**Async Processing**: Long-running tasks (analysis, data sync) use Celery for async execution

**Multi-level Caching**: Reduce database load with Redis caching at multiple layers

**Data Source Abstraction**: Isolate external data source dependencies in data service layer for easy switching

**AI Transparency**: All AI-generated analysis must include reasoning process and data sources
