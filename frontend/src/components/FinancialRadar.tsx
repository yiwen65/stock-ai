import { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import type { AnalysisReport } from '@/types'

interface FinancialRadarProps {
  report: AnalysisReport
}

export default function FinancialRadar({ report }: FinancialRadarProps) {
  const { fundamental, technical, capital_flow } = report

  const radarData = useMemo(() => {
    const val = fundamental?.valuation || {}
    const prof = fundamental?.profitability || {}
    const growth = fundamental?.growth || {}
    const health = fundamental?.financial_health || {}

    return {
      indicators: [
        { name: '盈利能力', max: 10 },
        { name: '成长性', max: 10 },
        { name: '财务健康', max: 10 },
        { name: '技术面', max: 10 },
        { name: '资金面', max: 10 },
        { name: '估值合理', max: 10 },
      ],
      values: [
        clamp(scoreFromROE(prof.roe)),
        clamp(scoreFromGrowth(growth.revenue_growth, growth.profit_growth)),
        clamp(scoreFromHealth(health.debt_ratio, health.current_ratio)),
        clamp(technical?.score ?? 5),
        clamp(capital_flow?.score ?? 5),
        clamp(scoreFromValuation(val.pe, val.pb)),
      ],
    }
  }, [fundamental, technical, capital_flow])

  const option = {
    backgroundColor: 'transparent',
    title: {
      text: '多维度评分雷达',
      left: 0,
      textStyle: { color: '#fff', fontSize: 16, fontWeight: 700, fontFamily: 'IBM Plex Sans' },
    },
    tooltip: {
      backgroundColor: 'rgba(20,20,20,0.95)',
      borderColor: '#2a2a2a',
      textStyle: { color: '#fff', fontFamily: 'IBM Plex Mono', fontSize: 12 },
    },
    radar: {
      indicator: radarData.indicators,
      shape: 'polygon',
      splitNumber: 5,
      axisName: { color: '#a0a0a0', fontSize: 12, fontFamily: 'IBM Plex Sans' },
      splitLine: { lineStyle: { color: '#2a2a2a' } },
      splitArea: { areaStyle: { color: ['rgba(255,107,74,0.02)', 'rgba(0,217,192,0.02)'] } },
      axisLine: { lineStyle: { color: '#2a2a2a' } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: radarData.values,
            name: '综合评分',
            lineStyle: { color: '#ff6b4a', width: 2 },
            areaStyle: { color: 'rgba(255,107,74,0.15)' },
            itemStyle: { color: '#ff6b4a' },
          },
        ],
      },
    ],
  }

  return <ReactECharts option={option} style={{ height: '320px', width: '100%' }} />
}

function clamp(v: number, min = 0, max = 10): number {
  return Math.max(min, Math.min(max, v))
}

function scoreFromROE(roe?: number): number {
  if (roe == null) return 5
  if (roe >= 20) return 9
  if (roe >= 15) return 7.5
  if (roe >= 10) return 6
  if (roe >= 5) return 4
  return 2
}

function scoreFromGrowth(rev?: number, profit?: number): number {
  const r = rev ?? 0
  const p = profit ?? 0
  const avg = (r + p) / 2
  if (avg >= 30) return 9
  if (avg >= 15) return 7
  if (avg >= 5) return 5
  if (avg >= 0) return 3.5
  return 2
}

function scoreFromHealth(debt?: number, current?: number): number {
  let s = 5
  if (debt != null) {
    if (debt < 30) s += 2
    else if (debt < 50) s += 1
    else if (debt > 70) s -= 2
  }
  if (current != null) {
    if (current > 2) s += 1.5
    else if (current > 1.5) s += 0.5
    else if (current < 1) s -= 1
  }
  return s
}

function scoreFromValuation(pe?: number, pb?: number): number {
  let s = 5
  if (pe != null) {
    if (pe > 0 && pe < 15) s += 2
    else if (pe > 0 && pe < 25) s += 1
    else if (pe > 50) s -= 2
  }
  if (pb != null) {
    if (pb > 0 && pb < 1.5) s += 1.5
    else if (pb > 0 && pb < 3) s += 0.5
    else if (pb > 5) s -= 1
  }
  return s
}
