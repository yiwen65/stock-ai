import { Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { Stock } from '@/types'
import styles from './StockTable.module.css'

interface StockTableProps {
  data: Stock[]
  loading?: boolean
}

export default function StockTable({ data, loading }: StockTableProps) {
  const navigate = useNavigate()

  const columns: ColumnsType<Stock> = [
    {
      title: '代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
      fixed: 'left',
      render: (code: string) => (
        <span className={styles.stockCode}>{code}</span>
      )
    },
    {
      title: '名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 150,
      fixed: 'left',
      render: (name: string, record: Stock) => (
        <button
          className={styles.stockName}
          onClick={() => navigate(`/analysis/${record.stock_code}`)}
        >
          {name}
        </button>
      )
    },
    {
      title: '最新价',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      align: 'right',
      render: (val: number) => (
        <span className={styles.price}>¥{val.toFixed(2)}</span>
      )
    },
    {
      title: '涨跌幅',
      dataIndex: 'pct_change',
      key: 'pct_change',
      width: 120,
      align: 'right',
      sorter: (a, b) => a.pct_change - b.pct_change,
      render: (val: number) => {
        const isPositive = val > 0
        return (
          <div className={`${styles.change} ${isPositive ? styles.changeUp : styles.changeDown}`}>
            {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            <span>{isPositive ? '+' : ''}{val.toFixed(2)}%</span>
          </div>
        )
      }
    },
    {
      title: 'PE',
      dataIndex: 'pe',
      key: 'pe',
      width: 80,
      align: 'right',
      sorter: (a, b) => (a.pe || 0) - (b.pe || 0),
      render: (val: number | null) => (
        <span className={styles.metric}>{val ? val.toFixed(2) : '-'}</span>
      )
    },
    {
      title: 'PB',
      dataIndex: 'pb',
      key: 'pb',
      width: 80,
      align: 'right',
      sorter: (a, b) => (a.pb || 0) - (b.pb || 0),
      render: (val: number | null) => (
        <span className={styles.metric}>{val ? val.toFixed(2) : '-'}</span>
      )
    },
    {
      title: '市值(亿)',
      dataIndex: 'market_cap',
      key: 'market_cap',
      width: 120,
      align: 'right',
      sorter: (a, b) => a.market_cap - b.market_cap,
      render: (val: number) => (
        <span className={styles.marketCap}>{(val / 100000000).toFixed(2)}</span>
      )
    }
  ]

  return (
    <div className={styles.tableContainer}>
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="stock_code"
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 只股票`,
          className: styles.pagination
        }}
        className={styles.table}
        scroll={{ x: 800 }}
      />
    </div>
  )
}
