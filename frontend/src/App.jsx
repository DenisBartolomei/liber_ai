import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'

// Pages
import LandingPage from './pages/LandingPage'
import CustomerChat from './pages/CustomerChat'
import VenueMenu from './pages/VenueMenu'
import Login from './pages/Login'
import Register from './pages/Register'
import DashboardProducts from './pages/DashboardProducts'
import DashboardSettings from './pages/DashboardSettings'
import DashboardAnalytics from './pages/DashboardAnalytics'
import Onboarding from './pages/Onboarding'
import NotFound from './pages/NotFound'

// Layout
import DashboardLayout from './components/layout/DashboardLayout'
import ProtectedRoute from './components/auth/ProtectedRoute'

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* B2C Customer Routes (accessed via QR code) */}
        <Route path="/v/:venueSlug" element={<CustomerChat />} />
        <Route path="/v/:venueSlug/menu" element={<VenueMenu />} />
        
        {/* B2B Dashboard Routes (protected) */}
        <Route path="/onboarding" element={
          <ProtectedRoute>
            <Onboarding />
          </ProtectedRoute>
        } />
        
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }>
          <Route index element={<DashboardAnalytics />} />
          <Route path="products" element={<DashboardProducts />} />
          <Route path="analytics" element={<DashboardAnalytics />} />
          <Route path="settings" element={<DashboardSettings />} />
        </Route>
        
        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AuthProvider>
  )
}

export default App

