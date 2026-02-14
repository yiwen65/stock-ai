import { Skeleton, Card } from 'antd'

type PageType = 'picker' | 'analysis' | 'market'

interface PageSkeletonProps {
  type: PageType
}

function PickerSkeleton() {
  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <Skeleton.Input active style={{ width: '100%', height: 48 }} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i} style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
            <Skeleton active paragraph={{ rows: 2 }} />
          </Card>
        ))}
      </div>
      <Card style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
        <Skeleton active paragraph={{ rows: 8 }} />
      </Card>
    </div>
  )
}

function AnalysisSkeleton() {
  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <Skeleton.Button active style={{ width: 80 }} />
        <Skeleton.Input active style={{ width: 200, height: 36 }} />
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton.Button active key={i} style={{ width: 80, height: 52, borderRadius: 8 }} />
        ))}
      </div>
      <Card style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
        <Skeleton active paragraph={{ rows: 0 }} />
        <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Skeleton.Node active style={{ width: '100%', height: 360 }}>
            <span />
          </Skeleton.Node>
        </div>
      </Card>
      <Card style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    </div>
  )
}

function MarketSkeleton() {
  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
            <Skeleton active paragraph={{ rows: 2 }} />
          </Card>
        ))}
      </div>
      <Card style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
        <Skeleton active paragraph={{ rows: 10 }} />
      </Card>
    </div>
  )
}

export default function PageSkeleton({ type }: PageSkeletonProps) {
  switch (type) {
    case 'picker': return <PickerSkeleton />
    case 'analysis': return <AnalysisSkeleton />
    case 'market': return <MarketSkeleton />
  }
}
