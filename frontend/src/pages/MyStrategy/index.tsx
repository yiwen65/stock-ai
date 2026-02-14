import { useState, useCallback } from 'react'
import { Button, Card, Table, Tag, Modal, Input, Select, message, Empty, Popconfirm } from 'antd'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Play, Trash2, History } from 'lucide-react'
import { strategyApi } from '@/services/strategy'
import type { Strategy } from '@/types'
import styles from './MyStrategy.module.css'

const STRATEGY_OPTIONS = [
  { value: 'graham', label: '格雷厄姆价值投资' },
  { value: 'buffett', label: '巴菲特护城河' },
  { value: 'quality_factor', label: '质量因子策略' },
  { value: 'peg', label: 'PEG成长策略' },
  { value: 'lynch', label: '彼得·林奇成长' },
  { value: 'rs_momentum', label: 'RS相对强度动量' },
  { value: 'dual_momentum', label: '双动量策略' },
  { value: 'ma_breakout', label: '均线多头排列' },
  { value: 'macd_divergence', label: 'MACD底背离' },
  { value: 'volume_breakout', label: '放量突破平台' },
  { value: 'earnings_surprise', label: '业绩预增事件驱动' },
  { value: 'shareholder_increase', label: '股东增持/回购' },
  { value: 'northbound', label: '北向资金持续流入' },
]

function ExecutionHistory({ strategyId }: { strategyId: number }) {
  const { data: execRaw, isLoading } = useQuery({
    queryKey: ['executions', strategyId],
    queryFn: () => strategyApi.listExecutions(strategyId, 10),
    staleTime: 30000,
  })
  const executions: any[] = Array.isArray(execRaw) ? execRaw : (execRaw as any)?.data || []

  if (isLoading) return <div style={{ padding: 12, opacity: 0.6 }}>加载执行历史...</div>
  if (!executions.length) return <div style={{ padding: 12, opacity: 0.6 }}>暂无执行记录，点击「执行」运行策略</div>

  const cols = [
    {
      title: '执行时间', dataIndex: 'executed_at', key: 'time', width: 180,
      render: (t: string) => t ? new Date(t).toLocaleString() : '-',
    },
    { title: '结果数量', dataIndex: 'result_count', key: 'count', width: 100 },
    {
      title: 'Top 股票', dataIndex: 'result_snapshot', key: 'snapshot',
      render: (snap: any[]) => snap?.slice(0, 5).map((s: any) =>
        <Tag key={s.stock_code} style={{ marginBottom: 2 }}>{s.stock_name || s.stock_code}</Tag>
      ) || '-',
    },
  ]

  return (
    <Table
      dataSource={executions}
      columns={cols}
      rowKey="id"
      size="small"
      pagination={false}
      style={{ background: 'transparent' }}
    />
  )
}

export default function MyStrategy() {
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newType, setNewType] = useState('graham')
  const [running, setRunning] = useState<number | null>(null)

  const { data: strategiesRes, isLoading } = useQuery({
    queryKey: ['userStrategies'],
    queryFn: () => strategyApi.listUserStrategies(),
  })
  const strategies: Strategy[] = Array.isArray(strategiesRes)
    ? strategiesRes
    : (strategiesRes as any)?.data || []

  const createMutation = useMutation({
    mutationFn: strategyApi.createUserStrategy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userStrategies'] })
      setShowCreate(false)
      setNewName('')
      message.success('策略已保存')
    },
    onError: (e: any) => message.error(e?.response?.data?.detail || '创建失败'),
  })

  const deleteMutation = useMutation({
    mutationFn: strategyApi.deleteUserStrategy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userStrategies'] })
      message.success('已删除')
    },
    onError: (e: any) => message.error(e?.response?.data?.detail || '删除失败'),
  })

  const handleCreate = useCallback(() => {
    if (!newName.trim()) { message.warning('请输入策略名称'); return }
    createMutation.mutate({
      name: newName.trim(),
      strategy_type: newType,
      conditions: {},
    })
  }, [newName, newType, createMutation])

  const handleRun = useCallback(async (strategy: Strategy) => {
    setRunning(strategy.id)
    try {
      const res: any = await strategyApi.execute({
        strategy_type: strategy.strategy_type,
        limit: 30,
      })
      const data = Array.isArray(res) ? res : res?.data || []
      message.success(`执行完成，筛选出 ${data.length} 只股票`)
      // Record execution history
      try {
        const snapshot = data.slice(0, 10).map((s: any) => ({
          stock_code: s.stock_code, stock_name: s.stock_name, score: s.score,
        }))
        await strategyApi.recordExecution(strategy.id, data.length, snapshot)
        queryClient.invalidateQueries({ queryKey: ['executions', strategy.id] })
      } catch { /* non-critical */ }
    } catch (e: any) {
      message.error('执行失败: ' + (e?.message || '未知错误'))
    } finally {
      setRunning(null)
    }
  }, [queryClient])

  const columns = [
    { title: '策略名称', dataIndex: 'name', key: 'name', render: (t: string) => <strong>{t}</strong> },
    {
      title: '策略类型', dataIndex: 'strategy_type', key: 'type',
      render: (t: string) => {
        const label = STRATEGY_OPTIONS.find(o => o.value === t)?.label || t
        return <Tag color="blue">{label}</Tag>
      }
    },
    {
      title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 200,
      render: (t: string) => t ? new Date(t).toLocaleString() : '-',
    },
    {
      title: '操作', key: 'actions', width: 200,
      render: (_: any, r: Strategy) => (
        <div style={{ display: 'flex', gap: 8 }}>
          <Button
            size="small"
            type="primary"
            icon={<Play size={14} />}
            loading={running === r.id}
            onClick={() => handleRun(r)}
          >
            执行
          </Button>
          <Popconfirm title="确认删除此策略?" onConfirm={() => deleteMutation.mutate(r.id)}>
            <Button size="small" danger icon={<Trash2 size={14} />}>删除</Button>
          </Popconfirm>
        </div>
      )
    },
  ]

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>我的策略</h1>
        <p className={styles.subtitle}>保存常用选股策略，随时一键执行</p>
      </div>

      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<Plus size={16} />} onClick={() => setShowCreate(true)}>
          新建策略
        </Button>
      </div>

      {strategies.length > 0 ? (
        <Card style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <Table
            dataSource={strategies}
            columns={columns}
            rowKey="id"
            pagination={false}
            size="middle"
            loading={isLoading}
            expandable={{
              expandedRowRender: (record: Strategy) => <ExecutionHistory strategyId={record.id} />,
              expandIcon: ({ expanded, onExpand, record }) => (
                <Button
                  type="text"
                  size="small"
                  icon={<History size={14} />}
                  onClick={e => onExpand(record, e)}
                  style={{ color: expanded ? 'var(--ant-color-primary)' : undefined }}
                />
              ),
            }}
          />
        </Card>
      ) : (
        <div className={styles.emptyState}>
          <Empty description={isLoading ? '加载中...' : '暂无保存的策略'} />
          {!isLoading && (
            <p className={styles.emptyText} style={{ marginTop: 12 }}>
              点击「新建策略」创建您的第一个选股策略
            </p>
          )}
        </div>
      )}

      <Modal
        title="新建策略"
        open={showCreate}
        onOk={handleCreate}
        onCancel={() => setShowCreate(false)}
        okText="保存"
        cancelText="取消"
        confirmLoading={createMutation.isPending}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, paddingTop: 8 }}>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>策略名称</label>
            <Input
              placeholder="例如：我的价值选股"
              value={newName}
              onChange={e => setNewName(e.target.value)}
              onPressEnter={handleCreate}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>策略类型</label>
            <Select
              value={newType}
              onChange={setNewType}
              options={STRATEGY_OPTIONS}
              style={{ width: '100%' }}
            />
          </div>
        </div>
      </Modal>
    </div>
  )
}
