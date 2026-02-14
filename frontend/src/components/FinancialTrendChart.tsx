import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { Segmented } from 'antd'
import type { FinancialItem } from '@/types'

interface FinancialTrendChartProps {
  data: FinancialItem[]
}

type ChartMode = 'profitability' | 'growth'

const AXIS_STYLE = {
  axisLine: { lineStyle: { color: '#2a2a2a' } },
  axisLabel: { color: '#a0a0a0', fontFamily: 'IBM Plex Mono', fontSize: 11 },
}
const SPLIT = { splitLine: { lineStyle: { color: '#2a2a2a', type: 'dashed' as const } } }
const TOOLTIP = {
  trigger: 'axis' as const,
  backgroundColor: 'rgba(20,20,20,0.95)',
  borderColor: '#2a2a2a',
  textStyle: { color: '#fff', fontFamily: 'IBM Plex Mono', fontSize: 11 },
}

function buildProfitabilityOption(dates: string[], items: FinancialItem[]) {
  return {
    backgroundColor: 'transparent',
    tooltip: TOOLTIP,
    legend: {
      data: ['ROE', '毛利率', '净利率'],
      top: 0, right: 0,
      textStyle: { color: '#a0a0a0', fontSize: 11, fontFamily: 'IBM Plex Mono' },
      itemWidth: 14, itemHeight: 2,
    },
    grid: { left: '3%', right: '3%', top: '12%', bottom: '8%', containLabel: true },
    xAxis: { type: 'category', data: dates, ...AXIS_STYLE },
    yAxis: {
      type: 'value', ...SPLIT, ...AXIS_STYLE,
      axisLabel: {
        ...AXIS_STYLE.axisLabel,
        formatter: (v: number) => v.toFixed(0) + '%',
      },
    },
    series: [
      {
        name: 'ROE', type: 'line', data: items.map(d => d.roe),
        smooth: true, symbol: 'circle', symbolSize: 6,
        lineStyle: { width: 2 }, itemStyle: { color: '#ff6b4a' },
      },
      {
        name: '毛利率', type: 'line', data: items.map(d => d.gross_margin),
        smooth: true, symbol: 'circle', symbolSize: 6,
        lineStyle: { width: 2 }, itemStyle: { color: '#00d9c0' },
      },
      {
        name: '净利率', type: 'line', data: items.map(d => d.net_margin),
        smooth: true, symbol: 'circle', symbolSize: 6,
        lineStyle: { width: 2 }, itemStyle: { color: '#4fc3f7' },
      },
    ],
  }
}

function buildGrowthOption(dates: string[], items: FinancialItem[]) {
  const revAmounts = items.map(d => (d.revenue ?? 0) / 1e8)
  const profitAmounts = items.map(d => (d.net_profit ?? 0) / 1e8)
  const revGrowth = items.map(d => d.revenue_growth)
  const profitGrowth = items.map(d => d.net_profit_growth)

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis' as const,
      axisPointer: { type: 'shadow' as const },
      backgroundColor: 'rgba(20,20,20,0.95)',
      borderColor: '#2a2a2a',
      textStyle: { color: '#fff', fontFamily: 'IBM Plex Mono', fontSize: 11 },
      formatter: (params: any) => {
        const ps = Array.isArray(params) ? params : [params]
        const idx = ps[0]?.dataIndex ?? 0
        let html = `<div style="margin-bottom:4px;font-weight:600">${ps[0]?.axisValue}</div>`
        ps.forEach((p: any) => {
          html += `<div>${p.marker} ${p.seriesName} <b>${p.value?.toFixed(2)}亿</b></div>`
        })
        const rg = revGrowth[idx], pg = profitGrowth[idx]
        html += `<div style="margin-top:4px;opacity:0.6;border-top:1px solid #333;padding-top:4px">`
        html += `营收同比 ${rg != null ? rg.toFixed(1) + '%' : '-'} ｜ 净利润同比 ${pg != null ? pg.toFixed(1) + '%' : '-'}`
        html += `</div>`
        return html
      },
    },
    legend: {
      data: ['营业收入', '净利润'],
      top: 0, right: 0,
      textStyle: { color: '#a0a0a0', fontSize: 11, fontFamily: 'IBM Plex Mono' },
      itemWidth: 14, itemHeight: 2,
    },
    grid: { left: '3%', right: '3%', top: '14%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category' as const, data: dates, ...AXIS_STYLE },
    yAxis: {
      type: 'value' as const, ...SPLIT, ...AXIS_STYLE,
      axisLabel: {
        ...AXIS_STYLE.axisLabel,
        formatter: (v: number) => v.toFixed(0) + '亿',
      },
    },
    series: [
      {
        name: '营业收入', type: 'bar' as const,
        data: revAmounts,
        barWidth: '35%',
        itemStyle: { color: '#00d9c0', borderRadius: [4, 4, 0, 0] },
      },
      {
        name: '净利润', type: 'bar' as const,
        data: profitAmounts.map(v => ({
          value: v,
          itemStyle: {
            color: v >= 0 ? '#4fc3f7' : '#f5222d',
            borderRadius: v >= 0 ? [4, 4, 0, 0] : [0, 0, 4, 4],
          },
        })),
        barWidth: '35%',
      },
    ],
  }
}

export default function FinancialTrendChart({ data }: FinancialTrendChartProps) {
  const [mode, setMode] = useState<ChartMode>('profitability')

  const sorted = useMemo(() => [...data], [data])
  const dates = useMemo(() => sorted.map(d => d.report_date.slice(0, 7)), [sorted])

  const option = useMemo(() => {
    if (mode === 'profitability') return buildProfitabilityOption(dates, sorted)
    return buildGrowthOption(dates, sorted)
  }, [mode, dates, sorted])

  if (data.length === 0) return null

  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <h3 style={{ fontSize: 18, fontWeight: 700, color: '#fff', fontFamily: 'IBM Plex Sans', margin: 0 }}>
          财务趋势
        </h3>
        <Segmented
          options={[
            { label: '盈利能力', value: 'profitability' },
            { label: '成长趋势', value: 'growth' },
          ]}
          value={mode}
          onChange={(val) => setMode(val as ChartMode)}
          size="small"
        />
      </div>
      <ReactECharts key={mode} option={option} style={{ height: '320px', width: '100%' }} notMerge />
    </div>
  )
}
