import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import LoadingSpinner from '../ui/LoadingSpinner'

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading, venue } = useAuth()
  const location = useLocation()

  console.log('[ProtectedRoute] Rendering...')
  console.log('[ProtectedRoute] isAuthenticated:', isAuthenticated)
  console.log('[ProtectedRoute] loading:', loading)
  console.log('[ProtectedRoute] venue:', venue)
  console.log('[ProtectedRoute] venue?.id:', venue?.id)

  if (loading) {
    console.log('[ProtectedRoute] Still loading, showing spinner')
    return (
      <div className="min-h-screen flex items-center justify-center bg-cream-50">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!isAuthenticated) {
    console.log('[ProtectedRoute] Not authenticated, redirecting to login')
    // Redirect to login, saving the attempted location
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  console.log('[ProtectedRoute] Authenticated, rendering children')
  return children
}

export default ProtectedRoute

