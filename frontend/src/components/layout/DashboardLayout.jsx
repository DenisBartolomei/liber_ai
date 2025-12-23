import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  LayoutDashboard, 
  Package, 
  MessageSquare, 
  BarChart3, 
  Settings,
  LogOut,
  Menu,
  X,
  ChevronRight
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import Logo from '../ui/Logo'

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { path: '/dashboard/products', icon: Package, label: 'Carta Vini' },
  { path: '/dashboard/chat', icon: MessageSquare, label: 'Assistente AI' },
  { path: '/dashboard/analytics', icon: BarChart3, label: 'Analytics' },
  { path: '/dashboard/settings', icon: Settings, label: 'Impostazioni' },
]

function DashboardLayout() {
  console.log('[DashboardLayout] Rendering...')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user, venue, logout } = useAuth()
  const navigate = useNavigate()
  
  console.log('[DashboardLayout] User:', user)
  console.log('[DashboardLayout] Venue:', venue)
  console.log('[DashboardLayout] Venue ID:', venue?.id)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-cream-50 flex">
      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-burgundy-900/50 backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-72 bg-burgundy-900 text-cream-50
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-burgundy-800">
            <div className="flex items-center gap-3">
              <Logo size="lg" className="rounded-xl" />
              <div>
                <h1 className="font-display text-xl font-bold">LIBER</h1>
                <p className="text-xs text-cream-100/70">Sommelier AI</p>
              </div>
            </div>
          </div>

          {/* Venue info */}
          {venue && (
            <div className="px-6 py-4 border-b border-burgundy-800">
              <p className="text-sm text-cream-100/70">Locale</p>
              <p className="font-semibold truncate">{venue.name}</p>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.end}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) => `
                  flex items-center gap-3 px-4 py-3 rounded-xl
                  transition-all duration-200 group
                  ${isActive 
                    ? 'bg-gold-500 text-burgundy-900 font-semibold shadow-gold' 
                    : 'text-cream-100 hover:bg-burgundy-800'
                  }
                `}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
                <ChevronRight className="w-4 h-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
              </NavLink>
            ))}
          </nav>

          {/* User section */}
          <div className="p-4 border-t border-burgundy-800">
            <div className="flex items-center gap-3 px-4 py-3">
              <div className="w-10 h-10 bg-burgundy-700 rounded-full flex items-center justify-center">
                <span className="text-sm font-bold">
                  {user?.email?.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user?.email}</p>
                <p className="text-xs text-cream-100/60 capitalize">{user?.role}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-3 mt-2 rounded-xl
                text-cream-100/80 hover:bg-burgundy-800 hover:text-cream-50
                transition-colors"
            >
              <LogOut className="w-5 h-5" />
              <span>Esci</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Mobile header */}
        <header className="lg:hidden bg-white border-b border-burgundy-100 px-4 py-3">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 text-burgundy-900 hover:bg-burgundy-50 rounded-lg"
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="flex items-center gap-2">
              <Logo size="md" />
              <span className="font-display font-bold text-burgundy-900">LIBER</span>
            </div>
            <div className="w-10" /> {/* Spacer */}
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-8 overflow-auto">
          <Outlet />
        </main>
      </div>

      {/* Mobile close button */}
      {sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(false)}
          className="fixed top-4 right-4 z-50 lg:hidden p-2 bg-cream-50 rounded-full shadow-lg"
        >
          <X className="w-6 h-6 text-burgundy-900" />
        </button>
      )}
    </div>
  )
}

export default DashboardLayout

