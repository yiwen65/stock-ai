import { create } from 'zustand'
import { Stock } from '@/types'

interface StockState {
  // Current stock list
  stocks: Stock[]
  setStocks: (stocks: Stock[]) => void

  // Selected stock for analysis
  selectedStock: Stock | null
  setSelectedStock: (stock: Stock | null) => void

  // Real-time quotes cache
  realtimeQuotes: Map<string, Stock>
  updateRealtimeQuote: (stockCode: string, quote: Stock) => void

  // Search history
  searchHistory: string[]
  addSearchHistory: (keyword: string) => void
  clearSearchHistory: () => void
}

export const useStockStore = create<StockState>((set) => ({
  stocks: [],
  setStocks: (stocks) => set({ stocks }),

  selectedStock: null,
  setSelectedStock: (stock) => set({ selectedStock: stock }),

  realtimeQuotes: new Map(),
  updateRealtimeQuote: (stockCode, quote) =>
    set((state) => {
      const newQuotes = new Map(state.realtimeQuotes)
      newQuotes.set(stockCode, quote)
      return { realtimeQuotes: newQuotes }
    }),

  searchHistory: JSON.parse(localStorage.getItem('searchHistory') || '[]'),
  addSearchHistory: (keyword) =>
    set((state) => {
      const history = [keyword, ...state.searchHistory.filter(k => k !== keyword)].slice(0, 10)
      localStorage.setItem('searchHistory', JSON.stringify(history))
      return { searchHistory: history }
    }),
  clearSearchHistory: () => {
    localStorage.removeItem('searchHistory')
    set({ searchHistory: [] })
  }
}))
