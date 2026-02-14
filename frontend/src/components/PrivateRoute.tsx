import { Navigate, useLocation } from 'react-router-dom'

interface PrivateRouteProps {
  children: React.ReactNode
}

export default function PrivateRoute({ children }: PrivateRouteProps) {
  const location = useLocation()
  const token = localStorage.getItem('token')

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
