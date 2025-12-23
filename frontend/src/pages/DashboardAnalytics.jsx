import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  BarChart3, 
  TrendingUp, 
  MessageSquare, 
  Wine,
  Calendar,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react'
import { analyticsService } from '../services/api'
import LoadingSpinner from '../components/ui/LoadingSpinner'

function DashboardAnalytics() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('week')

  useEffect(() => {
    loadStats()
  }, [period])

  const loadStats = async () => {
    setLoading(true)
    try {
      const response = await analyticsService.getConversationStats({ period })
      setStats(response.data)
    } catch (error) {
      // Demo data
      setStats({
        totalConversations: 347,
        avgMessagesPerConversation: 4.8,
        satisfactionRate: 92,
        peakHours: ['19:00', '20:00', '21:00'],
        topWines: [
          { name: 'Brunello di Montalcino 2018', requests: 45, trend: 12 },
          { name: 'Barolo DOCG 2017', requests: 38, trend: 8 },
          { name: 'Chianti Classico Riserva', requests: 32, trend: -3 },
          { name: 'Amarone della Valpolicella', requests: 28, trend: 15 },
          { name: 'Franciacorta Brut', requests: 25, trend: 5 }
        ],
        conversationsByDay: [
          { day: 'Lun', count: 42 },
          { day: 'Mar', count: 38 },
          { day: 'Mer', count: 51 },
          { day: 'Gio', count: 48 },
          { day: 'Ven', count: 67 },
          { day: 'Sab', count: 72 },
          { day: 'Dom', count: 29 }
        ],
        topQueries: [
          { query: 'Vino rosso corposo', count: 34 },
          { query: 'Abbinamento pesce', count: 28 },
          { query: 'Bollicine per aperitivo', count: 22 },
          { query: 'Vino biologico', count: 18 },
          { query: 'Dolce per dessert', count: 15 }
        ]
      })
    } finally {
      setLoading(false)
    }
  }

  const periods = [
    { value: 'week', label: 'Settimana' },
    { value: 'month', label: 'Mese' },
    { value: 'quarter', label: 'Trimestre' }
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const maxConversations = Math.max(...(stats?.conversationsByDay || []).map(d => d.count))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-burgundy-900 flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-gold-500" />
            Analytics
          </h1>
          <p className="text-burgundy-600 mt-1">
            Monitora le performance del tuo sommelier AI
          </p>
        </div>
        <div className="flex gap-2">
          {periods.map(p => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                period === p.value
                  ? 'bg-burgundy-900 text-cream-50'
                  : 'bg-white text-burgundy-700 hover:bg-burgundy-100'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-blue-600" />
            </div>
            <span className="text-sm text-burgundy-600">Conversazioni</span>
          </div>
          <p className="text-3xl font-bold text-burgundy-900">{stats?.totalConversations}</p>
          <p className="text-sm text-green-600 flex items-center mt-1">
            <ArrowUpRight className="w-4 h-4" />
            +18% vs periodo precedente
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-purple-600" />
            </div>
            <span className="text-sm text-burgundy-600">Media Messaggi</span>
          </div>
          <p className="text-3xl font-bold text-burgundy-900">{stats?.avgMessagesPerConversation}</p>
          <p className="text-sm text-green-600 flex items-center mt-1">
            <ArrowUpRight className="w-4 h-4" />
            +5% engagement
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
              <Wine className="w-5 h-5 text-green-600" />
            </div>
            <span className="text-sm text-burgundy-600">Soddisfazione</span>
          </div>
          <p className="text-3xl font-bold text-burgundy-900">{stats?.satisfactionRate}%</p>
          <p className="text-sm text-burgundy-500 mt-1">
            Feedback positivi
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center">
              <Calendar className="w-5 h-5 text-orange-600" />
            </div>
            <span className="text-sm text-burgundy-600">Orari di Punta</span>
          </div>
          <p className="text-xl font-bold text-burgundy-900">{stats?.peakHours?.join(', ')}</p>
          <p className="text-sm text-burgundy-500 mt-1">
            Maggiore attività
          </p>
        </motion.div>
      </div>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-1 gap-6">
        {/* Conversations by Day */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card"
        >
          <h2 className="font-display text-lg font-semibold text-burgundy-900 mb-6">
            Conversazioni per Giorno
          </h2>
          <div className="flex items-end justify-between h-48 gap-2">
            {stats?.conversationsByDay?.map((day, idx) => (
              <div key={day.day} className="flex-1 flex flex-col items-center gap-2">
                <div 
                  className="w-full bg-burgundy-200 rounded-t-lg transition-all hover:bg-burgundy-300"
                  style={{ height: `${(day.count / maxConversations) * 100}%` }}
                >
                  <div 
                    className="w-full bg-burgundy-900 rounded-t-lg"
                    style={{ height: '100%' }}
                  />
                </div>
                <span className="text-xs text-burgundy-600">{day.day}</span>
                <span className="text-xs font-medium text-burgundy-900">{day.count}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Top Wines Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="card"
      >
        <h2 className="font-display text-lg font-semibold text-burgundy-900 mb-6">
          Vini Più Richiesti
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-burgundy-100">
                <th className="text-left py-3 px-4 text-sm font-semibold text-burgundy-700">Posizione</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-burgundy-700">Vino</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-burgundy-700">Richieste</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-burgundy-700">Trend</th>
              </tr>
            </thead>
            <tbody>
              {stats?.topWines?.map((wine, idx) => (
                <tr key={idx} className="border-b border-burgundy-50">
                  <td className="py-3 px-4">
                    <span className="w-8 h-8 bg-gold-100 rounded-full flex items-center justify-center text-sm font-bold text-gold-700">
                      {idx + 1}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-3">
                      <Wine className="w-5 h-5 text-burgundy-400" />
                      <span className="font-medium text-burgundy-900">{wine.name}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-burgundy-700">{wine.requests}</td>
                  <td className="py-3 px-4">
                    <span className={`flex items-center text-sm font-medium ${
                      wine.trend > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {wine.trend > 0 ? (
                        <ArrowUpRight className="w-4 h-4" />
                      ) : (
                        <ArrowDownRight className="w-4 h-4" />
                      )}
                      {Math.abs(wine.trend)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  )
}

export default DashboardAnalytics

