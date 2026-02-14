import api from './api'
import type { ApiResponse, Strategy, Stock } from '@/types'

export interface UserStrategyPayload {
  name: string
  strategy_type: string
  conditions: Record<string, any>
}

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

  // ---- User Strategy CRUD (backend-persisted) ----

  listUserStrategies: (): Promise<ApiResponse<Strategy[]>> =>
    api.get('/strategies/user/list'),

  createUserStrategy: (data: UserStrategyPayload): Promise<ApiResponse<Strategy>> =>
    api.post('/strategies/user/create', data),

  updateUserStrategy: (id: number, data: Partial<UserStrategyPayload>): Promise<ApiResponse<Strategy>> =>
    api.put(`/strategies/user/${id}`, data),

  deleteUserStrategy: (id: number): Promise<ApiResponse<void>> =>
    api.delete(`/strategies/user/${id}`),

  // ---- Industries ----

  listIndustries: (): Promise<ApiResponse<string[]>> =>
    api.get('/strategies/industries'),

  // ---- Execution History ----

  recordExecution: (strategyId: number, resultCount: number, snapshot?: Record<string, any>[]): Promise<ApiResponse<any>> =>
    api.post(`/strategies/user/${strategyId}/executions`, null, {
      params: { result_count: resultCount },
      ...(snapshot ? { data: snapshot } : {}),
    }),

  listExecutions: (strategyId: number, limit = 10): Promise<ApiResponse<any[]>> =>
    api.get(`/strategies/user/${strategyId}/executions`, { params: { limit } }),
}
