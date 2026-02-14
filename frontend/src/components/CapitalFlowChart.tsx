import { useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { Segmented } from 'antd'
import type { AnalysisReport } from '@/types'

interface CapitalFlowChartProps {
  report: AnalysisReport
}

function fmt(val: number) {
  const a = Math.abs(val)
  if (a >= 1e8) return (val / 1e8).toFixed(2) + '亿'
  if (a >= 1e4) return (val / 1e4).toFixed(0) + '万'
  return val.toFixed(0)
}

const valColor = (v: number) => v > 0 ? '#f5222d' : v < 0 ? '#52c41a' : '#a0a0a0'

type FlowView = 'timeframe' | 'breakdown'

export default function CapitalFlowChart({ report }: CapitalFlowChartProps) {
  const cf = report.capital_flow
  const [view, setView] = useState<FlowView>('timeframe')
  if (!cf) return null

  const a = cf as any
  const ratio = cf.main_inflow_ratio ?? 0
  const score = cf.score ?? 5
  const today = cf.main_net_inflow ?? 0

  const AXIS = {
    axisLine: { lineStyle: { color: '#2a2a2a' } },
    axisLabel: { color: '#a0a0a0', fontFamily: 'IBM Plex Mono', fontSize: 10 },
  }
  const yAxis = {
    ...AXIS, type: 'value' as const,
    splitLine: { lineStyle: { color: '#2a2a2a', type: 'dashed' as const } },
    axisLabel: {
      ...AXIS.axisLabel,
      formatter: (v: number) => {
        const abs = Math.abs(v)
        return abs >= 1e8 ? (v / 1e8).toFixed(0) + '亿' : abs >= 1e4 ? (v / 1e4).toFixed(0) + '万' : v.toString()
      },
    },
  }
  const tooltipBase = {
    trigger: 'axis' as const,
    axisPointer: { type: 'shadow' as const },
    backgroundColor: 'rgba(20,20,20,0.95)', borderColor: '#2a2a2a',
    textStyle: { color: '#fff', fontFamily: 'IBM Plex Mono', fontSize: 11 },
  }

  // ── Data ──
  const superLarge = [a.super_large_net_inflow ?? 0, a.super_large_net_inflow_5d ?? 0, a.super_large_net_inflow_10d ?? 0]
  const large = [a.large_net_inflow ?? 0, a.large_net_inflow_5d ?? 0, a.large_net_inflow_10d ?? 0]
  const main = [cf.main_net_inflow ?? 0, a.main_net_inflow_5d ?? 0, a.main_net_inflow_10d ?? 0]
  const periods = ['今日', '近5日', '近10日']

  let option: any

  if (view === 'timeframe') {
    const mkSeries = (name: string, data: number[], color: string) => ({
      name, type: 'bar' as const, barWidth: '22%',
      data: data.map(v => ({
        value: v,
        itemStyle: { color: v >= 0 ? color : '#52c41a', borderRadius: v >= 0 ? [3, 3, 0, 0] : [0, 0, 3, 3] },
      })),
    })
    option = {
      backgroundColor: 'transparent',
      tooltip: {
        ...tooltipBase,
        formatter: (params: any) => {
          const ps = Array.isArray(params) ? params : [params]
          let html = `<div style="font-weight:600;margin-bottom:4px">${ps[0]?.name}</div>`
          ps.forEach((p: any) => { html += `<div>${p.marker} ${p.seriesName}: <b>${fmt(p.value)}</b></div>` })
          return html
        },
      },
      legend: {
        data: ['超大单', '大单', '主力合计'], top: 0, right: 0,
        textStyle: { color: '#a0a0a0', fontSize: 11, fontFamily: 'IBM Plex Mono' },
        itemWidth: 14, itemHeight: 2,
      },
      grid: { left: '3%', right: '3%', top: '14%', bottom: '8%', containLabel: true },
      xAxis: { type: 'category' as const, data: periods, ...AXIS, axisLabel: { ...AXIS.axisLabel, fontSize: 12 } },
      yAxis,
      series: [
        mkSeries('超大单', superLarge, '#ff4d4f'),
        mkSeries('大单', large, '#ff7a45'),
        mkSeries('主力合计', main, '#faad14'),
      ],
    }
  } else {
    const cats = ['超大单', '大单', '中单', '小单']
    const vals = [a.super_large_net_inflow ?? 0, a.large_net_inflow ?? 0, a.medium_net_inflow ?? 0, a.small_net_inflow ?? 0]
    option = {
      backgroundColor: 'transparent',
      tooltip: tooltipBase,
      grid: { left: '3%', right: '3%', top: '8%', bottom: '8%', containLabel: true },
      xAxis: { type: 'category' as const, data: cats, ...AXIS, axisLabel: { ...AXIS.axisLabel, fontSize: 12 } },
      yAxis,
      series: [{
        type: 'bar', barWidth: '45%',
        data: vals.map(v => ({
          value: v,
          itemStyle: { color: v >= 0 ? '#f5222d' : '#52c41a', borderRadius: v >= 0 ? [4, 4, 0, 0] : [0, 0, 4, 4] },
        })),
        label: {
          show: true, fontFamily: 'IBM Plex Mono', fontSize: 10, color: '#a0a0a0',
          position: 'outside' as const,
          formatter: (p: any) => fmt(p.value),
        },
      }],
    }
  }

  // ── Data table below chart (timeframe view) ──
  const tableStyle: React.CSSProperties = {
    width: '100%', fontSize: 11, color: '#a0a0a0', fontFamily: 'IBM Plex Mono',
    borderCollapse: 'collapse', marginTop: 4,
  }
  const cellStyle: React.CSSProperties = { padding: '3px 6px', textAlign: 'right', borderBottom: '1px solid #222' }
  const headStyle: React.CSSProperties = { ...cellStyle, textAlign: 'left', color: '#666' }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: '#fff', fontFamily: 'IBM Plex Sans', margin: 0 }}>
          资金流向
        </h3>
        <Segmented
          options={[
            { label: '多周期', value: 'timeframe' },
            { label: '今日明细', value: 'breakdown' },
          ]}
          value={view}
          onChange={(v) => setView(v as FlowView)}
          size="small"
        />
      </div>
      <ReactECharts key={view} option={option} style={{ height: view === 'timeframe' ? '180px' : '220px', width: '100%' }} />
      {view === 'timeframe' && (
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={headStyle}></th>
              {periods.map(p => <th key={p} style={{ ...cellStyle, color: '#888' }}>{p}</th>)}
            </tr>
          </thead>
          <tbody>
            {([['超大单', superLarge, '#ff4d4f'], ['大单', large, '#ff7a45'], ['主力合计', main, '#faad14']] as [string, number[], string][]).map(([name, data, color]) => (
              <tr key={name}>
                <td style={{ ...headStyle, color }}>{name}</td>
                {data.map((v, i) => <td key={i} style={{ ...cellStyle, color: valColor(v), fontWeight: 600 }}>{fmt(v)}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div style={{
        display: 'flex', gap: 16, justifyContent: 'center', marginTop: 6,
        fontSize: 12, color: '#a0a0a0', fontFamily: 'IBM Plex Mono',
      }}>
        <span>主力占比: <strong style={{ color: '#fff' }}>{(ratio * 100).toFixed(1)}%</strong></span>
        <span>资金评分: <strong style={{ color: '#ff6b4a' }}>{score.toFixed(1)}</strong>/10</span>
        <span>趋势: <strong style={{ color: today >= 0 ? '#f5222d' : '#52c41a' }}>{cf.trend}</strong></span>
      </div>
    </div>
  )
}
