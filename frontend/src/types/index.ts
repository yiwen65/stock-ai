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
}

export interface Strategy {
  id: number
  name: string
  strategy_type: string
  conditions: Record<string, any>
  created_at: string
  updated_at?: string
}

export interface AnalysisReport {
  stock_code: string
  stock_name: string
  fundamental: {
    score: number
    summary: string
    details?: Record<string, any>
  }
  technical: {
    score: number
    trend: string
    summary: string
    details?: Record<string, any>
  }
  overall_score: number
  recommendation: 'buy' | 'hold' | 'sell'
  summary: string
  generated_at?: string
}

export interface KLineData {
  date: string
  open: number
  close: number
  high: number
  low: number
  volume: number
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
