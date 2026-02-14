import { useState } from 'react'
import { Button, Card, Table, Tag, Input, message, Empty, Popconfirm } from 'antd'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, BarChart3 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { watchlistApi } from '@/services/watchlist'
import type { WatchlistItem } from '@/services/watchlist'
import styles from './Watchlist.module.css'

export default function Watchlist() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [addCode, setAddCode] = useState('')
  const [addName, setAddName] = useState('')

  const { data: listRaw, isLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: () => watchlistApi.list(),
  })
  const items: WatchlistItem[] = Array.isArray(listRaw) ? listRaw : (listRaw as any)?.data || []

  const addMutation = useMutation({
    mutationFn: () => watchlistApi.add(addCode.trim(), addName.trim()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
      setAddCode('')
      setAddName('')
      message.success('已添加到自选股')
    },
    onError: (e: any) => message.error(e?.response?.data?.detail || '添加失败'),
  })

  const removeMutation = useMutation({
    mutationFn: watchlistApi.remove,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
      message.success('已从自选股移除')
    },
    onError: (e: any) => message.error(e?.response?.data?.detail || '删除失败'),
  })

  const handleAdd = () => {
    if (!addCode.trim()) { message.warning('请输入股票代码'); return }
    addMutation.mutate()
  }

  const columns = [
    {
      title: '股票代码', dataIndex: 'stock_code', key: 'code', width: 120,
      render: (code: string) => <Tag color="blue">{code}</Tag>,
    },
    {
      title: '股票名称', dataIndex: 'stock_name', key: 'name',
      render: (name: string) => <strong>{name || '-'}</strong>,
    },
    {
      title: '备注', dataIndex: 'note', key: 'note', width: 200,
      render: (note: string) => note || '-',
    },
    {
      title: '添加时间', dataIndex: 'created_at', key: 'time', width: 180,
      render: (t: string) => t ? new Date(t).toLocaleString() : '-',
    },
    {
      title: '操作', key: 'actions', width: 180,
      render: (_: any, r: WatchlistItem) => (
        <div style={{ display: 'flex', gap: 8 }}>
          <Button
            size="small"
            type="primary"
            icon={<BarChart3 size={14} />}
            onClick={() => navigate(`/analysis/${r.stock_code}`)}
          >
            分析
          </Button>
          <Popconfirm title="确认移除?" onConfirm={() => removeMutation.mutate(r.stock_code)}>
            <Button size="small" danger icon={<Trash2 size={14} />}>移除</Button>
          </Popconfirm>
        </div>
      ),
    },
  ]

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>自选股</h1>
        <p className={styles.subtitle}>管理您关注的股票，快速跳转至深度分析</p>
      </div>

      <div className={styles.addBar}>
        <Input
          placeholder="股票代码，如 600519"
          value={addCode}
          onChange={e => setAddCode(e.target.value)}
          onPressEnter={handleAdd}
          style={{ maxWidth: 180 }}
        />
        <Input
          placeholder="股票名称（可选）"
          value={addName}
          onChange={e => setAddName(e.target.value)}
          onPressEnter={handleAdd}
          style={{ maxWidth: 180 }}
        />
        <Button
          type="primary"
          icon={<Plus size={16} />}
          onClick={handleAdd}
          loading={addMutation.isPending}
        >
          添加
        </Button>
      </div>

      {items.length > 0 ? (
        <Card style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <Table
            dataSource={items}
            columns={columns}
            rowKey="id"
            pagination={false}
            size="middle"
            loading={isLoading}
          />
        </Card>
      ) : (
        <div className={styles.emptyState}>
          <Empty description={isLoading ? '加载中...' : '暂无自选股'} />
          {!isLoading && (
            <p className={styles.emptyText} style={{ marginTop: 12 }}>
              输入股票代码添加到自选股，方便随时查看分析
            </p>
          )}
        </div>
      )}
    </div>
  )
}
