import { Anchor } from 'antd'

interface AnchorItem {
  key: string
  label: string
}

interface AnchorNavProps {
  items: AnchorItem[]
}

export default function AnchorNav({ items }: AnchorNavProps) {
  return (
    <div style={{
      position: 'fixed',
      right: 24,
      top: '50%',
      transform: 'translateY(-50%)',
      zIndex: 100,
      background: 'rgba(20,20,20,0.85)',
      backdropFilter: 'blur(8px)',
      borderRadius: 8,
      border: '1px solid var(--color-border)',
      padding: '8px 4px',
    }}>
      <Anchor
        direction="vertical"
        offsetTop={80}
        items={items.map(item => ({
          key: item.key,
          href: `#section-${item.key}`,
          title: (
            <span style={{ fontSize: 12, whiteSpace: 'nowrap' }}>{item.label}</span>
          ),
        }))}
      />
    </div>
  )
}
