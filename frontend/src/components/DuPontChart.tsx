import ReactECharts from 'echarts-for-react'
import { Tag } from 'antd'
import type { DuPontAnalysis } from '@/types'

interface DuPontChartProps {
  data: DuPontAnalysis
}

export default function DuPontChart({ data }: DuPontChartProps) {
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(20,20,20,0.95)',
      borderColor: '#2a2a2a',
      textStyle: { color: '#fff', fontFamily: 'IBM Plex Mono', fontSize: 12 },
    },
    series: [
      {
        type: 'tree',
        data: [
          {
            name: `ROE\n${data.roe.toFixed(2)}%`,
            itemStyle: { color: '#ff6b4a', borderColor: '#ff6b4a' },
            label: { fontSize: 14, fontWeight: 'bold' },
            children: [
              {
                name: `净利率\n${data.net_profit_margin.toFixed(2)}%`,
                itemStyle: { color: '#4fc3f7', borderColor: '#4fc3f7' },
              },
              {
                name: `周转率\n${data.asset_turnover.toFixed(2)}`,
                itemStyle: { color: '#00d9c0', borderColor: '#00d9c0' },
              },
              {
                name: `权益乘数\n${data.equity_multiplier.toFixed(2)}`,
                itemStyle: { color: '#faad14', borderColor: '#faad14' },
              },
            ],
          },
        ],
        top: '8%',
        left: '10%',
        bottom: '16%',
        right: '10%',
        symbolSize: 14,
        orient: 'TB',
        expandAndCollapse: false,
        label: {
          position: 'inside',
          backgroundColor: 'rgba(30,30,30,0.9)',
          borderRadius: 6,
          padding: [8, 12],
          color: '#fff',
          fontSize: 13,
          fontFamily: 'IBM Plex Mono',
          lineHeight: 20,
          rich: {},
        },
        lineStyle: {
          color: '#444',
          width: 2,
          curveness: 0.5,
        },
        itemStyle: {
          borderWidth: 2,
        },
      },
    ],
  }

  const driverColor =
    data.driver === '盈利能力驱动' ? '#4fc3f7'
    : data.driver === '运营效率驱动' ? '#00d9c0'
    : data.driver === '杠杆驱动' ? '#faad14'
    : '#a0a0a0'

  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 10,
      padding: '16px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
        <h4 style={{ fontSize: 16, fontWeight: 700, color: '#fff', fontFamily: 'IBM Plex Sans', margin: 0 }}>
          杜邦分析
        </h4>
        <Tag color={driverColor} style={{ margin: 0 }}>{data.driver}</Tag>
      </div>
      <ReactECharts option={option} style={{ height: '220px', width: '100%' }} />
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 8,
        marginTop: 4,
        textAlign: 'center',
        fontSize: 12,
        color: '#a0a0a0',
      }}>
        <div>
          <div style={{ fontWeight: 700, color: '#ff6b4a', fontSize: 16, fontFamily: 'IBM Plex Mono' }}>
            {data.roe.toFixed(2)}%
          </div>
          <div>ROE</div>
        </div>
        <div>
          <div style={{ fontWeight: 700, color: '#4fc3f7', fontSize: 16, fontFamily: 'IBM Plex Mono' }}>
            {data.net_profit_margin.toFixed(2)}%
          </div>
          <div>净利率</div>
        </div>
        <div>
          <div style={{ fontWeight: 700, color: '#00d9c0', fontSize: 16, fontFamily: 'IBM Plex Mono' }}>
            {data.asset_turnover.toFixed(2)}
          </div>
          <div>周转率</div>
        </div>
        <div>
          <div style={{ fontWeight: 700, color: '#faad14', fontSize: 16, fontFamily: 'IBM Plex Mono' }}>
            {data.equity_multiplier.toFixed(2)}
          </div>
          <div>权益乘数</div>
        </div>
      </div>
    </div>
  )
}
