import api from './api'
import { Stock, KLineData } from '@/types'

export const stockApi = {
  // Get stock list
  getList: (params?: {
    page?: number
    limit?: number
    keyword?: string
  }) => api.get<Stock[]>('/stocks', { params }),

  // Get stock detail
  getDetail: (stockCode: string) =>
    api.get<Stock>(`/stocks/${stockCode}`),

  // Get real-time quote
  getRealtime: (stockCode: string) =>
    api.get<Stock>(`/stocks/${stockCode}/realtime`),

  // Get K-line data
  getKLine: (stockCode: string, params?: {
    period?: '1d' | '1w' | '1m'
    adjust?: 'qfq' | 'hfq' | 'none'
    start_date?: string
    end_date?: string
  }) => api.get<KLineData[]>(`/stocks/${stockCode}/kline`, { params }),

  // Search stocks
  search: (keyword: string) =>
    api.get<Stock[]>('/stocks/search', { params: { keyword } })
}
