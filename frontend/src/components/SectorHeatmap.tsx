import ReactECharts from 'echarts-for-react'

interface SectorItem {
  sector_name: string
  pct_change: number
  turnover: number
}

interface SectorHeatmapProps {
  data: SectorItem[]
}

export default function SectorHeatmap({ data }: SectorHeatmapProps) {
  if (!data || data.length === 0) return null

  const treeData = data.map(s => ({
    name: s.sector_name,
    value: [Math.abs(s.turnover || 1), s.pct_change],
    pctChange: s.pct_change,
    turnover: s.turnover,
  }))

  const maxAbs = Math.max(...data.map(s => Math.abs(s.pct_change || 0)), 1)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: 'rgba(20,20,20,0.95)',
      borderColor: '#2a2a2a',
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: (params: any) => {
        const d = params.data
        const pct = d.pctChange
        const color = pct > 0 ? '#f5222d' : pct < 0 ? '#52c41a' : '#999'
        const turnover = d.turnover >= 1e8 ? (d.turnover / 1e8).toFixed(0) + '亿' : '-'
        return `<b>${d.name}</b><br/>涨跌幅: <span style="color:${color};font-weight:700">${pct > 0 ? '+' : ''}${pct?.toFixed(2)}%</span><br/>成交额: ${turnover}`
      },
    },
    series: [
      {
        type: 'treemap',
        width: '100%',
        height: '100%',
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        label: {
          show: true,
          formatter: (params: any) => {
            const pct = params.data.pctChange
            return `{name|${params.name}}\n{pct|${pct > 0 ? '+' : ''}${pct?.toFixed(2)}%}`
          },
          rich: {
            name: { fontSize: 12, color: '#fff', fontWeight: 600, lineHeight: 18 },
            pct: { fontSize: 14, fontWeight: 900, fontFamily: 'IBM Plex Mono', lineHeight: 20 },
          },
        },
        itemStyle: {
          borderColor: '#1a1a1a',
          borderWidth: 2,
          gapWidth: 2,
        },
        data: treeData,
        levels: [
          {
            itemStyle: {
              borderWidth: 0,
              gapWidth: 2,
            },
            color: treeData.map(d => {
              const pct = d.pctChange
              const ratio = Math.min(Math.abs(pct) / maxAbs, 1)
              if (pct > 0) {
                const r = Math.round(180 + 75 * ratio)
                const g = Math.round(50 - 20 * ratio)
                const b = Math.round(50 - 20 * ratio)
                return `rgb(${r},${g},${b})`
              } else if (pct < 0) {
                const r = Math.round(30 - 10 * ratio)
                const g = Math.round(140 + 60 * ratio)
                const b = Math.round(80 + 40 * ratio)
                return `rgb(${r},${g},${b})`
              }
              return '#333'
            }),
          },
        ],
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
      <h4 style={{ fontSize: 16, fontWeight: 700, color: '#fff', margin: '0 0 12px 0' }}>
        行业热力图
      </h4>
      <ReactECharts option={option} style={{ height: '400px', width: '100%' }} />
    </div>
  )
}
