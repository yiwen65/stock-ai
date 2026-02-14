import { useState, useMemo } from 'react'
import { Table, Tag, Card, Empty, Segmented } from 'antd'
import { useNavigate } from 'react-router-dom'
import ReactECharts from 'echarts-for-react'

interface PeerItem {
  stock_code: string
  stock_name: string
  price: number
  pct_change: number
  market_cap: number
  pe: number | null
  pb: number | null
  turnover_rate: number
}

interface PeerComparisonProps {
  industry: string
  target: PeerItem | null
  peers: PeerItem[]
  loading?: boolean
}

export default function PeerComparison({ industry, target, peers, loading }: PeerComparisonProps) {
  const navigate = useNavigate()
  const [view, setView] = useState<'table' | 'scatter'>('table')

  if (loading) {
    return (
      <Card
        style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 10 }}
        loading
      />
    )
  }

  if (!peers || peers.length === 0) {
    return (
      <Card style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 10 }}>
        <Empty description="暂无同行业数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </Card>
    )
  }

  const allItems = target ? [{ ...target, _isTarget: true }, ...peers.map(p => ({ ...p, _isTarget: false }))] : peers.map(p => ({ ...p, _isTarget: false }))

  const columns = [
    {
      title: '股票',
      key: 'name',
      width: 140,
      render: (_: any, r: any) => (
        <div
          style={{ cursor: 'pointer' }}
          onClick={() => navigate(`/analysis/${r.stock_code}`)}
        >
          <div style={{ fontWeight: r._isTarget ? 700 : 400, color: r._isTarget ? '#ff6b4a' : '#e0e0e0', fontSize: 13 }}>
            {r.stock_name}
            {r._isTarget && <Tag color="volcano" style={{ marginLeft: 4, fontSize: 10, lineHeight: '16px', padding: '0 4px' }}>当前</Tag>}
          </div>
          <div style={{ fontSize: 11, color: '#666' }}>{r.stock_code}</div>
        </div>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      width: 80,
      render: (v: number) => <span style={{ fontFamily: 'IBM Plex Mono', fontSize: 13 }}>¥{v?.toFixed(2)}</span>,
    },
    {
      title: '涨跌幅',
      dataIndex: 'pct_change',
      key: 'pct_change',
      width: 80,
      render: (v: number) => (
        <span style={{ color: v > 0 ? '#f5222d' : v < 0 ? '#52c41a' : '#a0a0a0', fontFamily: 'IBM Plex Mono', fontSize: 13 }}>
          {v > 0 ? '+' : ''}{v?.toFixed(2)}%
        </span>
      ),
    },
    {
      title: '市值',
      dataIndex: 'market_cap',
      key: 'market_cap',
      width: 90,
      render: (v: number) => {
        if (!v) return '-'
        if (v >= 1e12) return `${(v / 1e12).toFixed(1)}万亿`
        if (v >= 1e8) return `${(v / 1e8).toFixed(0)}亿`
        return `${(v / 1e4).toFixed(0)}万`
      },
      sorter: (a: any, b: any) => (a.market_cap || 0) - (b.market_cap || 0),
    },
    {
      title: 'PE',
      dataIndex: 'pe',
      key: 'pe',
      width: 70,
      render: (v: number | null) => v != null ? <span style={{ fontFamily: 'IBM Plex Mono', fontSize: 13 }}>{v.toFixed(1)}</span> : '-',
      sorter: (a: any, b: any) => (a.pe || 0) - (b.pe || 0),
    },
    {
      title: 'PB',
      dataIndex: 'pb',
      key: 'pb',
      width: 70,
      render: (v: number | null) => v != null ? <span style={{ fontFamily: 'IBM Plex Mono', fontSize: 13 }}>{v.toFixed(2)}</span> : '-',
      sorter: (a: any, b: any) => (a.pb || 0) - (b.pb || 0),
    },
    {
      title: '换手率',
      dataIndex: 'turnover_rate',
      key: 'turnover_rate',
      width: 70,
      render: (v: number) => <span style={{ fontFamily: 'IBM Plex Mono', fontSize: 13 }}>{v?.toFixed(2)}%</span>,
    },
  ]

  const scatterOption = useMemo(() => {
    const valid = allItems.filter((p: any) => p.pe != null && p.pe > 0 && p.pe < 200 && p.pb != null && p.pb > 0)
    if (valid.length < 2) return null
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item' as const,
        backgroundColor: 'rgba(20,20,20,0.95)',
        borderColor: '#2a2a2a',
        textStyle: { color: '#fff', fontSize: 11 },
        formatter: (p: any) => {
          const d = p.data
          return `<b>${d[3]}</b> (${d[4]})<br/>PE: ${d[0].toFixed(1)}　PB: ${d[1].toFixed(2)}<br/>市值: ${d[2] >= 1e12 ? (d[2]/1e12).toFixed(1)+'万亿' : (d[2]/1e8).toFixed(0)+'亿'}`
        },
      },
      xAxis: {
        name: 'PE',
        type: 'value' as const,
        axisLine: { lineStyle: { color: '#2a2a2a' } },
        axisLabel: { color: '#a0a0a0', fontSize: 10 },
        splitLine: { lineStyle: { color: '#2a2a2a', type: 'dashed' as const } },
      },
      yAxis: {
        name: 'PB',
        type: 'value' as const,
        axisLine: { lineStyle: { color: '#2a2a2a' } },
        axisLabel: { color: '#a0a0a0', fontSize: 10 },
        splitLine: { lineStyle: { color: '#2a2a2a', type: 'dashed' as const } },
      },
      series: [{
        type: 'scatter' as const,
        symbolSize: (d: number[]) => Math.max(12, Math.min(40, Math.sqrt(d[2] / 1e8))),
        data: valid.map((p: any) => ({
          value: [p.pe, p.pb, p.market_cap || 0, p.stock_name, p.stock_code],
          itemStyle: { color: p._isTarget ? '#ff6b4a' : '#4fc3f7', opacity: 0.85 },
        })),
        label: {
          show: true,
          formatter: (p: any) => p.data.value[3],
          position: 'top' as const,
          color: '#a0a0a0',
          fontSize: 10,
        },
      }],
    }
  }, [allItems])

  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 10,
      padding: '16px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <h4 style={{ fontSize: 16, fontWeight: 700, color: '#fff', fontFamily: 'IBM Plex Sans', margin: 0 }}>
          同行业对比
        </h4>
        <Tag color="blue">{industry}</Tag>
        <div style={{ marginLeft: 'auto' }}>
          <Segmented
            options={[
              { label: '表格', value: 'table' },
              { label: 'PE-PB 散点图', value: 'scatter' },
            ]}
            value={view}
            onChange={(v) => setView(v as 'table' | 'scatter')}
            size="small"
          />
        </div>
      </div>

      {view === 'table' ? (
        <>
          <Table
            dataSource={allItems}
            columns={columns}
            rowKey="stock_code"
            pagination={false}
            size="small"
            rowClassName={(r: any) => r._isTarget ? 'peer-target-row' : ''}
            scroll={{ x: 600 }}
          />
          <style>{`
            .peer-target-row td { background: rgba(255,107,74,0.05) !important; }
          `}</style>
        </>
      ) : scatterOption ? (
        <ReactECharts option={scatterOption} style={{ height: 340, width: '100%' }} notMerge />
      ) : (
        <Empty description="PE/PB 数据不足，无法绘制散点图" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </div>
  )
}
