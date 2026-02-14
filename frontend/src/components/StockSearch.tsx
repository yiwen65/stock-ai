import { useState, useCallback, useRef, useEffect } from 'react'
import { AutoComplete, Input } from 'antd'
import { Search, Clock, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { stockApi } from '@/services/stock'
import { useStockStore } from '@/stores/stockStore'

export default function StockSearch() {
  const navigate = useNavigate()
  const [options, setOptions] = useState<{ value: string; label: JSX.Element }[]>([])
  const { searchHistory, addSearchHistory, clearSearchHistory } = useStockStore()
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const requestSeqRef = useRef(0)

  useEffect(() => {
    return () => {
      if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
    }
  }, [])

  const buildHistoryOptions = useCallback(() => {
    if (searchHistory.length === 0) return []
    return [
      {
        value: '__history_header__',
        label: (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', opacity: 0.6, fontSize: 12 }}>
            <span><Clock size={12} style={{ marginRight: 4, verticalAlign: -1 }} />最近搜索</span>
            <span
              style={{ cursor: 'pointer', color: '#ff6b4a' }}
              onClick={(e) => { e.stopPropagation(); clearSearchHistory(); setOptions([]) }}
            >
              <X size={12} style={{ verticalAlign: -1 }} /> 清除
            </span>
          </div>
        ),
      },
      ...searchHistory.map((code) => ({
        value: code,
        label: (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Clock size={13} style={{ opacity: 0.3 }} />
            <strong>{code}</strong>
          </div>
        ),
      })),
    ]
  }, [searchHistory, clearSearchHistory])

  const handleSearch = useCallback((value: string) => {
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
    const keyword = value.trim()
    if (!keyword || keyword.length < 1) {
      requestSeqRef.current += 1
      setOptions(buildHistoryOptions())
      return
    }

    const requestId = ++requestSeqRef.current
    searchTimerRef.current = setTimeout(async () => {
      searchTimerRef.current = null
      try {
        const res = await stockApi.search(keyword, 8)
        if (requestId !== requestSeqRef.current) return
        const data = Array.isArray(res) ? res : (res as any)?.data || []
        setOptions(
          data.map((stock: any) => ({
            value: stock.stock_code,
            label: (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>
                  <strong>{stock.stock_code}</strong>
                  <span style={{ marginLeft: 8, opacity: 0.7 }}>{stock.stock_name}</span>
                </span>
                <span style={{
                  color: stock.pct_change > 0 ? '#f5222d' : stock.pct_change < 0 ? '#52c41a' : '#999',
                  fontSize: 13,
                }}>
                  {stock.price?.toFixed(2)} {stock.pct_change > 0 ? '+' : ''}{stock.pct_change?.toFixed(2)}%
                </span>
              </div>
            ),
          }))
        )
      } catch {
        if (requestId !== requestSeqRef.current) return
        setOptions([])
      }
    }, 300)
  }, [buildHistoryOptions])

  const handleSelect = (stockCode: string) => {
    if (stockCode === '__history_header__') return
    addSearchHistory(stockCode)
    navigate(`/analysis/${stockCode}`)
  }

  const handleFocus = () => {
    if (options.length === 0) setOptions(buildHistoryOptions())
  }

  return (
    <AutoComplete
      options={options}
      onSearch={handleSearch}
      onSelect={handleSelect}
      onFocus={handleFocus}
      filterOption={false}
      style={{ width: '100%', maxWidth: 400 }}
    >
      <Input
        size="large"
        placeholder="输入股票代码或名称搜索..."
        prefix={<Search size={18} style={{ opacity: 0.5 }} />}
        allowClear
      />
    </AutoComplete>
  )
}
