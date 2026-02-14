import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from '@/components/Layout'
import StockPicker from '@/pages/StockPicker'
import StockAnalysis from '@/pages/StockAnalysis'
import MyStrategy from '@/pages/MyStrategy'
import Market from '@/pages/Market'
import Disclaimer from '@/pages/Disclaimer'
import Terms from '@/pages/Terms'
import Privacy from '@/pages/Privacy'
import Watchlist from '@/pages/Watchlist'
import Login from '@/pages/Login'
import PrivateRoute from '@/components/PrivateRoute'
import RiskDisclaimerModal from '@/components/RiskDisclaimerModal'

function App() {
  return (
    <>
    <RiskDisclaimerModal />
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Layout />}>
        <Route index element={<StockPicker />} />
        <Route path="analysis/:code" element={<StockAnalysis />} />
        <Route path="strategy" element={<PrivateRoute><MyStrategy /></PrivateRoute>} />
        <Route path="market" element={<Market />} />
        <Route path="watchlist" element={<PrivateRoute><Watchlist /></PrivateRoute>} />
        <Route path="disclaimer" element={<Disclaimer />} />
        <Route path="terms" element={<Terms />} />
        <Route path="privacy" element={<Privacy />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
    </>
  )
}

export default App
