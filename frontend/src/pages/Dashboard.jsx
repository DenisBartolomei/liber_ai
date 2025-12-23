import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Wine, 
  MessageSquare, 
  Users, 
  TrendingUp, 
  QrCode,
  ArrowUpRight,
  Package,
  Sparkles
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { analyticsService } from '../services/api'
import LoadingSpinner from '../components/ui/LoadingSpinner'

function Dashboard() {
  const { venue } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const response = await analyticsService.getDashboardStats()
      setStats(response.data)
    } catch (error) {
      console.error('Error loading stats:', error)
      // Set mock data for demo
      setStats({
        totalConversations: 127,
        totalProducts: 45,
        avgConversationLength: 4.2,
        topWines: [
          { name: 'Brunello di Montalcino 2018', count: 23 },
          { name: 'Barolo DOCG 2017', count: 19 },
          { name: 'Chianti Classico Riserva', count: 15 }
        ],
        recentActivity: [
          { type: 'conversation', message: 'Nuova conversazione completata', time: '2 min fa' },
          { type: 'product', message: 'Prodotto aggiornato: Amarone', time: '1 ora fa' },
          { type: 'suggestion', message: 'Nuovo suggerimento AI disponibile', time: '3 ore fa' }
        ]
      })
    } finally {
      setLoading(false)
    }
  }

  const statCards = [
    {
      label: 'Conversazioni Totali',
      value: stats?.totalConversations || 0,
      icon: MessageSquare,
      color: 'bg-burgundy-100 text-burgundy-900',
      trend: '+12%'
    },
    {
      label: 'Prodotti in Carta',
      value: stats?.totalProducts || 0,
      icon: Package,
      color: 'bg-gold-100 text-gold-700',
      trend: null
    },
    {
      label: 'Media Messaggi',
      value: typeof stats?.avgConversationLength === 'number' 
        ? stats.avgConversationLength.toFixed(1) 
        : (parseFloat(stats?.avgConversationLength) || 0).toFixed(1),
      icon: TrendingUp,
      color: 'bg-green-100 text-green-700',
      trend: '+5%'
    },
    {
      label: 'QR Code Scansioni',
      value: stats?.qrScans || '89',
      icon: QrCode,
      color: 'bg-purple-100 text-purple-700',
      trend: '+18%'
    }
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-burgundy-900">
            Bentornato! 👋
          </h1>
          <p className="text-burgundy-600 mt-1">
            Ecco come sta andando {venue?.name || 'il tuo ristorante'}
          </p>
        </div>
        <Link 
          to="/dashboard/chat" 
          className="btn-primary inline-flex items-center gap-2 self-start"
        >
          <Sparkles className="w-5 h-5" />
          Assistente AI
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="card"
          >
            <div className="flex items-start justify-between">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${stat.color}`}>
                <stat.icon className="w-6 h-6" />
              </div>
              {stat.trend && (
                <span className="text-sm text-green-600 font-medium flex items-center">
                  {stat.trend}
                  <ArrowUpRight className="w-4 h-4" />
                </span>
              )}
            </div>
            <div className="mt-4">
              <p className="text-3xl font-bold text-burgundy-900">{stat.value}</p>
              <p className="text-sm text-burgundy-500 mt-1">{stat.label}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Content Grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Top Wines */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-display text-xl font-semibold text-burgundy-900">
              Vini Più Richiesti
            </h2>
            <Link to="/dashboard/analytics" className="text-sm text-gold-600 hover:text-gold-700">
              Vedi tutti
            </Link>
          </div>
          <div className="space-y-4">
            {stats?.topWines?.map((wine, index) => (
              <div key={index} className="flex items-center gap-4">
                <div className="w-10 h-10 bg-burgundy-100 rounded-xl flex items-center justify-center">
                  <Wine className="w-5 h-5 text-burgundy-900" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-burgundy-900 truncate">{wine.name}</p>
                  <p className="text-sm text-burgundy-500">{wine.count} richieste</p>
                </div>
                <div className="w-20 h-2 bg-burgundy-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-burgundy-900 rounded-full"
                    style={{ width: `${(wine.count / stats.topWines[0].count) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card"
        >
          <h2 className="font-display text-xl font-semibold text-burgundy-900 mb-6">
            Attività Recenti
          </h2>
          <div className="space-y-4">
            {stats?.recentActivity?.map((activity, index) => (
              <div key={index} className="flex items-start gap-4 pb-4 border-b border-burgundy-100 last:border-0 last:pb-0">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  activity.type === 'conversation' ? 'bg-blue-100' :
                  activity.type === 'product' ? 'bg-gold-100' : 'bg-green-100'
                }`}>
                  {activity.type === 'conversation' && <MessageSquare className="w-5 h-5 text-blue-600" />}
                  {activity.type === 'product' && <Package className="w-5 h-5 text-gold-600" />}
                  {activity.type === 'suggestion' && <Sparkles className="w-5 h-5 text-green-600" />}
                </div>
                <div className="flex-1">
                  <p className="text-burgundy-900">{activity.message}</p>
                  <p className="text-sm text-burgundy-500">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="card bg-gradient-to-br from-burgundy-900 to-burgundy-800"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h2 className="font-display text-xl font-semibold text-cream-50 mb-2">
              Pronto a migliorare la tua carta vini?
            </h2>
            <p className="text-cream-100/80">
              Usa l'assistente AI per ricevere suggerimenti personalizzati sui vini da aggiungere
            </p>
          </div>
          <Link to="/dashboard/chat" className="btn-secondary flex-shrink-0">
            Chiedi all'AI
          </Link>
        </div>
      </motion.div>
    </div>
  )
}

export default Dashboard

