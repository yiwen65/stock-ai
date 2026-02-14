import api from './api'
import type { ApiResponse } from '@/types'

export interface WatchlistItem {
  id: number
  stock_code: string
  stock_name: string
  note: string | null
  created_at: string | null
}

export const watchlistApi = {
  list: (): Promise<ApiResponse<WatchlistItem[]>> =>
    api.get('/watchlist'),

  add: (stock_code: string, stock_name: string, note?: string): Promise<ApiResponse<WatchlistItem>> =>
    api.post('/watchlist', { stock_code, stock_name, note }),

  remove: (stock_code: string): Promise<ApiResponse<void>> =>
    api.delete(`/watchlist/${stock_code}`),

  check: (stock_code: string): Promise<ApiResponse<{ in_watchlist: boolean }>> =>
    api.get(`/watchlist/check/${stock_code}`),
}
