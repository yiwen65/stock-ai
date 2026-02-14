import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { Segmented } from 'antd'
import type { KLineData } from '@/types'

interface TechIndicatorChartProps {
  data: KLineData[]
}

type IndicatorType = 'MACD' | 'RSI' | 'KDJ' | 'BOLL'

function calcEMA(prices: number[], period: number): number[] {
  const k = 2 / (period + 1)
  const ema: number[] = [prices[0]]
  for (let i = 1; i < prices.length; i++) {
    ema.push(prices[i] * k + ema[i - 1] * (1 - k))
  }
  return ema
}

function calcMACD(data: KLineData[]) {
  const closes = data.map(d => d.close)
  const ema12 = calcEMA(closes, 12)
  const ema26 = calcEMA(closes, 26)
  const dif = ema12.map((v, i) => +(v - ema26[i]).toFixed(3))
  const dea = calcEMA(dif, 9).map(v => +v.toFixed(3))
  const histogram = dif.map((v, i) => +((v - dea[i]) * 2).toFixed(3))
  return { dif, dea, histogram }
}

function calcRSI(data: KLineData[], period = 14): (number | null)[] {
  const closes = data.map(d => d.close)
  const rsi: (number | null)[] = []
  for (let i = 0; i < closes.length; i++) {
    if (i < period) { rsi.push(null); continue }
    let gains = 0, losses = 0
    for (let j = i - period + 1; j <= i; j++) {
      const diff = closes[j] - closes[j - 1]
      if (diff > 0) gains += diff
      else losses -= diff
    }
    const rs = losses === 0 ? 100 : gains / losses
    rsi.push(+(100 - 100 / (1 + rs)).toFixed(1))
  }
  return rsi
}

function calcKDJ(data: KLineData[], n = 9, m1 = 3, m2 = 3) {
  const kArr: (number | null)[] = []
  const dArr: (number | null)[] = []
  const jArr: (number | null)[] = []
  let prevK = 50, prevD = 50
  for (let i = 0; i < data.length; i++) {
    if (i < n - 1) { kArr.push(null); dArr.push(null); jArr.push(null); continue }
    let high = -Infinity, low = Infinity
    for (let j = i - n + 1; j <= i; j++) {
      if (data[j].high > high) high = data[j].high
      if (data[j].low < low) low = data[j].low
    }
    const rsv = high === low ? 50 : ((data[i].close - low) / (high - low)) * 100
    const k = +((2 / m1) * prevK + (1 / m1) * rsv).toFixed(2)
    const d = +((2 / m2) * prevD + (1 / m2) * k).toFixed(2)
    const j = +(3 * k - 2 * d).toFixed(2)
    kArr.push(k); dArr.push(d); jArr.push(j)
    prevK = k; prevD = d
  }
  return { k: kArr, d: dArr, j: jArr }
}

function calcBOLL(data: KLineData[], period = 20, multiplier = 2) {
  const closes = data.map(d => d.close)
  const mid: (number | null)[] = []
  const upper: (number | null)[] = []
  const lower: (number | null)[] = []
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) { mid.push(null); upper.push(null); lower.push(null); continue }
    let sum = 0
    for (let j = i - period + 1; j <= i; j++) sum += closes[j]
    const ma = sum / period
    let variance = 0
    for (let j = i - period + 1; j <= i; j++) variance += (closes[j] - ma) ** 2
    const std = Math.sqrt(variance / period)
    mid.push(+ma.toFixed(2))
    upper.push(+(ma + multiplier * std).toFixed(2))
    lower.push(+(ma - multiplier * std).toFixed(2))
  }
  return { mid, upper, lower }
}

const AXIS_STYLE = {
  axisLine: { lineStyle: { color: '#2a2a2a' } },
  axisLabel: { color: '#a0a0a0', fontFamily: 'IBM Plex Mono', fontSize: 10 },
}
const SPLIT_STYLE = { splitLine: { lineStyle: { color: '#2a2a2a', type: 'dashed' as const } } }
const TOOLTIP = {
  trigger: 'axis' as const,
  axisPointer: { type: 'cross' as const },
  backgroundColor: 'rgba(20,20,20,0.95)',
  borderColor: '#2a2a2a',
  textStyle: { color: '#fff', fontFamily: 'IBM Plex Mono', fontSize: 11 },
}
const ZOOM = (start: number) => [
  { type: 'inside', xAxisIndex: 0, start, end: 100 },
  {
    type: 'slider', xAxisIndex: 0, start, end: 100, top: '90%',
    backgroundColor: '#1a1a1a', fillerColor: 'rgba(255,107,74,0.2)',
    borderColor: '#2a2a2a', handleStyle: { color: '#ff6b4a' },
    textStyle: { color: '#a0a0a0', fontFamily: 'IBM Plex Mono' },
  },
]
const LEGEND = (names: string[]) => ({
  data: names, top: 0, right: 0,
  textStyle: { color: '#a0a0a0', fontSize: 11, fontFamily: 'IBM Plex Mono' },
  itemWidth: 14, itemHeight: 2,
})
const LINE = (name: string, data: (number | null)[], color: string) => ({
  name, type: 'line' as const, data, smooth: true, symbol: 'none' as const,
  lineStyle: { width: 1.5 }, itemStyle: { color },
})

function buildMACDOption(dates: string[], macd: ReturnType<typeof calcMACD>) {
  return {
    backgroundColor: 'transparent', tooltip: TOOLTIP, legend: LEGEND(['DIF', 'DEA', 'MACD']),
    grid: [{ left: '3%', right: '3%', top: '10%', height: '72%', containLabel: true }],
    xAxis: [{ type: 'category', data: dates, ...AXIS_STYLE }],
    yAxis: [{ type: 'value', splitNumber: 4, ...SPLIT_STYLE, ...AXIS_STYLE }],
    dataZoom: ZOOM(70),
    series: [
      {
        name: 'MACD', type: 'bar',
        data: macd.histogram.map(v => ({ value: v, itemStyle: { color: v >= 0 ? '#00d9c0' : '#ff4757', opacity: 0.8 } })),
      },
      LINE('DIF', macd.dif, '#f5a623'),
      LINE('DEA', macd.dea, '#4fc3f7'),
    ],
  }
}

function buildRSIOption(dates: string[], rsi: (number | null)[]) {
  return {
    backgroundColor: 'transparent', tooltip: TOOLTIP, legend: LEGEND(['RSI(14)']),
    grid: [{ left: '3%', right: '3%', top: '10%', height: '72%', containLabel: true }],
    xAxis: [{ type: 'category', data: dates, ...AXIS_STYLE }],
    yAxis: [{ type: 'value', min: 0, max: 100, splitNumber: 4, ...SPLIT_STYLE, ...AXIS_STYLE }],
    dataZoom: ZOOM(70),
    series: [{
      ...LINE('RSI(14)', rsi, '#ab47bc'),
      markLine: {
        silent: true, lineStyle: { type: 'dashed', width: 1, opacity: 0.5 },
        data: [
          { yAxis: 70, lineStyle: { color: '#f5222d' }, label: { formatter: '超买 70', color: '#f5222d', fontSize: 10 } },
          { yAxis: 30, lineStyle: { color: '#52c41a' }, label: { formatter: '超卖 30', color: '#52c41a', fontSize: 10 } },
        ],
      },
    }],
  }
}

function buildKDJOption(dates: string[], kdj: ReturnType<typeof calcKDJ>) {
  return {
    backgroundColor: 'transparent', tooltip: TOOLTIP, legend: LEGEND(['K', 'D', 'J']),
    grid: [{ left: '3%', right: '3%', top: '10%', height: '72%', containLabel: true }],
    xAxis: [{ type: 'category', data: dates, ...AXIS_STYLE }],
    yAxis: [{ type: 'value', min: 0, max: 100, splitNumber: 4, ...SPLIT_STYLE, ...AXIS_STYLE }],
    dataZoom: ZOOM(70),
    series: [
      LINE('K', kdj.k, '#f5a623'),
      LINE('D', kdj.d, '#4fc3f7'),
      LINE('J', kdj.j, '#ab47bc'),
    ],
  }
}

function buildBOLLOption(dates: string[], closes: number[], boll: ReturnType<typeof calcBOLL>) {
  return {
    backgroundColor: 'transparent', tooltip: TOOLTIP, legend: LEGEND(['收盘价', '上轨', '中轨', '下轨']),
    grid: [{ left: '3%', right: '3%', top: '10%', height: '72%', containLabel: true }],
    xAxis: [{ type: 'category', data: dates, ...AXIS_STYLE }],
    yAxis: [{ type: 'value', scale: true, ...SPLIT_STYLE, ...AXIS_STYLE }],
    dataZoom: ZOOM(70),
    series: [
      LINE('收盘价', closes, '#ffffff'),
      { ...LINE('上轨', boll.upper, '#f5222d'), lineStyle: { width: 1, type: 'dashed' as const } },
      LINE('中轨', boll.mid, '#faad14'),
      { ...LINE('下轨', boll.lower, '#52c41a'), lineStyle: { width: 1, type: 'dashed' as const } },
    ],
  }
}

export default function TechIndicatorChart({ data }: TechIndicatorChartProps) {
  const [activeTab, setActiveTab] = useState<IndicatorType>('MACD')
  const dates = useMemo(() => data.map(d => d.date), [data])
  const macd = useMemo(() => calcMACD(data), [data])
  const rsi = useMemo(() => calcRSI(data), [data])
  const kdj = useMemo(() => calcKDJ(data), [data])
  const boll = useMemo(() => calcBOLL(data), [data])
  const closes = useMemo(() => data.map(d => d.close), [data])

  const option = useMemo(() => {
    switch (activeTab) {
      case 'MACD': return buildMACDOption(dates, macd)
      case 'RSI': return buildRSIOption(dates, rsi)
      case 'KDJ': return buildKDJOption(dates, kdj)
      case 'BOLL': return buildBOLLOption(dates, closes, boll)
    }
  }, [activeTab, dates, macd, rsi, kdj, boll, closes])

  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <h3 style={{ fontSize: 18, fontWeight: 700, color: '#fff', fontFamily: 'IBM Plex Sans', margin: 0 }}>
          技术指标
        </h3>
        <Segmented
          options={['MACD', 'RSI', 'KDJ', 'BOLL']}
          value={activeTab}
          onChange={(val) => setActiveTab(val as IndicatorType)}
          size="small"
        />
      </div>
      <ReactECharts option={option} style={{ height: '320px', width: '100%' }} notMerge />
    </div>
  )
}
