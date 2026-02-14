import { create } from 'zustand'
import { Strategy } from '@/types'

interface StrategyState {
  // User's strategies
  strategies: Strategy[]
  setStrategies: (strategies: Strategy[]) => void
  addStrategy: (strategy: Strategy) => void
  updateStrategy: (id: number, strategy: Partial<Strategy>) => void
  deleteStrategy: (id: number) => void

  // Current active strategy
  activeStrategy: Strategy | null
  setActiveStrategy: (strategy: Strategy | null) => void

  // Strategy execution results cache
  executionResults: Map<number, any>
  setExecutionResult: (strategyId: number, result: any) => void
  clearExecutionResults: () => void
}

export const useStrategyStore = create<StrategyState>((set) => ({
  strategies: [],
  setStrategies: (strategies) => set({ strategies }),
  addStrategy: (strategy) =>
    set((state) => ({ strategies: [...state.strategies, strategy] })),
  updateStrategy: (id, updates) =>
    set((state) => ({
      strategies: state.strategies.map(s =>
        s.id === id ? { ...s, ...updates } : s
      )
    })),
  deleteStrategy: (id) =>
    set((state) => ({
      strategies: state.strategies.filter(s => s.id !== id)
    })),

  activeStrategy: null,
  setActiveStrategy: (strategy) => set({ activeStrategy: strategy }),

  executionResults: new Map(),
  setExecutionResult: (strategyId, result) =>
    set((state) => {
      const newResults = new Map(state.executionResults)
      newResults.set(strategyId, result)
      return { executionResults: newResults }
    }),
  clearExecutionResults: () => set({ executionResults: new Map() })
}))
