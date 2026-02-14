import api from './api'
import type { ApiResponse, AnalysisReport, KLineData, FinancialItem, NewsItem } from '@/types'

export const analysisApi = {
  analyze: (stockCode: string, forceRefresh = false): Promise<ApiResponse<AnalysisReport>> =>
    api.post(`/stocks/${stockCode}/analyze`, null, {
      params: { force_refresh: forceRefresh },
      timeout: 300000,
    }),

  getReport: (stockCode: string): Promise<ApiResponse<AnalysisReport>> =>
    api.get(`/stocks/${stockCode}/report`),

  getKLine: (
    stockCode: string,
    params?: { period?: '1d' | '1w' | '1M'; days?: number }
  ): Promise<ApiResponse<KLineData[]>> =>
    api.get(`/stocks/${stockCode}/kline`, { params }),

  getFinancial: (
    stockCode: string,
    params?: { years?: number }
  ): Promise<ApiResponse<FinancialItem[]>> =>
    api.get(`/stocks/${stockCode}/financial`, { params }),

  getNews: (
    stockCode: string,
    limit: number = 20
  ): Promise<ApiResponse<NewsItem[]>> =>
    api.get(`/stocks/${stockCode}/news`, { params: { limit } }),

  getPeers: (
    stockCode: string,
    limit: number = 6
  ): Promise<ApiResponse<{ industry: string; target: any; peers: any[] }>> =>
    api.get(`/stocks/${stockCode}/peers`, { params: { limit } }),
}
