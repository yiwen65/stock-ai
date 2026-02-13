# Phase 5: 前端应用开发

**优先级**: 🟡 中
**状态**: ⬜ 待开始
**预计工作量**: 大
**依赖**: Phase 1C, Phase 2 完成

---

## 任务清单

### ⬜ Task 1: React 项目初始化
**状态**: 待开始
**文件**:
- 创建: `frontend/package.json`
- 创建: `frontend/vite.config.ts`
- 创建: `frontend/tsconfig.json`
- 创建: `frontend/src/main.tsx`

**步骤**:

1. **初始化 Vite + React + TypeScript 项目**
   ```bash
   cd frontend
   npm create vite@latest . -- --template react-ts
   ```

2. **安装核心依赖**
   ```bash
   npm install \
     react@18.2.0 \
     react-dom@18.2.0 \
     react-router-dom@6.22.0 \
     antd@5.14.0 \
     @ant-design/icons@5.3.0 \
     echarts@5.5.0 \
     echarts-for-react@3.0.2 \
     zustand@4.5.0 \
     @tanstack/react-query@5.20.0 \
     axios@1.6.7 \
     dayjs@1.11.10
   ```

3. **安装开发依赖**
   ```bash
   npm install -D \
     @types/react@18.2.55 \
     @types/react-dom@18.2.19 \
     @vitejs/plugin-react@4.2.1 \
     typescript@5.3.3 \
     tailwindcss@3.4.1 \
     autoprefixer@10.4.17 \
     postcss@8.4.35
   ```

4. **配置 Vite**
   ```typescript
   // frontend/vite.config.ts
   import { defineConfig } from 'vite'
   import react from '@vitejs/plugin-react'
   import path from 'path'

   export default defineConfig({
     plugins: [react()],
     resolve: {
       alias: {
         '@': path.resolve(__dirname, './src')
       }
     },
     server: {
       port: 3000,
       proxy: {
         '/api': {
           target: 'http://localhost:8000',
           changeOrigin: true
         }
       }
     }
   })
   ```

5. **配置 TypeScript**
   ```json
   // frontend/tsconfig.json
   {
     "compilerOptions": {
       "target": "ES2020",
       "useDefineForClassFields": true,
       "lib": ["ES2020", "DOM", "DOM.Iterable"],
       "module": "ESNext",
       "skipLibCheck": true,
       "moduleResolution": "bundler",
       "allowImportingTsExtensions": true,
       "resolveJsonModule": true,
       "isolatedModules": true,
       "noEmit": true,
       "jsx": "react-jsx",
       "strict": true,
       "noUnusedLocals": true,
       "noUnusedParameters": true,
       "noFallthroughCasesInSwitch": true,
       "baseUrl": ".",
       "paths": {
         "@/*": ["./src/*"]
       }
     },
     "include": ["src"],
     "references": [{ "path": "./tsconfig.node.json" }]
   }
   ```

6. **提交代码**
   ```bash
   git add frontend/
   git commit -m "feat: initialize React frontend project"
   ```

---

### ⬜ Task 2: 基础架构搭建
**状态**: 待开始
**文件**:
- 创建: `frontend/src/services/api.ts`
- 创建: `frontend/src/stores/userStore.ts`
- 创建: `frontend/src/types/index.ts`
- 创建: `frontend/src/App.tsx`

**步骤**:

1. **创建 API 客户端**
   ```typescript
   // frontend/src/services/api.ts
   import axios from 'axios'

   const api = axios.create({
     baseURL: '/api/v1',
     timeout: 10000
   })

   // 请求拦截器
   api.interceptors.request.use(
     (config) => {
       const token = localStorage.getItem('token')
       if (token) {
         config.headers.Authorization = `Bearer ${token}`
       }
       return config
     },
     (error) => Promise.reject(error)
   )

   // 响应拦截器
   api.interceptors.response.use(
     (response) => response.data,
     (error) => {
       if (error.response?.status === 401) {
         localStorage.removeItem('token')
         window.location.href = '/login'
       }
       return Promise.reject(error)
     }
   )

   export default api
   ```

2. **创建类型定义**
   ```typescript
   // frontend/src/types/index.ts

   export interface Stock {
     stock_code: string
     stock_name: string
     price: number
     change: number
     pct_change: number
     pe: number
     pb: number
     market_cap: number
   }

   export interface Strategy {
     id: number
     name: string
     strategy_type: string
     conditions: any
     created_at: string
   }

   export interface AnalysisReport {
     stock_code: string
     stock_name: string
     fundamental: {
       score: number
       summary: string
     }
     technical: {
       score: number
       trend: string
       summary: string
     }
     overall_score: number
     recommendation: string
     summary: string
   }
   ```

3. **创建状态管理**
   ```typescript
   // frontend/src/stores/userStore.ts
   import { create } from 'zustand'

   interface UserState {
     user: any | null
     token: string | null
     setUser: (user: any) => void
     setToken: (token: string) => void
     logout: () => void
   }

   export const useUserStore = create<UserState>((set) => ({
     user: null,
     token: localStorage.getItem('token'),
     setUser: (user) => set({ user }),
     setToken: (token) => {
       localStorage.setItem('token', token)
       set({ token })
     },
     logout: () => {
       localStorage.removeItem('token')
       set({ user: null, token: null })
     }
   }))
   ```

4. **创建路由配置**
   ```typescript
   // frontend/src/App.tsx
   import { BrowserRouter, Routes, Route } from 'react-router-dom'
   import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
   import Layout from '@/components/Layout'
   import StockPicker from '@/pages/StockPicker'
   import StockAnalysis from '@/pages/StockAnalysis'
   import MyStrategy from '@/pages/MyStrategy'
   import Market from '@/pages/Market'

   const queryClient = new QueryClient()

   function App() {
     return (
       <QueryClientProvider client={queryClient}>
         <BrowserRouter>
           <Routes>
             <Route path="/" element={<Layout />}>
               <Route index element={<StockPicker />} />
               <Route path="analysis/:code" element={<StockAnalysis />} />
               <Route path="strategy" element={<MyStrategy />} />
               <Route path="market" element={<Market />} />
             </Route>
           </Routes>
         </BrowserRouter>
       </QueryClientProvider>
     )
   }

   export default App
   ```

5. **提交代码**
   ```bash
   git add frontend/src/
   git commit -m "feat: setup frontend architecture"
   ```

---

### ⬜ Task 3: 选股中心页面
**状态**: 待开始
**文件**:
- 创建: `frontend/src/pages/StockPicker/index.tsx`
- 创建: `frontend/src/components/StrategyForm.tsx`
- 创建: `frontend/src/components/StockTable.tsx`
- 创建: `frontend/src/services/strategy.ts`

**步骤**:

1. **创建策略 API 服务**
   ```typescript
   // frontend/src/services/strategy.ts
   import api from './api'

   export const strategyApi = {
     execute: (params: any) =>
       api.post('/strategies/execute', params),

     parse: (description: string) =>
       api.post('/strategies/parse', { description }),

     list: () =>
       api.get('/strategies')
   }
   ```

2. **创建策略表单组件**
   ```typescript
   // frontend/src/components/StrategyForm.tsx
   import { Form, Select, InputNumber, Button } from 'antd'

   export default function StrategyForm({ onSubmit }: any) {
     const [form] = Form.useForm()

     return (
       <Form form={form} onFinish={onSubmit} layout="inline">
         <Form.Item name="strategy_type" label="策略类型">
           <Select style={{ width: 200 }}>
             <Select.Option value="graham">格雷厄姆价值</Select.Option>
             <Select.Option value="buffett">巴菲特护城河</Select.Option>
             <Select.Option value="peg">PEG成长</Select.Option>
             <Select.Option value="custom">自定义</Select.Option>
           </Select>
         </Form.Item>

         <Form.Item name="limit" label="结果数量">
           <InputNumber min={10} max={100} defaultValue={50} />
         </Form.Item>

         <Form.Item>
           <Button type="primary" htmlType="submit">
             执行选股
           </Button>
         </Form.Item>
       </Form>
     )
   }
   ```

3. **创建股票表格组件**
   ```typescript
   // frontend/src/components/StockTable.tsx
   import { Table } from 'antd'
   import { Stock } from '@/types'

   export default function StockTable({ data, loading }: any) {
     const columns = [
       { title: '代码', dataIndex: 'stock_code', key: 'stock_code' },
       { title: '名称', dataIndex: 'stock_name', key: 'stock_name' },
       {
         title: '最新价',
         dataIndex: 'price',
         key: 'price',
         render: (val: number) => val.toFixed(2)
       },
       {
         title: '涨跌幅',
         dataIndex: 'pct_change',
         key: 'pct_change',
         render: (val: number) => (
           <span style={{ color: val > 0 ? 'red' : 'green' }}>
             {val > 0 ? '+' : ''}{val.toFixed(2)}%
           </span>
         )
       },
       { title: 'PE', dataIndex: 'pe', key: 'pe' },
       { title: 'PB', dataIndex: 'pb', key: 'pb' },
       {
         title: '市值(亿)',
         dataIndex: 'market_cap',
         key: 'market_cap',
         render: (val: number) => (val / 100000000).toFixed(2)
       }
     ]

     return (
       <Table
         columns={columns}
         dataSource={data}
         loading={loading}
         rowKey="stock_code"
         pagination={{ pageSize: 20 }}
       />
     )
   }
   ```

4. **创建选股页面**
   ```typescript
   // frontend/src/pages/StockPicker/index.tsx
   import { useState } from 'react'
   import { Card, message } from 'antd'
   import { useQuery } from '@tanstack/react-query'
   import StrategyForm from '@/components/StrategyForm'
   import StockTable from '@/components/StockTable'
   import { strategyApi } from '@/services/strategy'

   export default function StockPicker() {
     const [params, setParams] = useState<any>(null)

     const { data, isLoading } = useQuery({
       queryKey: ['stocks', params],
       queryFn: () => strategyApi.execute(params),
       enabled: !!params
     })

     const handleSubmit = async (values: any) => {
       setParams(values)
     }

     return (
       <div>
         <Card title="选股中心" style={{ marginBottom: 16 }}>
           <StrategyForm onSubmit={handleSubmit} />
         </Card>

         <Card title="选股结果">
           <StockTable data={data?.data || []} loading={isLoading} />
         </Card>
       </div>
     )
   }
   ```

5. **提交代码**
   ```bash
   git add frontend/src/
   git commit -m "feat: implement stock picker page"
   ```

---

### ⬜ Task 4: 个股分析页面
**状态**: 待开始
**文件**:
- 创建: `frontend/src/pages/StockAnalysis/index.tsx`
- 创建: `frontend/src/components/KLineChart.tsx`
- 创建: `frontend/src/components/AnalysisReport.tsx`
- 创建: `frontend/src/services/analysis.ts`

**步骤**:

1. **创建分析 API 服务**
   ```typescript
   // frontend/src/services/analysis.ts
   import api from './api'

   export const analysisApi = {
     analyze: (stockCode: string) =>
       api.post(`/stocks/${stockCode}/analyze`),

     getReport: (stockCode: string) =>
       api.get(`/stocks/${stockCode}/report`)
   }
   ```

2. **创建 K 线图组件**
   ```typescript
   // frontend/src/components/KLineChart.tsx
   import ReactECharts from 'echarts-for-react'

   export default function KLineChart({ data }: any) {
     const option = {
       title: { text: 'K线图' },
       tooltip: { trigger: 'axis' },
       xAxis: {
         type: 'category',
         data: data.map((d: any) => d.date)
       },
       yAxis: { type: 'value' },
       series: [
         {
           name: 'K线',
           type: 'candlestick',
           data: data.map((d: any) => [d.open, d.close, d.low, d.high])
         }
       ]
     }

     return <ReactECharts option={option} style={{ height: 400 }} />
   }
   ```

3. **创建分析报告组件**
   ```typescript
   // frontend/src/components/AnalysisReport.tsx
   import { Card, Descriptions, Tag, Progress } from 'antd'

   export default function AnalysisReport({ report }: any) {
     return (
       <div>
         <Card title="综合评分" style={{ marginBottom: 16 }}>
           <Progress
             type="circle"
             percent={report.overall_score * 10}
             format={() => `${report.overall_score.toFixed(1)}分`}
           />
           <Tag color={
             report.recommendation === 'buy' ? 'green' :
             report.recommendation === 'hold' ? 'blue' : 'red'
           }>
             {report.recommendation}
           </Tag>
         </Card>

         <Card title="基本面分析" style={{ marginBottom: 16 }}>
           <Descriptions column={2}>
             <Descriptions.Item label="评分">
               {report.fundamental.score.toFixed(1)}
             </Descriptions.Item>
           </Descriptions>
           <p>{report.fundamental.summary}</p>
         </Card>

         <Card title="技术面分析">
           <Descriptions column={2}>
             <Descriptions.Item label="评分">
               {report.technical.score.toFixed(1)}
             </Descriptions.Item>
             <Descriptions.Item label="趋势">
               {report.technical.trend}
             </Descriptions.Item>
           </Descriptions>
           <p>{report.technical.summary}</p>
         </Card>
       </div>
     )
   }
   ```

4. **创建分析页面**
   ```typescript
   // frontend/src/pages/StockAnalysis/index.tsx
   import { useParams } from 'react-router-dom'
   import { useQuery } from '@tanstack/react-query'
   import { Card, Spin } from 'antd'
   import KLineChart from '@/components/KLineChart'
   import AnalysisReport from '@/components/AnalysisReport'
   import { analysisApi } from '@/services/analysis'

   export default function StockAnalysis() {
     const { code } = useParams()

     const { data, isLoading } = useQuery({
       queryKey: ['analysis', code],
       queryFn: () => analysisApi.analyze(code!)
     })

     if (isLoading) return <Spin size="large" />

     return (
       <div>
         <Card title={`${data.stock_name} (${data.stock_code})`}>
           <KLineChart data={data.kline} />
         </Card>

         <AnalysisReport report={data} />
       </div>
     )
   }
   ```

5. **提交代码**
   ```bash
   git add frontend/src/
   git commit -m "feat: implement stock analysis page"
   ```

---

### ⬜ Task 5: 布局和导航
**状态**: 待开始
**文件**:
- 创建: `frontend/src/components/Layout/index.tsx`

**步骤**:

1. **创建布局组件**
   ```typescript
   // frontend/src/components/Layout/index.tsx
   import { Layout as AntLayout, Menu } from 'antd'
   import { Outlet, useNavigate } from 'react-router-dom'
   import {
     StockOutlined,
     BarChartOutlined,
     SettingOutlined
   } from '@ant-design/icons'

   const { Header, Content, Sider } = AntLayout

   export default function Layout() {
     const navigate = useNavigate()

     const menuItems = [
       { key: '/', icon: <StockOutlined />, label: '选股中心' },
       { key: '/market', icon: <BarChartOutlined />, label: '市场概览' },
       { key: '/strategy', icon: <SettingOutlined />, label: '我的策略' }
     ]

     return (
       <AntLayout style={{ minHeight: '100vh' }}>
         <Header style={{ color: 'white', fontSize: 20 }}>
           A股AI智能分析
         </Header>
         <AntLayout>
           <Sider width={200}>
             <Menu
               mode="inline"
               items={menuItems}
               onClick={({ key }) => navigate(key)}
             />
           </Sider>
           <Content style={{ padding: 24 }}>
             <Outlet />
           </Content>
         </AntLayout>
       </AntLayout>
     )
   }
   ```

2. **提交代码**
   ```bash
   git add frontend/src/components/Layout/
   git commit -m "feat: implement layout and navigation"
   ```

---

## 完成标准

Phase 5 完成后，前端应用应具备以下能力：

### 功能完整性
- ✅ React + TypeScript 项目初始化
- ✅ 路由和状态管理
- ✅ 选股中心页面
- ✅ 个股分析页面
- ✅ 布局和导航
- ✅ API 集成

### 质量标准
- ✅ TypeScript 类型完整
- ✅ 组件可复用
- ✅ 响应式设计

### 用户体验
- ✅ 界面美观
- ✅ 交互流畅
- ✅ 加载状态提示

---

## 下一步

完成 Phase 5 后，进入 **Phase 6: 用户认证与权限**

参考文档: `docs/tasks/phase-6-auth.md`
