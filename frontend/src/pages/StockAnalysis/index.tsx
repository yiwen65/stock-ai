import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Spin, Button } from 'antd'
import { ArrowLeft, RefreshCw, Database, BarChart3, TrendingUp, DollarSign, CheckCircle } from 'lucide-react'
import KLineChart from '@/components/KLineChart'
import TechIndicatorChart from '@/components/TechIndicatorChart'
import FinancialRadar from '@/components/FinancialRadar'
import CapitalFlowChart from '@/components/CapitalFlowChart'
import AnalysisReport, { REPORT_SECTIONS } from '@/components/AnalysisReport'
import AnchorNav from '@/components/AnchorNav'
import DuPontChart from '@/components/DuPontChart'
import FinancialTrendChart from '@/components/FinancialTrendChart'
import NewsPanel from '@/components/NewsPanel'
import PeerComparison from '@/components/PeerComparison'
import { analysisApi } from '@/services/analysis'
import styles from './StockAnalysis.module.css'

const ANALYSIS_STEPS = [
  { icon: Database, label: '获取股票数据', duration: 2000 },
  { icon: BarChart3, label: '基本面分析', duration: 3000 },
  { icon: TrendingUp, label: '技术面分析', duration: 3000 },
  { icon: DollarSign, label: '资金面 + 消息面分析', duration: 4000 },
  { icon: CheckCircle, label: '生成综合评估', duration: 3000 },
]

function AnalysisProgress() {
  const [step, setStep] = useState(0)

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = []
    let cumulative = 0
    ANALYSIS_STEPS.forEach((s, i) => {
      cumulative += s.duration
      timers.push(setTimeout(() => setStep(i + 1), cumulative))
    })
    return () => timers.forEach(clearTimeout)
  }, [])

  return (
    <div className={styles.loading}>
      <Spin size="large" />
      <p className={styles.loadingText}>正在进行 AI 深度分析...</p>
      <div className={styles.progressSteps}>
        {ANALYSIS_STEPS.map((s, i) => {
          const Icon = s.icon
          const done = step > i
          const active = step === i
          return (
            <div
              key={i}
              className={`${styles.progressStep} ${done ? styles.stepDone : ''} ${active ? styles.stepActive : ''}`}
            >
              <Icon size={16} />
              <span>{s.label}</span>
              {done && <span className={styles.stepCheck}>✓</span>}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function StockAnalysis() {
  const { code } = useParams<{ code: string }>()
  const navigate = useNavigate()

  const [refreshKey, setRefreshKey] = useState(0)

  const { data, isLoading, error } = useQuery({
    queryKey: ['analysis', code, refreshKey],
    queryFn: () => analysisApi.analyze(code!, refreshKey > 0),
    enabled: !!code,
    retry: 2,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 5000),
  })

  const [klinePeriod, setKlinePeriod] = useState<'1d' | '1w' | '1M'>('1d')

  const { data: klineData } = useQuery({
    queryKey: ['kline', code, klinePeriod],
    queryFn: () => analysisApi.getKLine(code!, { period: klinePeriod }),
    enabled: !!code
  })

  const { data: financialData } = useQuery({
    queryKey: ['financial', code],
    queryFn: () => analysisApi.getFinancial(code!),
    enabled: !!code
  })

  const { data: newsData, isLoading: newsLoading } = useQuery({
    queryKey: ['news', code],
    queryFn: () => analysisApi.getNews(code!, 10),
    enabled: !!code
  })

  const { data: peersData, isLoading: peersLoading } = useQuery({
    queryKey: ['peers', code],
    queryFn: () => analysisApi.getPeers(code!, 6),
    enabled: !!code
  })

  if (isLoading) {
    return <AnalysisProgress />
  }

  if (error || !data) {
    return (
      <div className={styles.error}>
        <h2 className={styles.errorTitle}>加载失败</h2>
        <p className={styles.errorText}>无法加载股票分析数据，请稍后重试</p>
        <Button onClick={() => navigate('/')}>返回选股中心</Button>
      </div>
    )
  }

  const report = (data as any)?.data ?? data

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
          onClick={() => setRefreshKey(k => k + 1)}
          loading={isLoading && refreshKey > 0}
          className={styles.refreshButton}
        >
          刷新分析
        </Button>
      </div>

      {/* Key Metrics Bar */}
      <div className={styles.metricsBar}>
        <div className={styles.metricItem}>
          <span className={styles.metricLabel}>AI评分</span>
          <span className={styles.metricValue} style={{ color: 'var(--color-primary)' }}>
            {report.overall_score.toFixed(1)}<small>/10</small>
          </span>
        </div>
        <div className={styles.metricItem}>
          <span className={styles.metricLabel}>建议</span>
          <span className={styles.metricValue} style={{
            color: report.recommendation === 'buy' ? '#52c41a'
              : report.recommendation === 'sell' ? '#f5222d' : '#faad14'
          }}>
            {{ buy: '买入', hold: '持有', watch: '观望', sell: '卖出' }[report.recommendation] || report.recommendation}
          </span>
        </div>
        <div className={styles.metricItem}>
          <span className={styles.metricLabel}>风险</span>
          <span className={styles.metricValue} style={{
            color: report.risk_level === 'low' ? '#52c41a'
              : report.risk_level === 'high' ? '#f5222d' : '#faad14'
          }}>
            {{ low: '低', medium: '中', high: '高' }[report.risk_level] || report.risk_level}
          </span>
        </div>
        {report.confidence && (
          <div className={styles.metricItem}>
            <span className={styles.metricLabel}>置信度</span>
            <span className={styles.metricValue} style={{
              color: report.confidence === 'high' ? '#52c41a'
                : report.confidence === 'low' ? '#f5222d' : '#faad14'
            }}>
              {{ high: '高', medium: '中', low: '低' }[report.confidence] || report.confidence}
            </span>
          </div>
        )}
        {report.fundamental?.valuation?.pe != null && (
          <div className={styles.metricItem}>
            <span className={styles.metricLabel}>PE</span>
            <span className={styles.metricValue}>{report.fundamental.valuation.pe.toFixed(1)}</span>
          </div>
        )}
        {report.fundamental?.valuation?.pb != null && (
          <div className={styles.metricItem}>
            <span className={styles.metricLabel}>PB</span>
            <span className={styles.metricValue}>{report.fundamental.valuation.pb.toFixed(2)}</span>
          </div>
        )}
        {report.fundamental?.profitability?.roe != null && (
          <div className={styles.metricItem}>
            <span className={styles.metricLabel}>ROE</span>
            <span className={styles.metricValue}>{report.fundamental.profitability.roe.toFixed(1)}%</span>
          </div>
        )}
        <div className={styles.metricItem}>
          <span className={styles.metricLabel}>基本面</span>
          <span className={styles.metricValue}>{report.fundamental?.score?.toFixed(1)}</span>
        </div>
        <div className={styles.metricItem}>
          <span className={styles.metricLabel}>技术面</span>
          <span className={styles.metricValue}>{report.technical?.score?.toFixed(1)}</span>
        </div>
      </div>

      <AnchorNav items={REPORT_SECTIONS} />

      <div className={styles.content}>
        {(() => { const kline = Array.isArray(klineData) ? klineData : (klineData as any)?.data || []; return kline.length > 0 ? (
          <div className={styles.chartSection}>
            <KLineChart
              data={kline}
              title={`${report.stock_name} K线图`}
              period={klinePeriod}
              onPeriodChange={setKlinePeriod}
            />
          </div>
        ) : null })()}

        {(() => { const kline = Array.isArray(klineData) ? klineData : (klineData as any)?.data || []; return kline.length > 30 ? (
          <div className={styles.chartSection}>
            <TechIndicatorChart data={kline} />
          </div>
        ) : null })()}

        {(() => { const fin = Array.isArray(financialData) ? financialData : (financialData as any)?.data || []; return fin.length > 0 ? (
          <div className={styles.chartSection}>
            <FinancialTrendChart data={fin} />
          </div>
        ) : null })()}

        {peersData && (
          <div className={styles.chartSection}>
            <PeerComparison
              industry={(peersData as any)?.industry || (peersData as any)?.data?.industry || ''}
              target={(peersData as any)?.target || (peersData as any)?.data?.target}
              peers={(peersData as any)?.peers || (peersData as any)?.data?.peers || []}
              loading={peersLoading}
            />
          </div>
        )}

        <div className={styles.reportGrid}>
          <div className={styles.reportSection}>
            <AnalysisReport report={report} />
          </div>
          <div className={styles.radarSection}>
            <FinancialRadar report={report} />
            <div style={{ marginTop: 16, borderTop: '1px solid var(--color-border)', paddingTop: 16 }}>
              <CapitalFlowChart report={report} />
            </div>
            {report.fundamental?.dupont && (
              <div style={{ marginTop: 16, borderTop: '1px solid var(--color-border)', paddingTop: 16 }}>
                <DuPontChart data={report.fundamental.dupont} />
              </div>
            )}
            <div style={{ marginTop: 16, borderTop: '1px solid var(--color-border)', paddingTop: 16 }}>
              <NewsPanel
                news={Array.isArray(newsData) ? newsData : (newsData as any)?.data ?? []}
                loading={newsLoading}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
