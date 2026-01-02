import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  BarChart3, 
  TrendingUp, 
  MessageSquare, 
  Wine,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  DollarSign,
  Users,
  Target,
  AlertCircle,
  Sparkles,
  PieChart,
  Activity,
  TrendingDown,
  Package
} from 'lucide-react'
import { analyticsService, api } from '../services/api'
import { useAuth } from '../context/AuthContext'
import LoadingSpinner from '../components/ui/LoadingSpinner'

// Budget Histogram Component
function BudgetHistogram({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-sm text-burgundy-500 text-center py-8">Nessun dato disponibile</p>
  }

  const maxCount = Math.max(...data.map(d => d.count || 0))
  const barHeight = 350 // Fixed height for bars area
  const paddingLeft = 50 // Space for y-axis labels
  const paddingRight = 20
  const paddingBottom = 60 // Space for x-axis labels
  const paddingTop = 30 // Space for count labels
  const gap = 12 // Gap between bars in pixels

  // Calculate bar width based on available space
  const totalBars = data.length
  const availableWidth = 1200 // Minimum width, will expand
  const barWidth = Math.max(60, (availableWidth - paddingLeft - paddingRight - (gap * (totalBars - 1))) / totalBars)
  const totalWidth = paddingLeft + (barWidth * totalBars) + (gap * (totalBars - 1)) + paddingRight

  return (
    <div className="w-full overflow-x-auto">
      <div className="min-w-full" style={{ minWidth: `${totalWidth}px` }}>
        <svg 
          width="100%" 
          height={barHeight + paddingTop + paddingBottom} 
          viewBox={`0 0 ${totalWidth} ${barHeight + paddingTop + paddingBottom}`}
          preserveAspectRatio="xMinYMin meet"
          className="w-full"
        >
          {/* Y-axis line */}
          <line
            x1={paddingLeft}
            y1={paddingTop}
            x2={paddingLeft}
            y2={barHeight + paddingTop}
            stroke="#722F37"
            strokeWidth="2"
          />

          {/* Y-axis labels and grid lines */}
          {[0, 1, 2, 3, 4, 5].map(tick => {
            const value = Math.round((maxCount / 5) * tick)
            const y = paddingTop + barHeight - (tick * (barHeight / 5))
            return (
              <g key={tick}>
                {/* Grid line */}
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={totalWidth - paddingRight}
                  y2={y}
                  stroke="#E5E7EB"
                  strokeWidth="1"
                  strokeDasharray="4,4"
                />
                {/* Y-axis label */}
                <text
                  x={paddingLeft - 10}
                  y={y + 4}
                  fill="#722F37"
                  fontSize="12"
                  fontWeight="500"
                  textAnchor="end"
                >
                  {value}
                </text>
              </g>
            )
          })}

          {/* Bars */}
          {data.map((item, index) => {
            const barHeightValue = maxCount > 0 ? (item.count / maxCount) * barHeight : 0
            const x = paddingLeft + index * (barWidth + gap)
            const y = paddingTop + barHeight - barHeightValue

            return (
              <g key={index}>
                {/* Bar */}
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={barHeightValue}
                  fill="#722F37"
                  rx="4"
                  className="hover:opacity-80 transition-opacity cursor-pointer"
                />
                {/* Count label on top of bar */}
                {barHeightValue > 20 && (
                  <text
                    x={x + barWidth / 2}
                    y={y - 8}
                    fill="#722F37"
                    fontSize="14"
                    fontWeight="bold"
                    textAnchor="middle"
                  >
                    {item.count}
                  </text>
                )}
                {/* Range label below bar */}
                <text
                  x={x + barWidth / 2}
                  y={barHeight + paddingTop + 20}
                  fill="#722F37"
                  fontSize="12"
                  fontWeight="500"
                  textAnchor="middle"
                >
                  {item.range}
                </text>
              </g>
            )
          })}

          {/* X-axis label */}
          <text
            x={totalWidth / 2}
            y={barHeight + paddingTop + 45}
            fill="#722F37"
            fontSize="14"
            fontWeight="600"
            textAnchor="middle"
          >
            Fascia di Budget (€)
          </text>

          {/* Y-axis label */}
          <text
            x={-barHeight / 2}
            y={15}
            fill="#722F37"
            fontSize="14"
            fontWeight="600"
            textAnchor="middle"
            transform={`rotate(-90, ${paddingLeft / 2}, ${(barHeight + paddingTop) / 2})`}
          >
            Numero di Richieste
          </text>
        </svg>
      </div>
    </div>
  )
}

// Pie Chart Component
function PieChartComponent({ data }) {
  if (!data || data.length === 0) return null
  
  const total = data.reduce((sum, d) => sum + (d.count || 0), 0)
  if (total === 0) return null

  const colors = ['#722F37', '#D4AF37', '#8B4513', '#A0522D', '#CD853F']
  const size = 200
  const radius = 80
  const center = size / 2
  let currentAngle = -90 // Start from top

  const segments = data.map((item, idx) => {
    const count = item.count || 0
    const percentage = (count / total) * 100
    const angle = (percentage / 100) * 360
    
    // Handle full circle (100%)
    if (angle >= 360) {
      return {
        path: `M ${center} ${center} m -${radius} 0 a ${radius} ${radius} 0 1 1 ${radius * 2} 0 a ${radius} ${radius} 0 1 1 -${radius * 2} 0`,
        color: colors[idx % colors.length],
        percentage,
        item
      }
    }
    
    const startAngle = currentAngle
    const endAngle = currentAngle + angle
    currentAngle = endAngle

    // Calculate path for pie slice
    const startRad = (startAngle * Math.PI) / 180
    const endRad = (endAngle * Math.PI) / 180
    
    const x1 = center + radius * Math.cos(startRad)
    const y1 = center + radius * Math.sin(startRad)
    const x2 = center + radius * Math.cos(endRad)
    const y2 = center + radius * Math.sin(endRad)
    
    const largeArc = angle > 180 ? 1 : 0
    
    const path = [
      `M ${center} ${center}`,
      `L ${x1} ${y1}`,
      `A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`,
      'Z'
    ].join(' ')

    return {
      path,
      color: colors[idx % colors.length],
      percentage,
      item
    }
  })

  return (
    <div className="flex justify-center items-center w-full min-h-[200px]">
      <svg 
        width={size} 
        height={size} 
        viewBox={`0 0 ${size} ${size}`} 
        className="flex-shrink-0"
        style={{ display: 'block' }}
      >
        {segments.map((segment, idx) => (
          <path
            key={idx}
            d={segment.path}
            fill={segment.color}
            stroke="#FFF8E7"
            strokeWidth="2"
            className="hover:opacity-80 transition-opacity cursor-pointer"
          />
        ))}
      </svg>
    </div>
  )
}

function DashboardAnalytics() {
  const { isPremium, venue, updateVenue } = useAuth()
  const [period, setPeriod] = useState('month')
  
  // FREE tier data
  const [overviewData, setOverviewData] = useState(null)
  const [operationalData, setOperationalData] = useState(null)
  const [loadingFree, setLoadingFree] = useState(true)
  const [errorFree, setErrorFree] = useState(null)
  
  // PREMIUM tier data
  const [customerIntelligence, setCustomerIntelligence] = useState(null)
  const [winePerformance, setWinePerformance] = useState(null)
  const [revenueData, setRevenueData] = useState(null)
  const [benchmark, setBenchmark] = useState(null)
  const [loadingPremium, setLoadingPremium] = useState(true)
  const [errorPremium, setErrorPremium] = useState(null)

  // Refresh venue data to get updated conversation count
  useEffect(() => {
    const refreshVenue = async () => {
      if (venue?.id) {
        try {
          const { venueService } = await import('../services/api')
          // Use the authenticated endpoint that includes stats
          const response = await api.get(`/venues/${venue.id}`)
          if (response.data && updateVenue) {
            updateVenue(response.data)
          }
        } catch (error) {
          console.error('[DashboardAnalytics] Error refreshing venue:', error)
        }
      }
    }
    refreshVenue()
  }, [venue?.id, updateVenue])

  useEffect(() => {
    loadFreeData()
    if (isPremium) {
      loadPremiumData()
    }
  }, [period, isPremium])

  const loadFreeData = async () => {
    setLoadingFree(true)
    setErrorFree(null)
    try {
      const params = { period }
      const [overview, operational] = await Promise.all([
        analyticsService.getOverview(params),
        analyticsService.getOperational(params)
      ])
      setOverviewData(overview.data)
      setOperationalData(operational.data)
    } catch (error) {
      console.error('Error loading free analytics:', error)
      setErrorFree(error.response?.data?.message || 'Errore nel caricamento dei dati')
    } finally {
      setLoadingFree(false)
    }
  }

  const loadPremiumData = async () => {
    setLoadingPremium(true)
    setErrorPremium(null)
    try {
      const params = { period }
      const [customer, wine, revenue, bench] = await Promise.all([
        analyticsService.getCustomerIntelligence(params).catch(err => {
          if (err.response?.status === 403) return { data: null, is403: true }
          throw err
        }),
        analyticsService.getWinePerformance(params).catch(err => {
          if (err.response?.status === 403) return { data: null, is403: true }
          throw err
        }),
        analyticsService.getRevenue(params).catch(err => {
          if (err.response?.status === 403) return { data: null, is403: true }
          throw err
        }),
        analyticsService.getBenchmark(params).catch(err => {
          if (err.response?.status === 403) return { data: null, is403: true }
          throw err
        })
      ])
      
      setCustomerIntelligence(customer.is403 ? null : customer.data)
      setWinePerformance(wine.is403 ? null : wine.data)
      setRevenueData(revenue.is403 ? null : revenue.data)
      setBenchmark(bench.is403 ? null : bench.data)
    } catch (error) {
      console.error('Error loading premium analytics:', error)
      setErrorPremium(error.response?.data?.message || 'Errore nel caricamento dei dati premium')
    } finally {
      setLoadingPremium(false)
    }
  }

  const periods = [
    { value: 'week', label: 'Settimana' },
    { value: 'month', label: 'Mese' },
    { value: 'quarter', label: 'Trimestre' },
    { value: 'year', label: 'Anno' }
  ]

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2
    }).format(value || 0)
  }

  return (
    <div className="space-y-8">
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

      {/* FREE TIER SECTION */}
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-burgundy-700 bg-burgundy-100 px-3 py-1 rounded-full">
            FREE
          </span>
          <h2 className="font-display text-2xl font-semibold text-burgundy-900">
            Panoramica e Monitoraggio
          </h2>
        </div>

        {loadingFree ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="lg" />
          </div>
        ) : errorFree ? (
          <div className="card bg-red-50 border-red-200">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="w-5 h-5" />
              <p>{errorFree}</p>
            </div>
          </div>
        ) : (
          <>
            {/* Annual Conversation Limit Card */}
            {venue?.annual_conversation_limit !== undefined && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="card mb-6"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                      <MessageSquare className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="font-display text-lg font-semibold text-burgundy-900">
                        Limite Conversazioni Annuali
                      </h3>
                      <p className="text-sm text-burgundy-600">
                        Utilizzo conversazioni B2C per anno solare
                      </p>
                    </div>
                  </div>
                </div>

                {venue.annual_conversation_limit !== null ? (
                  <>
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-burgundy-700">
                          {venue.annual_conversation_count || 0} / {venue.annual_conversation_limit}
                        </span>
                        <span className="text-sm font-semibold text-burgundy-900">
                          {Math.round(((venue.annual_conversation_count || 0) / venue.annual_conversation_limit) * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-burgundy-100 rounded-full h-3 overflow-hidden">
                        <div
                          className={`h-full transition-all duration-300 ${
                            (venue.annual_conversation_count || 0) >= venue.annual_conversation_limit
                              ? 'bg-red-500'
                              : (venue.annual_conversation_count || 0) >= venue.annual_conversation_limit * 0.8
                              ? 'bg-yellow-500'
                              : 'bg-green-500'
                          }`}
                          style={{
                            width: `${Math.min(100, ((venue.annual_conversation_count || 0) / venue.annual_conversation_limit) * 100)}%`
                          }}
                        />
                      </div>
                    </div>

                    <div className={`p-3 rounded-lg ${
                      (venue.annual_conversation_count || 0) >= venue.annual_conversation_limit
                        ? 'bg-red-50 border border-red-200'
                        : (venue.annual_conversation_count || 0) >= venue.annual_conversation_limit * 0.8
                        ? 'bg-yellow-50 border border-yellow-200'
                        : 'bg-green-50 border border-green-200'
                    }`}>
                      <div className="flex items-center gap-2">
                        {((venue.annual_conversation_count || 0) >= venue.annual_conversation_limit) ? (
                          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
                        ) : (venue.annual_conversation_count || 0) >= venue.annual_conversation_limit * 0.8 ? (
                          <AlertCircle className="w-4 h-4 text-yellow-600 flex-shrink-0" />
                        ) : (
                          <Target className="w-4 h-4 text-green-600 flex-shrink-0" />
                        )}
                        <p className={`text-sm font-medium ${
                          (venue.annual_conversation_count || 0) >= venue.annual_conversation_limit
                            ? 'text-red-900'
                            : (venue.annual_conversation_count || 0) >= venue.annual_conversation_limit * 0.8
                            ? 'text-yellow-900'
                            : 'text-green-900'
                        }`}>
                          {(venue.annual_conversation_count || 0) >= venue.annual_conversation_limit
                            ? 'Limite annuale raggiunto'
                            : (venue.annual_conversation_count || 0) >= venue.annual_conversation_limit * 0.8
                            ? 'Limite quasi raggiunto (80%+)'
                            : 'Stato normale'}
                        </p>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="p-4 bg-cream-50 rounded-lg border border-burgundy-200">
                    <p className="text-sm text-burgundy-600">
                      Conversazioni illimitate per questo locale
                    </p>
                  </div>
                )}
              </motion.div>
            )}

            {/* Overview Stats Cards */}
            {overviewData && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
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
                  <p className="text-3xl font-bold text-burgundy-900">
                    {overviewData.total_conversations || 0}
                  </p>
                  <p className="text-sm text-burgundy-500 mt-1">
                    {overviewData.total_selected_products || 0} bottiglie selezionate
                  </p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="card"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                      <Target className="w-5 h-5 text-green-600" />
                    </div>
                    <span className="text-sm text-burgundy-600">Tasso Selezione</span>
                  </div>
                  <p className="text-3xl font-bold text-burgundy-900">
                    {overviewData.selection_rate?.toFixed(1) || 0}%
                  </p>
                  <p className="text-sm text-burgundy-500 mt-1">
                    Conversazioni con vendita
                  </p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="card"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                      <DollarSign className="w-5 h-5 text-purple-600" />
                    </div>
                    <span className="text-sm text-burgundy-600">Valore Medio</span>
                  </div>
                  <p className="text-2xl font-bold text-burgundy-900">
                    {formatCurrency(overviewData.avg_bottle_value)}
                  </p>
                  <p className="text-sm text-burgundy-500 mt-1">
                    Per bottiglia selezionata
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
                      <TrendingUp className="w-5 h-5 text-orange-600" />
                    </div>
                    <span className="text-sm text-burgundy-600">Margine Medio</span>
                  </div>
                  <p className="text-2xl font-bold text-burgundy-900">
                    {formatCurrency(overviewData.avg_margin)}
                  </p>
                  <p className="text-sm text-burgundy-500 mt-1">
                    Per bottiglia
                  </p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="card"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-gold-100 rounded-xl flex items-center justify-center">
                      <Package className="w-5 h-5 text-gold-600" />
                    </div>
                    <span className="text-sm text-burgundy-600">Prodotti in Carta</span>
                  </div>
                  <p className="text-3xl font-bold text-burgundy-900">
                    {overviewData.total_products || 0}
                  </p>
                  <p className="text-sm text-burgundy-500 mt-1">
                    Vini nella carta
                  </p>
                </motion.div>
              </div>
            )}

            {/* Operational Monitoring */}
            {operationalData && (
              <div className="grid lg:grid-cols-2 gap-6">
                {/* Price Distribution - Pie Chart */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="card"
                >
                    <h3 className="font-display text-lg font-semibold text-burgundy-900 mb-4 flex items-center gap-2">
                      <PieChart className="w-5 h-5" />
                      Distribuzione prezzi vini scelti
                    </h3>
                  {operationalData.price_distribution && operationalData.price_distribution.length > 0 ? (
                    <div className="flex flex-col items-center gap-6 py-4">
                      {/* Pie Chart SVG */}
                      <div className="w-full flex justify-center">
                        <PieChartComponent data={operationalData.price_distribution} />
                      </div>
                      {/* Legend */}
                      <div className="w-full space-y-2">
                        {operationalData.price_distribution.map((item, idx) => {
                          const colors = ['#722F37', '#D4AF37', '#8B4513', '#A0522D', '#CD853F']
                          const total = operationalData.price_distribution.reduce((sum, d) => sum + d.count, 0)
                          const percentage = total > 0 ? ((item.count / total) * 100).toFixed(1) : 0
                          return (
                            <div key={idx} className="flex items-center justify-between text-sm">
                              <div className="flex items-center gap-2">
                                <div 
                                  className="w-4 h-4 rounded"
                                  style={{ backgroundColor: colors[idx % colors.length] }}
                                />
                                <span className="text-burgundy-700">{item.range}</span>
                              </div>
                              <div className="flex items-center gap-3">
                                <span className="text-burgundy-900 font-semibold">{item.count}</span>
                                <span className="text-burgundy-500 text-xs">({percentage}%)</span>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-burgundy-500 text-center py-8">Nessun dato disponibile</p>
                  )}
                </motion.div>

                {/* Wine Type Distribution */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                  className="card"
                >
                  <h3 className="font-display text-lg font-semibold text-burgundy-900 mb-4 flex items-center gap-2">
                    <Wine className="w-5 h-5" />
                    Distribuzione Tipi Vino
                  </h3>
                  <div className="space-y-3">
                    {operationalData.wine_type_distribution?.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between">
                        <span className="text-sm text-burgundy-700 capitalize">{item.type}</span>
                        <div className="flex items-center gap-3">
                          <div className="w-32 bg-burgundy-100 rounded-full h-2">
                            <div
                              className="bg-gold-500 h-2 rounded-full"
                              style={{
                                width: `${(item.count / Math.max(...(operationalData.wine_type_distribution || []).map(d => d.count))) * 100}%`
                              }}
                            />
                          </div>
                          <span className="text-sm font-semibold text-burgundy-900 w-8 text-right">
                            {item.count}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>

              </div>
            )}
          </>
        )}
      </div>

      {/* PREMIUM TIER SECTION */}
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-gold-700 bg-gold-100 px-3 py-1 rounded-full">
            PREMIUM
          </span>
          <h2 className="font-display text-2xl font-semibold text-burgundy-900">
            Intelligence Avanzata
          </h2>
        </div>

        {!isPremium ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card bg-gradient-to-br from-gold-50 to-burgundy-50 border-2 border-gold-300"
          >
            <div className="text-center py-8">
              <Sparkles className="w-16 h-16 text-gold-600 mx-auto mb-4" />
              <h3 className="font-display text-2xl font-bold text-burgundy-900 mb-2">
                Sblocca Analytics Premium
              </h3>
              <p className="text-burgundy-700 mb-6 max-w-2xl mx-auto">
                Passa a Premium per accedere a intelligence avanzata, analisi di performance dei vini,
                metriche di revenue e molto altro.
              </p>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div className="text-left">
                  <h4 className="font-semibold text-burgundy-900 mb-2">Customer Intelligence</h4>
                  <ul className="text-sm text-burgundy-700 space-y-1">
                    <li>• Elasticità dei prezzi</li>
                    <li>• Analisi preferenze</li>
                  </ul>
                </div>
                <div className="text-left">
                  <h4 className="font-semibold text-burgundy-900 mb-2">Wine Performance</h4>
                  <ul className="text-sm text-burgundy-700 space-y-1">
                    <li>• Conversion rate</li>
                    <li>• Vini bloccanti</li>
                  </ul>
                </div>
                <div className="text-left">
                  <h4 className="font-semibold text-burgundy-900 mb-2">Revenue Intelligence</h4>
                  <ul className="text-sm text-burgundy-700 space-y-1">
                    <li>• Extra vendita</li>
                    <li>• Margine perso</li>
                  </ul>
                </div>
                <div className="text-left">
                  <h4 className="font-semibold text-burgundy-900 mb-2">Benchmark</h4>
                  <ul className="text-sm text-burgundy-700 space-y-1">
                    <li>• Confronto settore</li>
                    <li>• Ranking percentile</li>
                  </ul>
                </div>
              </div>
              <button className="bg-gold-600 hover:bg-gold-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors">
                Passa a Premium
              </button>
            </div>
          </motion.div>
        ) : (
          <>
            {loadingPremium ? (
              <div className="flex items-center justify-center h-64">
                <LoadingSpinner size="lg" />
              </div>
            ) : errorPremium ? (
              <div className="card bg-red-50 border-red-200">
                <div className="flex items-center gap-2 text-red-700">
                  <AlertCircle className="w-5 h-5" />
                  <p>{errorPremium}</p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Budget Distribution Histogram - Full Width */}
                {customerIntelligence && customerIntelligence.budget_distribution && customerIntelligence.budget_distribution.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="card"
                  >
                    <h3 className="font-display text-lg font-semibold text-burgundy-900 mb-6 flex items-center gap-2">
                      <BarChart3 className="w-5 h-5" />
                      Distribuzione Richieste per Fascia di Budget
                    </h3>
                    <div className="w-full">
                      <BudgetHistogram data={customerIntelligence.budget_distribution} />
                    </div>
                  </motion.div>
                )}

                <div className="grid lg:grid-cols-2 gap-6">
                  {/* Customer Intelligence */}
                  {customerIntelligence && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="card"
                    >
                      <h3 className="font-display text-lg font-semibold text-burgundy-900 mb-4 flex items-center gap-2">
                        <Users className="w-5 h-5" />
                        Customer Intelligence
                      </h3>
                      <div className="space-y-4">
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-burgundy-700">Budget Medio Proposto</span>
                            <span className="text-lg font-bold text-burgundy-900">
                              {formatCurrency(customerIntelligence.avg_budget_initial)}
                            </span>
                          </div>
                          <p className="text-xs text-burgundy-500">
                            Budget medio iniziale dichiarato dai clienti (per bottiglia)
                          </p>
                        </div>
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-burgundy-700">Elasticità Prezzi</span>
                            <span className="text-lg font-bold text-burgundy-900">
                              {customerIntelligence.price_elasticity_rate?.toFixed(1)}%
                            </span>
                          </div>
                          <p className="text-xs text-burgundy-500">
                            % clienti che accettano vini sopra budget iniziale
                          </p>
                        </div>
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-burgundy-700">Delta Prezzo Medio</span>
                            <span className="text-lg font-bold text-burgundy-900">
                              {customerIntelligence.avg_price_delta_pct?.toFixed(1)}%
                            </span>
                          </div>
                          <p className="text-xs text-burgundy-500">
                            Differenza media tra prezzo selezionato e budget
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}

                {/* Revenue Intelligence */}
                {revenueData && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="card"
                  >
                    <h3 className="font-display text-lg font-semibold text-burgundy-900 mb-4 flex items-center gap-2">
                      <DollarSign className="w-5 h-5" />
                      Revenue Intelligence
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm text-burgundy-700">Margine Medio/Conversazione</span>
                          <span className="text-lg font-bold text-burgundy-900">
                            {formatCurrency(revenueData.avg_margin_per_conversation)}
                          </span>
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm text-burgundy-700">Extra Vendita</span>
                          <span className="text-lg font-bold text-green-600">
                            {formatCurrency(revenueData.extra_vendita)}
                          </span>
                        </div>
                        <p className="text-xs text-burgundy-500">
                          Ricavi derivanti da vini venduti oltre budget cliente
                        </p>
                      </div>
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm text-burgundy-700">Margine Perso Stimato</span>
                          <span className="text-lg font-bold text-red-600">
                            {formatCurrency(revenueData.estimated_lost_margin)}
                          </span>
                        </div>
                        <p className="text-xs text-burgundy-500">
                          {revenueData.sessions_without_selection || 0} conversazioni senza selezione
                        </p>
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* Wine Performance */}
                {winePerformance && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="card"
                  >
                    <h3 className="font-display text-lg font-semibold text-burgundy-900 mb-4 flex items-center gap-2">
                      <Activity className="w-5 h-5" />
                      Wine Performance
                    </h3>
                    {winePerformance.blocking_wines && winePerformance.blocking_wines.length > 0 ? (
                      <div>
                        <p className="text-sm text-burgundy-700 mb-3">Vini Bloccanti (alta proposta, bassa selezione):</p>
                        <div className="space-y-2">
                          {winePerformance.blocking_wines.slice(0, 5).map((wine) => (
                            <div key={wine.id} className="flex items-center justify-between py-2 border-b border-burgundy-50">
                              <span className="text-sm text-burgundy-900">{wine.name}</span>
                              <span className="text-xs text-red-600">
                                {wine.conversion_rate}% ({wine.selections}/{wine.proposals})
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-burgundy-500">Nessun vino bloccante identificato</p>
                    )}
                  </motion.div>
                )}

                {/* Vini Selezionati - Lista Completa */}
                {operationalData && operationalData.top_selected_wines && operationalData.top_selected_wines.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="card"
                  >
                    <h3 className="font-display text-lg font-semibold text-burgundy-900 mb-4 flex items-center gap-2">
                      <TrendingUp className="w-5 h-5" />
                      Vini Selezionati
                    </h3>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {operationalData.top_selected_wines.map((wine, idx) => (
                        <div key={wine.id} className="flex items-center justify-between py-2 border-b border-burgundy-50 last:border-0">
                          <div className="flex items-center gap-3">
                            <span className="w-6 h-6 bg-gold-100 rounded-full flex items-center justify-center text-xs font-bold text-gold-700">
                              {idx + 1}
                            </span>
                            <span className="text-sm text-burgundy-900">{wine.name}</span>
                          </div>
                          <span className="text-sm font-semibold text-burgundy-700">{wine.count}</span>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {/* Vini Proposti Non Selezionati - Lista Completa */}
                {operationalData && operationalData.top_proposed_not_selected && operationalData.top_proposed_not_selected.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="card"
                  >
                    <h3 className="font-display text-lg font-semibold text-burgundy-900 mb-4 flex items-center gap-2">
                      <AlertCircle className="w-5 h-5" />
                      Vini Proposti Non Selezionati
                    </h3>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {operationalData.top_proposed_not_selected.map((wine, idx) => (
                        <div key={wine.id} className="flex items-center justify-between py-2 border-b border-burgundy-50 last:border-0">
                          <div className="flex items-center gap-3">
                            <span className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center text-xs font-bold text-red-700">
                              {idx + 1}
                            </span>
                            <span className="text-sm text-burgundy-900">{wine.name}</span>
                          </div>
                          <span className="text-sm font-semibold text-red-600">{wine.proposed_not_selected}</span>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {/* Benchmark */}
                {benchmark && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="card lg:col-span-2"
                  >
                    <h3 className="font-display text-lg font-semibold text-burgundy-900 mb-4 flex items-center gap-2">
                      <BarChart3 className="w-5 h-5" />
                      Benchmark Comparison
                    </h3>
                    {benchmark.note ? (
                      <p className="text-sm text-burgundy-500">{benchmark.note}</p>
                    ) : (
                      <div className="grid md:grid-cols-3 gap-4">
                        <div>
                          <p className="text-sm text-burgundy-700 mb-2">Valore Bottiglia Medio</p>
                          <p className="text-2xl font-bold text-burgundy-900">
                            {formatCurrency(benchmark.venue_metrics?.avg_bottle_value)}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-burgundy-700 mb-2">Margine Medio</p>
                          <p className="text-2xl font-bold text-burgundy-900">
                            {formatCurrency(benchmark.venue_metrics?.avg_margin)}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-burgundy-700 mb-2">Tasso Selezione</p>
                          <p className="text-2xl font-bold text-burgundy-900">
                            {benchmark.venue_metrics?.selection_rate?.toFixed(1)}%
                          </p>
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default DashboardAnalytics
