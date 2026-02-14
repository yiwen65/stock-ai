import { useState } from 'react'
import { message } from 'antd'
import { useQuery } from '@tanstack/react-query'
import StrategyForm from '@/components/StrategyForm'
import StockTable from '@/components/StockTable'
import RiskDisclaimer from '@/components/RiskDisclaimer'
import { strategyApi } from '@/services/strategy'
import styles from './StockPicker.module.css'

export default function StockPicker() {
  const [params, setParams] = useState<any>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['stocks', params],
    queryFn: () => strategyApi.execute(params),
    enabled: !!params
  })

  const handleSubmit = async (values: any) => {
    try {
      setParams(values)
    } catch (err: any) {
      message.error(err.message || '执行选股失败')
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>选股中心</h1>
        <p className={styles.subtitle}>涵盖价值投资、成长策略、技术分析、事件驱动等多维度智能选股</p>
      </div>

      <div className={styles.formSection}>
        <StrategyForm onSubmit={handleSubmit} loading={isLoading} />
      </div>

      {error && (
        <div style={{ padding: '16px', color: '#ff4d4f', textAlign: 'center' }}>
          选股执行失败，请稍后重试
        </div>
      )}

      {params && (
        <div className={styles.resultsSection}>
          <div className={styles.resultsHeader}>
            <h2 className={styles.resultsTitle}>选股结果</h2>
            {Array.isArray(data) && data.length > 0 && (
              <span className={styles.resultCount}>
                找到 <strong>{data.length}</strong> 只股票
              </span>
            )}
          </div>
          <StockTable data={Array.isArray(data) ? data : []} loading={isLoading} />
        </div>
      )}

      {!params && (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>📊</div>
          <h3 className={styles.emptyTitle}>选择策略开始选股</h3>
          <p className={styles.emptyText}>
            选择一个投资策略，系统将为您筛选符合条件的优质股票
          </p>
        </div>
      )}

      <div style={{ marginTop: 24 }}>
        <RiskDisclaimer compact />
      </div>
    </div>
  )
}
