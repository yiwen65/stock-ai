import { Progress, Tag } from 'antd'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import type { AnalysisReport } from '@/types'
import styles from './AnalysisReport.module.css'

interface AnalysisReportProps {
  report: AnalysisReport
}

export default function AnalysisReport({ report }: AnalysisReportProps) {
  const getRecommendationConfig = (rec: string) => {
    switch (rec) {
      case 'buy':
        return { color: 'success', text: '买入', icon: TrendingUp, className: styles.recBuy }
      case 'sell':
        return { color: 'error', text: '卖出', icon: TrendingDown, className: styles.recSell }
      default:
        return { color: 'default', text: '持有', icon: Minus, className: styles.recHold }
    }
  }

  const recConfig = getRecommendationConfig(report.recommendation)
  const RecIcon = recConfig.icon

  return (
    <div className={styles.container}>
      {/* Overall Score */}
      <div className={styles.overallCard}>
        <div className={styles.scoreSection}>
          <h3 className={styles.cardTitle}>综合评分</h3>
          <div className={styles.scoreDisplay}>
            <Progress
              type="circle"
              percent={report.overall_score * 10}
              format={() => (
                <div className={styles.scoreValue}>
                  <span className={styles.scoreNumber}>{report.overall_score.toFixed(1)}</span>
                  <span className={styles.scoreMax}>/10</span>
                </div>
              )}
              strokeColor={{
                '0%': '#ff6b4a',
                '100%': '#00d9c0'
              }}
              trailColor="#2a2a2a"
              strokeWidth={8}
              width={140}
            />
          </div>
        </div>

        <div className={styles.recommendationSection}>
          <h3 className={styles.cardTitle}>投资建议</h3>
          <div className={`${styles.recommendation} ${recConfig.className}`}>
            <RecIcon size={24} strokeWidth={2.5} />
            <span className={styles.recommendationText}>{recConfig.text}</span>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className={styles.summaryCard}>
        <h3 className={styles.cardTitle}>分析摘要</h3>
        <p className={styles.summaryText}>{report.summary}</p>
      </div>

      {/* Fundamental Analysis */}
      <div className={styles.analysisCard}>
        <div className={styles.cardHeader}>
          <h3 className={styles.cardTitle}>基本面分析</h3>
          <div className={styles.scoreTag}>
            评分: <strong>{report.fundamental.score.toFixed(1)}</strong>/10
          </div>
        </div>
        <p className={styles.analysisText}>{report.fundamental.summary}</p>
      </div>

      {/* Technical Analysis */}
      <div className={styles.analysisCard}>
        <div className={styles.cardHeader}>
          <h3 className={styles.cardTitle}>技术面分析</h3>
          <div className={styles.scoreTag}>
            评分: <strong>{report.technical.score.toFixed(1)}</strong>/10
          </div>
        </div>
        <div className={styles.trendBadge}>
          趋势: <span className={styles.trendValue}>{report.technical.trend}</span>
        </div>
        <p className={styles.analysisText}>{report.technical.summary}</p>
      </div>
    </div>
  )
}
