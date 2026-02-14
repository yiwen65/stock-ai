import api from './api'
import { Stock, KLineData } from '@/types'

export const stockApi = {
  // Get stock list
  getList: () => api.get<Stock[]>('/stocks'),

  // Get real-time quote
  getQuote: (stockCode: string) =>
    api.get<Stock>(`/stocks/${stockCode}/quote`),

  // Get K-line data
  getKLine: (stockCode: string, params?: {
    period?: '1d' | '1w' | '1M'
    days?: number
  }) => api.get<KLineData[]>(`/stocks/${stockCode}/kline`, { params }),

  // Search stocks by code or name
  search: (q: string, limit: number = 10) =>
    api.get<Stock[]>('/stocks/search', { params: { q, limit } }),

  // Get sector list
  getSectors: () => api.get('/market/sectors'),

  // Get major market indices
  getIndices: () => api.get('/market/indices'),

  // Get market capital flow by sector
  getMarketCapitalFlow: () => api.get('/market/capital-flow'),
}
