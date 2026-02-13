import ReactECharts from 'echarts-for-react'
import type { KLineData } from '@/types'
import styles from './KLineChart.module.css'

interface KLineChartProps {
  data: KLineData[]
  title?: string
}

export default function KLineChart({ data, title = 'K线图' }: KLineChartProps) {
  const option = {
    backgroundColor: 'transparent',
    title: {
      text: title,
      left: 0,
      textStyle: {
        color: '#ffffff',
        fontSize: 18,
        fontWeight: 700,
        fontFamily: 'IBM Plex Sans'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      backgroundColor: 'rgba(20, 20, 20, 0.95)',
      borderColor: '#2a2a2a',
      textStyle: {
        color: '#ffffff',
        fontFamily: 'IBM Plex Mono'
      }
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.date),
      axisLine: {
        lineStyle: {
          color: '#2a2a2a'
        }
      },
      axisLabel: {
        color: '#a0a0a0',
        fontFamily: 'IBM Plex Mono',
        fontSize: 11
      }
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: {
        lineStyle: {
          color: '#2a2a2a',
          type: 'dashed'
        }
      },
      axisLine: {
        lineStyle: {
          color: '#2a2a2a'
        }
      },
      axisLabel: {
        color: '#a0a0a0',
        fontFamily: 'IBM Plex Mono',
        fontSize: 11
      }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 70,
        end: 100
      },
      {
        type: 'slider',
        start: 70,
        end: 100,
        backgroundColor: '#1a1a1a',
        fillerColor: 'rgba(255, 107, 74, 0.2)',
        borderColor: '#2a2a2a',
        handleStyle: {
          color: '#ff6b4a'
        },
        textStyle: {
          color: '#a0a0a0',
          fontFamily: 'IBM Plex Mono'
        }
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: data.map((d) => [d.open, d.close, d.low, d.high]),
        itemStyle: {
          color: '#00d9c0',
          color0: '#ff4757',
          borderColor: '#00d9c0',
          borderColor0: '#ff4757'
        }
      }
    ]
  }

  return (
    <div className={styles.chartContainer}>
      <ReactECharts option={option} style={{ height: '450px', width: '100%' }} />
    </div>
  )
}
