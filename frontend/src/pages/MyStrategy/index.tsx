import styles from './MyStrategy.module.css'

export default function MyStrategy() {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>我的策略</h1>
        <p className={styles.subtitle}>管理和执行您的自定义选股策略</p>
      </div>

      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>📋</div>
        <h3 className={styles.emptyTitle}>暂无策略</h3>
        <p className={styles.emptyText}>
          创建您的第一个自定义选股策略，系统将保存并可随时执行
        </p>
      </div>
    </div>
  )
}
