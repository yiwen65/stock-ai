import { useQuery } from '@tanstack/react-query'
import { Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import RiskDisclaimer from '@/components/RiskDisclaimer'
import PageSkeleton from '@/components/PageSkeleton'
import SectorHeatmap from '@/components/SectorHeatmap'
import MarketCapitalFlow from '@/components/MarketCapitalFlow'
import { stockApi } from '@/services/stock'
import styles from './Market.module.css'

interface MarketIndex {
  code: string
  name: string
  price: number
  change: number
  pct_change: number
  volume: number
  amount: number
}

interface Sector {
  sector_name: string
  sector_code: string
  pct_change: number
  turnover: number
  leader_stock: string
  leader_pct_change: number
}

export default function Market() {
  const { data: indicesRaw } = useQuery({
    queryKey: ['market-indices'],
    queryFn: () => stockApi.getIndices(),
    refetchInterval: 30000,
  })

  const { data, isLoading } = useQuery({
    queryKey: ['sectors'],
    queryFn: () => stockApi.getSectors(),
    refetchInterval: 60000,
  })

  const { data: capitalFlowRaw, isLoading: capitalFlowLoading } = useQuery({
    queryKey: ['market-capital-flow'],
    queryFn: () => stockApi.getMarketCapitalFlow(),
    refetchInterval: 300000,
  })
  const capitalFlow = Array.isArray(capitalFlowRaw) ? capitalFlowRaw : (capitalFlowRaw as any)?.data || []

  const indices: MarketIndex[] = Array.isArray(indicesRaw) ? indicesRaw : (indicesRaw as any)?.data || []
  const sectors: Sector[] = Array.isArray(data) ? data : (data as any)?.data || []

  const columns: ColumnsType<Sector> = [
    {
      title: '板块名称',
      dataIndex: 'sector_name',
      key: 'sector_name',
      width: 150,
      fixed: 'left',
      render: (name: string) => <strong>{name}</strong>,
    },
    {
      title: '涨跌幅',
      dataIndex: 'pct_change',
      key: 'pct_change',
      width: 120,
      align: 'right',
      sorter: (a, b) => a.pct_change - b.pct_change,
      defaultSortOrder: 'descend',
      render: (val: number) => {
        const positive = val > 0
        return (
          <span style={{ color: positive ? '#f5222d' : val < 0 ? '#52c41a' : '#999', fontWeight: 600 }}>
            {positive ? '+' : ''}{val?.toFixed(2)}%
          </span>
        )
      },
    },
    {
      title: '成交额(亿)',
      dataIndex: 'turnover',
      key: 'turnover',
      width: 120,
      align: 'right',
      sorter: (a, b) => a.turnover - b.turnover,
      render: (val: number) => val ? (val / 1e8).toFixed(2) : '-',
    },
    {
      title: '领涨股',
      dataIndex: 'leader_stock',
      key: 'leader_stock',
      width: 120,
    },
    {
      title: '领涨股涨跌幅',
      dataIndex: 'leader_pct_change',
      key: 'leader_pct_change',
      width: 120,
      align: 'right',
      render: (val: number) => {
        if (val == null) return '-'
        const positive = val > 0
        return (
          <Tag color={positive ? 'red' : val < 0 ? 'green' : 'default'}>
            {positive ? '+' : ''}{val?.toFixed(2)}%
          </Tag>
        )
      },
    },
  ]

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>市场概览</h1>
        <p className={styles.subtitle}>大盘指数与行业板块实时行情</p>
      </div>

      {/* Market Indices */}
      {indices.length > 0 && (
        <div className={styles.indexGrid}>
          {indices.map((idx) => {
            const positive = idx.pct_change > 0
            const color = positive ? '#f5222d' : idx.pct_change < 0 ? '#52c41a' : '#999'
            return (
              <div key={idx.code} className={styles.indexCard} style={{ borderTopColor: color }}>
                <div className={styles.indexName}>{idx.name}</div>
                <div className={styles.indexPrice} style={{ color }}>{idx.price.toFixed(2)}</div>
                <div className={styles.indexChange} style={{ color }}>
                  {positive ? '+' : ''}{idx.change.toFixed(2)} ({positive ? '+' : ''}{idx.pct_change.toFixed(2)}%)
                </div>
                <div className={styles.indexMeta}>
                  成交额 {idx.amount >= 1e12 ? (idx.amount / 1e12).toFixed(2) + '万亿' : (idx.amount / 1e8).toFixed(0) + '亿'}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {!isLoading && sectors.length > 0 && (
        <div style={{ marginTop: '1.5rem' }}>
          <SectorHeatmap data={sectors} />
        </div>
      )}

      {!capitalFlowLoading && capitalFlow.length > 0 && (
        <div style={{ marginTop: '1.5rem' }}>
          <MarketCapitalFlow data={capitalFlow} />
        </div>
      )}

      <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '1.5rem 0 1rem' }}>行业板块</h2>

      {isLoading ? (
        <PageSkeleton type="market" />
      ) : sectors.length > 0 ? (
        <Table
          columns={columns}
          dataSource={sectors}
          rowKey="sector_code"
          pagination={{
            pageSize: 30,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个板块`,
          }}
          scroll={{ x: 700 }}
          size="middle"
        />
      ) : (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>📈</div>
          <h3 className={styles.emptyTitle}>暂无板块数据</h3>
          <p className={styles.emptyText}>请稍后刷新页面</p>
        </div>
      )}

      <div style={{ marginTop: 24 }}>
        <RiskDisclaimer compact />
      </div>
    </div>
  )
}
