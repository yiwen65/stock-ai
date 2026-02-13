import api from './api'
import type { ApiResponse, AnalysisReport, KLineData } from '@/types'

export const analysisApi = {
  analyze: (stockCode: string): Promise<ApiResponse<AnalysisReport>> =>
    api.post(`/stocks/${stockCode}/analyze`),

  getReport: (stockCode: string): Promise<ApiResponse<AnalysisReport>> =>
    api.get(`/stocks/${stockCode}/report`),

  getKLine: (
    stockCode: string,
    params?: { period?: string; adjust?: string; start_date?: string; end_date?: string }
  ): Promise<ApiResponse<KLineData[]>> =>
    api.get(`/stocks/${stockCode}/kline`, { params })
}
