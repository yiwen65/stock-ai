import { Card, Empty, Tag } from 'antd'
import { Newspaper, ExternalLink } from 'lucide-react'
import type { NewsItem } from '@/types'

interface NewsPanelProps {
  news: NewsItem[]
  loading?: boolean
}

export default function NewsPanel({ news, loading }: NewsPanelProps) {
  if (loading) {
    return (
      <Card
        style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 10 }}
        loading
      />
    )
  }

  if (!news || news.length === 0) {
    return (
      <Card style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 10 }}>
        <Empty description="暂无相关新闻" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </Card>
    )
  }

  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 10,
      padding: '16px',
    }}>
      <h4 style={{
        fontSize: 16,
        fontWeight: 700,
        color: '#fff',
        fontFamily: 'IBM Plex Sans',
        margin: '0 0 12px 0',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <Newspaper size={18} />
        消息面动态
      </h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {news.slice(0, 10).map((item, i) => (
          <div
            key={i}
            style={{
              padding: '10px 12px',
              background: 'rgba(255,255,255,0.02)',
              borderRadius: 8,
              border: '1px solid rgba(255,255,255,0.05)',
              transition: 'border-color 0.2s',
              cursor: item.url ? 'pointer' : 'default',
            }}
            onClick={() => item.url && window.open(item.url, '_blank')}
            onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(255,107,74,0.3)')}
            onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.05)')}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#e0e0e0', lineHeight: 1.5, flex: 1 }}>
                {item.title}
              </div>
              {item.url && <ExternalLink size={14} style={{ color: '#666', flexShrink: 0, marginTop: 3 }} />}
            </div>
            {item.content && (
              <div style={{ fontSize: 12, color: '#888', marginTop: 6, lineHeight: 1.6 }}>
                {item.content}
              </div>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
              {item.source && <Tag style={{ margin: 0, fontSize: 11 }}>{item.source}</Tag>}
              {item.publish_time && (
                <span style={{ fontSize: 11, color: '#666' }}>{item.publish_time}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
