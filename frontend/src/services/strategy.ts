import api from './api'
import type { ApiResponse, Strategy, Stock } from '@/types'

export const strategyApi = {
  execute: (params: {
    strategy_type: string
    limit?: number
    conditions?: Record<string, any>
  }): Promise<ApiResponse<Stock[]>> =>
    api.post('/strategies/execute', params),

  parse: (description: string): Promise<ApiResponse<{ conditions: Record<string, any> }>> =>
    api.post('/strategies/parse', { description }),

  list: (): Promise<ApiResponse<Strategy[]>> =>
    api.get('/strategies'),

  create: (data: Partial<Strategy>): Promise<ApiResponse<Strategy>> =>
    api.post('/strategies', data),

  delete: (id: number): Promise<ApiResponse<void>> =>
    api.delete(`/strategies/${id}`)
}
