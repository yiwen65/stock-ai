import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider, theme, App as AntApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000
    }
  }
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        locale={zhCN}
        theme={{
          algorithm: theme.darkAlgorithm,
          token: {
            colorPrimary: '#ff6b4a',
            colorSuccess: '#00d9c0',
            colorError: '#ff4757',
            colorWarning: '#faad14',
            colorBgBase: '#0a0a0a',
            colorBgContainer: '#141414',
            colorBgElevated: '#1e1e1e',
            colorBorder: '#2a2a2a',
            colorText: '#ffffff',
            colorTextSecondary: '#a0a0a0',
            borderRadius: 8,
            fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif",
            fontFamilyCode: "'IBM Plex Mono', 'Fira Code', monospace",
          },
        }}
      >
        <AntApp
          message={{ maxCount: 3, duration: 2.5 }}
          notification={{ placement: 'topRight', duration: 4 }}
        >
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </AntApp>
      </ConfigProvider>
    </QueryClientProvider>
  </React.StrictMode>
)
