// Type definitions for the stock analysis application

export interface Stock {
  stock_code: string
  stock_name: string
  price: number
  change: number
  pct_change: number
  pe: number | null
  pb: number | null
  market_cap: number
  volume?: number
  turnover_rate?: number
  roe?: number | null
  score?: number | null
  risk_level?: string | null
}

export interface StrategyInfo {
  name: string
  description: string
  category: string
}

export interface Strategy {
  id: number
  name: string
  strategy_type: string
  conditions: Record<string, any>
  created_at: string
  updated_at?: string
}

export interface NewsItem {
  title: string
  content: string
  publish_time: string
  source: string
  url: string
}

export interface DuPontAnalysis {
  roe: number
  net_profit_margin: number
  asset_turnover: number
  equity_multiplier: number
  driver: string
}

export interface FundamentalAnalysis {
  score: number
  valuation: Record<string, number>
  profitability: Record<string, number>
  growth: Record<string, number>
  financial_health: Record<string, number>
  dupont?: DuPontAnalysis
  summary: string
}

export interface TechnicalAnalysis {
  score: number
  trend: string
  support_levels: number[]
  resistance_levels: number[]
  indicators: Record<string, number>
  summary: string
}

export interface CapitalFlowAnalysis {
  score: number
  main_net_inflow: number
  main_inflow_ratio: number
  trend: string
  summary: string
}

export interface IndustryComparisonMetric {
  metric: string
  label: string
  target_value: number
  industry_avg: number
  rank: number
  total: number
  percentile: number
  vs_avg: string
}

export interface IndustryComparison {
  industry: string
  target: Record<string, any> | null
  peers: Record<string, any>[]
  comparison_metrics: IndustryComparisonMetric[]
  industry_position: string
}

export interface NewsAnalysis {
  agent: string
  score: number
  sentiment: string
  key_events: Array<{
    title: string
    category: string
    impact: string
    impact_level: string
  }>
  summary: string
  analysis: string
}

export interface AnalysisReport {
  stock_code: string
  stock_name: string
  fundamental: FundamentalAnalysis
  technical: TechnicalAnalysis
  capital_flow: CapitalFlowAnalysis
  industry_comparison?: IndustryComparison | null
  overall_score: number
  risk_level: 'low' | 'medium' | 'high'
  recommendation: 'buy' | 'hold' | 'watch' | 'sell'
  confidence?: 'high' | 'medium' | 'low'
  summary: string
  generated_at?: number
}

export interface KLineData {
  date: string
  open: number
  close: number
  high: number
  low: number
  volume: number
  amount?: number
}

export interface FinancialItem {
  stock_code: string
  report_date: string
  eps: number
  roe: number
  revenue: number
  net_profit: number
  revenue_growth: number
  net_profit_growth: number
  debt_ratio: number
  current_ratio: number
  gross_margin: number
  net_margin: number
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
  timestamp: number
}

export interface User {
  id: number
  username: string
  email: string
  created_at: string
}
