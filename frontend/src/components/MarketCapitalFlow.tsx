import ReactECharts from 'echarts-for-react'
import { Empty } from 'antd'

interface CapitalFlowItem {
  sector_name: string
  main_net_inflow: number
  main_net_inflow_pct: number
  pct_change: number
}

interface MarketCapitalFlowProps {
  data: CapitalFlowItem[]
  loading?: boolean
}

function formatAmount(val: number): string {
  if (Math.abs(val) >= 1e8) return (val / 1e8).toFixed(2) + '亿'
  if (Math.abs(val) >= 1e4) return (val / 1e4).toFixed(0) + '万'
  return val.toFixed(0)
}

export default function MarketCapitalFlow({ data, loading }: MarketCapitalFlowProps) {
  if (loading) return null
  if (!data || data.length === 0) {
    return (
      <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 10, padding: 16 }}>
        <Empty description="暂无资金流向数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </div>
    )
  }

  const sorted = [...data].sort((a, b) => b.main_net_inflow - a.main_net_inflow)
  const top10 = sorted.slice(0, 10)
  const bottom10 = sorted.slice(-10).reverse()
  const chartData = [...top10, ...bottom10]

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(20,20,20,0.95)',
      borderColor: '#2a2a2a',
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: (params: any) => {
        const p = params[0]
        const val = p.value
        return `<b>${p.name}</b><br/>主力净流入: <span style="color:${val > 0 ? '#f5222d' : '#52c41a'};font-weight:700">${formatAmount(val)}</span>`
      },
    },
    grid: { left: 100, right: 40, top: 10, bottom: 10 },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: '#888',
        fontSize: 11,
        formatter: (v: number) => formatAmount(v),
      },
      splitLine: { lineStyle: { color: '#2a2a2a' } },
    },
    yAxis: {
      type: 'category',
      data: chartData.map(d => d.sector_name),
      axisLabel: { color: '#ccc', fontSize: 12 },
      axisLine: { show: false },
      axisTick: { show: false },
      inverse: true,
    },
    series: [
      {
        type: 'bar',
        data: chartData.map(d => ({
          value: d.main_net_inflow,
          itemStyle: {
            color: d.main_net_inflow > 0 ? '#c0392b' : '#27ae60',
            borderRadius: d.main_net_inflow > 0 ? [0, 4, 4, 0] : [4, 0, 0, 4],
          },
        })),
        barWidth: 16,
        label: {
          show: true,
          position: 'right',
          color: '#aaa',
          fontSize: 11,
          formatter: (p: any) => formatAmount(p.value),
        },
      },
    ],
  }

  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 10,
      padding: '16px',
    }}>
      <h4 style={{ fontSize: 16, fontWeight: 700, color: '#fff', margin: '0 0 8px 0' }}>
        行业资金流向 TOP10
      </h4>
      <ReactECharts option={option} style={{ height: `${Math.max(chartData.length * 28, 300)}px`, width: '100%' }} />
    </div>
  )
}
