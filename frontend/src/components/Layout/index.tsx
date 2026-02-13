import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { TrendingUp, BarChart3, Settings, Activity } from 'lucide-react'
import styles from './Layout.module.css'

export default function Layout() {
  const navigate = useNavigate()
  const location = useLocation()

  const navItems = [
    { key: '/', icon: TrendingUp, label: '选股中心' },
    { key: '/market', icon: Activity, label: '市场概览' },
    { key: '/strategy', icon: Settings, label: '我的策略' }
  ]

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.logo}>
            <BarChart3 size={32} strokeWidth={2.5} />
            <h1 className={styles.logoText}>
              <span className={styles.logoMain}>A股AI</span>
              <span className={styles.logoSub}>智能分析</span>
            </h1>
          </div>
          <div className={styles.headerRight}>
            <div className={styles.statusIndicator}>
              <span className={styles.statusDot}></span>
              <span className={styles.statusText}>实时数据</span>
            </div>
          </div>
        </div>
      </header>

      <div className={styles.container}>
        <aside className={styles.sidebar}>
          <nav className={styles.nav}>
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.key
              return (
                <button
                  key={item.key}
                  className={`${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
                  onClick={() => navigate(item.key)}
                >
                  <Icon size={20} strokeWidth={2} />
                  <span>{item.label}</span>
                </button>
              )
            })}
          </nav>
        </aside>

        <main className={styles.main}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
