import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { TrendingUp, BarChart3, Settings, Activity, Star, LogIn, LogOut, User } from 'lucide-react'
import StockSearch from '@/components/StockSearch'
import styles from './Layout.module.css'

export default function Layout() {
  const navigate = useNavigate()
  const location = useLocation()
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('token'))

  useEffect(() => {
    const check = () => setIsLoggedIn(!!localStorage.getItem('token'))
    window.addEventListener('storage', check)
    return () => window.removeEventListener('storage', check)
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    setIsLoggedIn(false)
    navigate('/')
  }

  const navItems = [
    { key: '/', icon: TrendingUp, label: '选股中心' },
    { key: '/market', icon: Activity, label: '市场概览' },
    { key: '/watchlist', icon: Star, label: '自选股' },
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
          <div className={styles.headerCenter} style={{ flex: 1, display: 'flex', justifyContent: 'center', padding: '0 24px' }}>
            <StockSearch />
          </div>
          <div className={styles.headerRight}>
            <div className={styles.statusIndicator}>
              <span className={styles.statusDot}></span>
              <span className={styles.statusText}>实时数据</span>
            </div>
            {isLoggedIn ? (
              <button className={styles.authButton} onClick={handleLogout} title="登出">
                <User size={16} />
                <LogOut size={14} style={{ marginLeft: 4 }} />
              </button>
            ) : (
              <button className={styles.authButton} onClick={() => navigate('/login')} title="登录">
                <LogIn size={16} />
                <span style={{ marginLeft: 4, fontSize: 13 }}>登录</span>
              </button>
            )}
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

      <footer className={styles.footer}>
        <span>数据来源：AKShare (公开市场数据)　|　AI分析仅供参考，不构成投资建议　|　</span>
        <a className={styles.footerLink} onClick={() => navigate('/disclaimer')}>免责声明</a>
        <span>　|　</span>
        <a className={styles.footerLink} onClick={() => navigate('/terms')}>用户协议</a>
        <span>　|　</span>
        <a className={styles.footerLink} onClick={() => navigate('/privacy')}>隐私政策</a>
      </footer>
    </div>
  )
}
