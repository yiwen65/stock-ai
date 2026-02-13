import styles from './Market.module.css'

export default function Market() {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>市场概览</h1>
        <p className={styles.subtitle}>实时市场数据与行情分析</p>
      </div>

      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>📈</div>
        <h3 className={styles.emptyTitle}>市场数据加载中</h3>
        <p className={styles.emptyText}>
          实时市场行情、板块热度、资金流向等数据即将上线
        </p>
      </div>
    </div>
  )
}
