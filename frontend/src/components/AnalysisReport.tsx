import { Progress, Tag, Collapse, Table } from 'antd'
import { TrendingUp, TrendingDown, Minus, Eye, AlertTriangle, BarChart3 } from 'lucide-react'
import type { AnalysisReport, IndustryComparisonMetric } from '@/types'
import styles from './AnalysisReport.module.css'

interface AnalysisReportProps {
  report: AnalysisReport
}

const recMap: Record<string, { color: string; text: string; icon: any; className: string }> = {
  buy: { color: 'success', text: '买入', icon: TrendingUp, className: 'recBuy' },
  hold: { color: 'processing', text: '持有', icon: Minus, className: 'recHold' },
  watch: { color: 'warning', text: '观望', icon: Eye, className: 'recHold' },
  sell: { color: 'error', text: '卖出', icon: TrendingDown, className: 'recSell' },
}

const riskMap: Record<string, { color: string; text: string }> = {
  low: { color: 'green', text: '低风险' },
  medium: { color: 'orange', text: '中风险' },
  high: { color: 'red', text: '高风险' },
}

function MetricItem({ label, value, suffix }: { label: string; value: number | undefined; suffix?: string }) {
  if (value == null) return null
  return (
    <div style={{ display: 'inline-block', minWidth: 100, marginRight: 20, marginBottom: 8 }}>
      <div style={{ fontSize: 12, opacity: 0.6 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 600 }}>{typeof value === 'number' ? value.toFixed(2) : value}{suffix || ''}</div>
    </div>
  )
}

function SectionHeader({ title, score }: { title: string; score: number }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
      <span style={{ fontWeight: 700, fontSize: 15 }}>{title}</span>
      <span className={styles.scoreTag} style={{ marginLeft: 'auto', marginRight: 8 }}>
        评分: <strong>{score.toFixed(1)}</strong>/10
      </span>
    </div>
  )
}

export const REPORT_SECTIONS = [
  { key: 'overview', label: '综合评分' },
  { key: 'summary', label: '分析摘要' },
  { key: 'fundamental', label: '基本面' },
  { key: 'technical', label: '技术面' },
  { key: 'capital', label: '资金面' },
  { key: 'industry', label: '行业对比' },
]

export default function AnalysisReport({ report }: AnalysisReportProps) {
  const recConfig = recMap[report.recommendation] || recMap.hold
  const RecIcon = recConfig.icon
  const riskConfig = riskMap[report.risk_level] || riskMap.medium

  const ic = report.industry_comparison

  const collapseItems = [
    {
      key: 'fundamental',
      label: <SectionHeader title="基本面分析" score={report.fundamental.score} />,
      children: (
        <>
          <div style={{ margin: '12px 0' }}>
            <MetricItem label="PE" value={report.fundamental.valuation?.pe} />
            <MetricItem label="PB" value={report.fundamental.valuation?.pb} />
            <MetricItem label="市值(亿)" value={report.fundamental.valuation?.market_cap ? report.fundamental.valuation.market_cap / 1e8 : undefined} />
            <MetricItem label="ROE" value={report.fundamental.profitability?.roe} suffix="%" />
            <MetricItem label="EPS" value={report.fundamental.profitability?.eps} />
            <MetricItem label="毛利率" value={report.fundamental.profitability?.gross_margin} suffix="%" />
            <MetricItem label="净利率" value={report.fundamental.profitability?.net_margin} suffix="%" />
            <MetricItem label="营收增长" value={report.fundamental.growth?.revenue_growth} suffix="%" />
            <MetricItem label="净利润增长" value={report.fundamental.growth?.profit_growth} suffix="%" />
            <MetricItem label="资产负债率" value={report.fundamental.financial_health?.debt_ratio} suffix="%" />
            <MetricItem label="流动比率" value={report.fundamental.financial_health?.current_ratio} />
          </div>
          {(report.fundamental.valuation?.pe_percentile != null || report.fundamental.valuation?.pb_percentile != null) && (
            <div style={{ margin: '12px 0', padding: '12px 16px', background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 10, opacity: 0.8 }}>估值历史分位</div>
              {report.fundamental.valuation?.pe_percentile != null && (
                <div style={{ marginBottom: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                    <span style={{ opacity: 0.6 }}>PE 历史分位</span>
                    <span style={{ fontWeight: 700, fontFamily: 'IBM Plex Mono', color: report.fundamental.valuation.pe_percentile > 70 ? '#f5222d' : report.fundamental.valuation.pe_percentile < 30 ? '#52c41a' : '#faad14' }}>
                      {report.fundamental.valuation.pe_percentile.toFixed(1)}%
                    </span>
                  </div>
                  <Progress
                    percent={report.fundamental.valuation.pe_percentile}
                    showInfo={false}
                    strokeColor={report.fundamental.valuation.pe_percentile > 70 ? '#f5222d' : report.fundamental.valuation.pe_percentile < 30 ? '#52c41a' : '#faad14'}
                    trailColor="#2a2a2a"
                    size="small"
                  />
                </div>
              )}
              {report.fundamental.valuation?.pb_percentile != null && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                    <span style={{ opacity: 0.6 }}>PB 历史分位</span>
                    <span style={{ fontWeight: 700, fontFamily: 'IBM Plex Mono', color: report.fundamental.valuation.pb_percentile > 70 ? '#f5222d' : report.fundamental.valuation.pb_percentile < 30 ? '#52c41a' : '#faad14' }}>
                      {report.fundamental.valuation.pb_percentile.toFixed(1)}%
                    </span>
                  </div>
                  <Progress
                    percent={report.fundamental.valuation.pb_percentile}
                    showInfo={false}
                    strokeColor={report.fundamental.valuation.pb_percentile > 70 ? '#f5222d' : report.fundamental.valuation.pb_percentile < 30 ? '#52c41a' : '#faad14'}
                    trailColor="#2a2a2a"
                    size="small"
                  />
                </div>
              )}
              <div style={{ fontSize: 11, opacity: 0.5, marginTop: 6 }}>
                低于30%: 估值偏低 | 高于70%: 估值偏高 (基于近250个交易日)
              </div>
            </div>
          )}
          <p className={styles.analysisText}>{report.fundamental.summary}</p>
        </>
      ),
    },
    {
      key: 'technical',
      label: <SectionHeader title="技术面分析" score={report.technical.score} />,
      children: (
        <>
          <div className={styles.trendBadge}>
            趋势: <span className={styles.trendValue}>{report.technical.trend}</span>
          </div>
          <div style={{ margin: '12px 0' }}>
            <MetricItem label="MA5" value={report.technical.indicators?.ma5} />
            <MetricItem label="MA10" value={report.technical.indicators?.ma10} />
            <MetricItem label="MA20" value={report.technical.indicators?.ma20} />
            <MetricItem label="MA60" value={report.technical.indicators?.ma60} />
            <MetricItem label="RSI(14)" value={report.technical.indicators?.rsi14} />
            <MetricItem label="KDJ-K" value={report.technical.indicators?.kdj_k} />
            <MetricItem label="KDJ-D" value={report.technical.indicators?.kdj_d} />
            <MetricItem label="MACD DIF" value={report.technical.indicators?.macd_dif} />
            <MetricItem label="MACD DEA" value={report.technical.indicators?.macd_dea} />
          </div>
          {report.technical.support_levels?.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ opacity: 0.6, marginRight: 8 }}>支撑位:</span>
              {report.technical.support_levels.map((l, i) => (
                <Tag key={i} color="green">¥{l.toFixed(2)}</Tag>
              ))}
            </div>
          )}
          {report.technical.resistance_levels?.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ opacity: 0.6, marginRight: 8 }}>压力位:</span>
              {report.technical.resistance_levels.map((l, i) => (
                <Tag key={i} color="red">¥{l.toFixed(2)}</Tag>
              ))}
            </div>
          )}
          <p className={styles.analysisText}>{report.technical.summary}</p>
        </>
      ),
    },
    {
      key: 'capital',
      label: <SectionHeader title="资金面分析" score={report.capital_flow.score} />,
      children: (
        <>
          <div style={{ margin: '12px 0' }}>
            <div style={{ marginBottom: 8 }}>
              <span style={{ opacity: 0.6, marginRight: 8 }}>资金趋势:</span>
              <Tag color={report.capital_flow.trend.includes('流入') ? 'green' : report.capital_flow.trend.includes('流出') ? 'red' : 'default'}>
                {report.capital_flow.trend}
              </Tag>
            </div>
            <MetricItem
              label="主力净流入"
              value={report.capital_flow.main_net_inflow ? (Math.abs(report.capital_flow.main_net_inflow) >= 1e8 ? report.capital_flow.main_net_inflow / 1e8 : report.capital_flow.main_net_inflow / 1e4) : 0}
              suffix={Math.abs(report.capital_flow.main_net_inflow ?? 0) >= 1e8 ? '亿' : '万'}
            />
            <MetricItem
              label="主力占比"
              value={report.capital_flow.main_inflow_ratio ? report.capital_flow.main_inflow_ratio * 100 : 0}
              suffix="%"
            />
          </div>
          <p className={styles.analysisText}>{report.capital_flow.summary}</p>
        </>
      ),
    },
  ]

  // Industry comparison section
  if (ic && ic.target) {
    const peerColumns = [
      { title: '股票', dataIndex: 'stock_name', key: 'stock_name', width: 90 },
      { title: 'PE', dataIndex: 'pe', key: 'pe', render: (v: number | null) => v != null ? v.toFixed(1) : '-' },
      { title: 'PB', dataIndex: 'pb', key: 'pb', render: (v: number | null) => v != null ? v.toFixed(2) : '-' },
      { title: 'ROE', dataIndex: 'roe', key: 'roe', render: (v: number | null) => v != null ? `${v.toFixed(1)}%` : '-' },
      { title: '涨跌幅', dataIndex: 'pct_change', key: 'pct_change', render: (v: number) => (
        <span style={{ color: v > 0 ? '#f5222d' : v < 0 ? '#52c41a' : undefined }}>{v?.toFixed(2)}%</span>
      )},
    ]

    const tableData = [{ ...ic.target, _isTarget: true }, ...ic.peers].map((item, i) => ({ ...item, key: item.stock_code || i }))

    collapseItems.push({
      key: 'industry',
      label: (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <span style={{ fontWeight: 700, fontSize: 15 }}>
            <BarChart3 size={14} style={{ marginRight: 6, verticalAlign: -2 }} />
            同行业对比 · {ic.industry}
          </span>
        </div>
      ),
      children: (
        <>
          <p style={{ fontSize: 13, opacity: 0.8, marginBottom: 12 }}>{ic.industry_position}</p>

          {ic.comparison_metrics.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              {ic.comparison_metrics.map((m: IndustryComparisonMetric) => (
                <div key={m.metric} style={{ display: 'flex', alignItems: 'center', marginBottom: 8, fontSize: 13 }}>
                  <span style={{ width: 100, opacity: 0.6 }}>{m.label}</span>
                  <span style={{ width: 70, fontWeight: 600, fontFamily: 'IBM Plex Mono' }}>{m.target_value}</span>
                  <Tag color={m.vs_avg === '高于平均' ? 'green' : m.vs_avg === '低于平均' ? 'red' : 'default'} style={{ fontSize: 11 }}>
                    {m.vs_avg}
                  </Tag>
                  <span style={{ opacity: 0.5, fontSize: 12, marginLeft: 8 }}>
                    排名 {m.rank}/{m.total} | 行业均值 {m.industry_avg}
                  </span>
                </div>
              ))}
            </div>
          )}

          <Table
            columns={peerColumns}
            dataSource={tableData}
            pagination={false}
            size="small"
            rowClassName={(record: any) => record._isTarget ? styles.targetRow || '' : ''}
            style={{ marginTop: 8 }}
          />
        </>
      ),
    })
  }

  return (
    <div className={styles.container}>
      {/* Overall Score + Recommendation + Risk */}
      <div id="section-overview" className={styles.overallCard}>
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
          <div className={`${styles.recommendation} ${styles[recConfig.className] || ''}`}>
            <RecIcon size={24} strokeWidth={2.5} />
            <span className={styles.recommendationText}>{recConfig.text}</span>
          </div>
          <div style={{ marginTop: 12 }}>
            <Tag color={riskConfig.color} style={{ fontSize: 14, padding: '4px 12px' }}>
              <AlertTriangle size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
              {riskConfig.text}
            </Tag>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div id="section-summary" className={styles.summaryCard}>
        <h3 className={styles.cardTitle}>分析摘要</h3>
        <p className={styles.summaryText}>{report.summary}</p>
      </div>

      {/* Collapsible Analysis Sections */}
      <Collapse
        defaultActiveKey={['fundamental', 'technical', 'capital']}
        ghost
        items={collapseItems.map(item => ({
          ...item,
          id: `section-${item.key}`,
          className: styles.analysisCard,
          style: { marginBottom: 0 },
        }))}
      />

      {/* Disclaimer */}
      <div style={{ marginTop: 16, padding: '12px 16px', background: 'rgba(255,165,0,0.08)', borderRadius: 8, border: '1px solid rgba(255,165,0,0.2)' }}>
        <p style={{ margin: 0, fontSize: 12, opacity: 0.7 }}>
          ⚠️ 风险提示：以上分析基于历史数据和算法模型生成，仅供参考，不构成任何投资建议。
          股市有风险，投资需谨慎。数据来源于公开市场信息，不保证数据的完整性和准确性。
        </p>
      </div>
    </div>
  )
}
