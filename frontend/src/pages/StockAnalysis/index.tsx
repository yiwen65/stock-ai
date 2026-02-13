import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Spin, Button, message } from 'antd'
import { ArrowLeft, RefreshCw } from 'lucide-react'
import KLineChart from '@/components/KLineChart'
import AnalysisReport from '@/components/AnalysisReport'
import { analysisApi } from '@/services/analysis'
import styles from './StockAnalysis.module.css'

export default function StockAnalysis() {
  const { code } = useParams<{ code: string }>()
  const navigate = useNavigate()

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['analysis', code],
    queryFn: () => analysisApi.analyze(code!),
    enabled: !!code
  })

  const { data: klineData, isLoading: klineLoading } = useQuery({
    queryKey: ['kline', code],
    queryFn: () => analysisApi.getKLine(code!, { period: 'daily', adjust: 'qfq' }),
    enabled: !!code
  })

  if (isLoading || klineLoading) {
    return (
      <div className={styles.loading}>
        <Spin size="large" />
        <p className={styles.loadingText}>正在分析股票数据...</p>
      </div>
    )
  }

  if (error || !data?.data) {
    return (
      <div className={styles.error}>
        <h2 className={styles.errorTitle}>加载失败</h2>
        <p className={styles.errorText}>无法加载股票分析数据，请稍后重试</p>
        <Button onClick={() => navigate('/')}>返回选股中心</Button>
      </div>
    )
  }

  const report = data.data

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Button
          icon={<ArrowLeft size={18} />}
          onClick={() => navigate(-1)}
          className={styles.backButton}
        >
          返回
        </Button>
        <div className={styles.stockInfo}>
          <h1 className={styles.stockName}>{report.stock_name}</h1>
          <span className={styles.stockCode}>{report.stock_code}</span>
        </div>
        <Button
          icon={<RefreshCw size={18} />}
          onClick={() => refetch()}
          className={styles.refreshButton}
        >
          刷新分析
        </Button>
      </div>

      <div className={styles.content}>
        {klineData?.data && klineData.data.length > 0 && (
          <div className={styles.chartSection}>
            <KLineChart data={klineData.data} title={`${report.stock_name} K线图`} />
          </div>
        )}

        <div className={styles.reportSection}>
          <AnalysisReport report={report} />
        </div>
      </div>
    </div>
  )
}
