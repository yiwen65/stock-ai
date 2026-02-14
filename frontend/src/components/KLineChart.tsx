import { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { Segmented } from 'antd'
import type { KLineData } from '@/types'
import styles from './KLineChart.module.css'

type KLinePeriod = '1d' | '1w' | '1M'

interface KLineChartProps {
  data: KLineData[]
  title?: string
  period?: KLinePeriod
  onPeriodChange?: (period: KLinePeriod) => void
}

function calcMA(data: KLineData[], period: number): (number | null)[] {
  const result: (number | null)[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else {
      let sum = 0
      for (let j = 0; j < period; j++) sum += data[i - j].close
      result.push(+(sum / period).toFixed(2))
    }
  }
  return result
}

const PERIOD_OPTIONS = [
  { label: '日K', value: '1d' },
  { label: '周K', value: '1w' },
  { label: '月K', value: '1M' },
]

export default function KLineChart({ data, title = 'K线图', period = '1d', onPeriodChange }: KLineChartProps) {
  const dates = useMemo(() => data.map((d) => d.date), [data])
  const ma5 = useMemo(() => calcMA(data, 5), [data])
  const ma10 = useMemo(() => calcMA(data, 10), [data])
  const ma20 = useMemo(() => calcMA(data, 20), [data])
  const ma60 = useMemo(() => calcMA(data, 60), [data])
  const volumes = useMemo(() => data.map((d) => d.volume ?? 0), [data])
  const volColors = useMemo(
    () => data.map((d) => (d.close >= d.open ? '#00d9c0' : '#ff4757')),
    [data]
  )

  const option = {
    backgroundColor: 'transparent',
    title: {
      text: title,
      left: 0,
      textStyle: { color: '#ffffff', fontSize: 18, fontWeight: 700, fontFamily: 'IBM Plex Sans' }
    },
    legend: {
      data: ['MA5', 'MA10', 'MA20', 'MA60'],
      top: 4,
      right: 0,
      textStyle: { color: '#a0a0a0', fontSize: 11, fontFamily: 'IBM Plex Mono' },
      itemWidth: 14,
      itemHeight: 2
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(20, 20, 20, 0.95)',
      borderColor: '#2a2a2a',
      textStyle: { color: '#ffffff', fontFamily: 'IBM Plex Mono', fontSize: 12 }
    },
    axisPointer: { link: [{ xAxisIndex: [0, 1] }] },
    grid: [
      { left: '3%', right: '3%', top: '15%', height: '55%', containLabel: true },
      { left: '3%', right: '3%', top: '76%', height: '12%', containLabel: true }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        axisLine: { lineStyle: { color: '#2a2a2a' } },
        axisLabel: { color: '#a0a0a0', fontFamily: 'IBM Plex Mono', fontSize: 11 }
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1,
        axisLine: { lineStyle: { color: '#2a2a2a' } },
        axisLabel: { show: false }
      }
    ],
    yAxis: [
      {
        type: 'value',
        scale: true,
        gridIndex: 0,
        splitLine: { lineStyle: { color: '#2a2a2a', type: 'dashed' } },
        axisLine: { lineStyle: { color: '#2a2a2a' } },
        axisLabel: { color: '#a0a0a0', fontFamily: 'IBM Plex Mono', fontSize: 11 }
      },
      {
        type: 'value',
        gridIndex: 1,
        splitNumber: 2,
        splitLine: { lineStyle: { color: '#2a2a2a', type: 'dashed' } },
        axisLine: { lineStyle: { color: '#2a2a2a' } },
        axisLabel: {
          color: '#a0a0a0',
          fontFamily: 'IBM Plex Mono',
          fontSize: 10,
          formatter: (v: number) => (v >= 1e8 ? (v / 1e8).toFixed(1) + '亿' : v >= 1e4 ? (v / 1e4).toFixed(0) + '万' : v.toString())
        }
      }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 70, end: 100 },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        start: 70,
        end: 100,
        top: '92%',
        backgroundColor: '#1a1a1a',
        fillerColor: 'rgba(255, 107, 74, 0.2)',
        borderColor: '#2a2a2a',
        handleStyle: { color: '#ff6b4a' },
        textStyle: { color: '#a0a0a0', fontFamily: 'IBM Plex Mono' }
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: data.map((d) => [d.open, d.close, d.low, d.high]),
        itemStyle: { color: '#00d9c0', color0: '#ff4757', borderColor: '#00d9c0', borderColor0: '#ff4757' }
      },
      { name: 'MA5', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: ma5, smooth: true, lineStyle: { width: 1 }, symbol: 'none', itemStyle: { color: '#f5a623' } },
      { name: 'MA10', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: ma10, smooth: true, lineStyle: { width: 1 }, symbol: 'none', itemStyle: { color: '#4fc3f7' } },
      { name: 'MA20', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: ma20, smooth: true, lineStyle: { width: 1 }, symbol: 'none', itemStyle: { color: '#ab47bc' } },
      { name: 'MA60', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: ma60, smooth: true, lineStyle: { width: 1 }, symbol: 'none', itemStyle: { color: '#66bb6a' } },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes.map((v, i) => ({ value: v, itemStyle: { color: volColors[i], opacity: 0.7 } }))
      }
    ]
  }

  return (
    <div className={styles.chartContainer}>
      {onPeriodChange && (
        <div className={styles.periodSelector}>
          <Segmented
            options={PERIOD_OPTIONS}
            value={period}
            onChange={(val) => onPeriodChange(val as KLinePeriod)}
            size="small"
          />
        </div>
      )}
      <ReactECharts option={option} style={{ height: '520px', width: '100%' }} />
    </div>
  )
}
