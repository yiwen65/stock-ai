import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from '@/components/Layout'
import StockPicker from '@/pages/StockPicker'
import StockAnalysis from '@/pages/StockAnalysis'
import MyStrategy from '@/pages/MyStrategy'
import Market from '@/pages/Market'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<StockPicker />} />
        <Route path="analysis/:code" element={<StockAnalysis />} />
        <Route path="strategy" element={<MyStrategy />} />
        <Route path="market" element={<Market />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
