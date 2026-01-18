import { motion } from 'framer-motion'
import { X, Droplet, Sparkles, Activity, Droplets, MapPin, Grape, Calendar, Wine, Award, Utensils, Thermometer } from 'lucide-react'

function WineIdentityCard({ wine, onClose }) {
  // Get image URL - support both relative and absolute paths
  const getImageUrl = () => {
    if (!wine.image_url) return null
    if (wine.image_url.startsWith('http://') || wine.image_url.startsWith('https://')) {
      return wine.image_url
    }
    if (wine.image_url.startsWith('/')) {
      return wine.image_url
    }
    return `/${wine.image_url}`
  }

  const imageUrl = getImageUrl()
  
  // Parse aromas if it's a string
  const getAromasList = () => {
    if (!wine.aromas) return []
    if (Array.isArray(wine.aromas)) return wine.aromas
    if (typeof wine.aromas === 'string') {
      return wine.aromas.split(',').map(a => a.trim()).filter(a => a)
    }
    return []
  }

  // Parse food pairings
  const getFoodPairings = () => {
    if (!wine.food_pairings) return []
    if (Array.isArray(wine.food_pairings)) return wine.food_pairings
    if (typeof wine.food_pairings === 'string') {
      return wine.food_pairings.split(',').map(f => f.trim()).filter(f => f)
    }
    return []
  }

  const aromasList = getAromasList()
  const foodPairings = getFoodPairings()
  const isRedWine = wine.type?.toLowerCase() === 'red'
  const isWhiteWine = wine.type?.toLowerCase() === 'white'
  const isRoseWine = wine.type?.toLowerCase() === 'rose'
  const isSparklingWine = wine.type?.toLowerCase() === 'sparkling'
  
  // Dynamic gradient based on wine type
  const getHeaderGradient = () => {
    if (isRedWine) return 'from-red-900 via-burgundy-800 to-burgundy-900'
    if (isWhiteWine) return 'from-amber-600 via-yellow-700 to-amber-800'
    if (isRoseWine) return 'from-pink-600 via-rose-700 to-pink-800'
    if (isSparklingWine) return 'from-yellow-500 via-amber-600 to-yellow-700'
    return 'from-burgundy-900 via-burgundy-800 to-burgundy-700'
  }

  // Wine type label and icon color
  const getWineTypeInfo = () => {
    if (isRedWine) return { label: 'Rosso', iconColor: 'text-red-400', bgColor: 'bg-red-500/20' }
    if (isWhiteWine) return { label: 'Bianco', iconColor: 'text-amber-300', bgColor: 'bg-amber-500/20' }
    if (isRoseWine) return { label: 'Rosato', iconColor: 'text-pink-300', bgColor: 'bg-pink-500/20' }
    if (isSparklingWine) return { label: 'Spumante', iconColor: 'text-yellow-300', bgColor: 'bg-yellow-500/20' }
    return { label: wine.type, iconColor: 'text-white', bgColor: 'bg-white/20' }
  }

  const wineTypeInfo = getWineTypeInfo()

  // Progress bar component with animated fill
  const ProgressBar = ({ value, max = 10, label, color = 'bg-gold-500', icon: Icon }) => {
    if (value === null || value === undefined) return null
    const percentage = (value / max) * 100
    
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {Icon && <Icon className="w-4 h-4 text-burgundy-600" />}
            <span className="text-sm font-semibold text-burgundy-800">{label}</span>
          </div>
          <span className="text-xs font-bold text-burgundy-600 bg-burgundy-100 px-2 py-0.5 rounded-full">{value}/10</span>
        </div>
        <div className="w-full bg-burgundy-100 rounded-full h-3 overflow-hidden shadow-inner">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
            className={`h-full ${color} rounded-full relative`}
          >
            <div className="absolute inset-0 bg-white/20 rounded-full" />
          </motion.div>
        </div>
      </div>
    )
  }

  // Stat badge component
  const StatBadge = ({ icon: Icon, label, value, className = '' }) => {
    if (!value) return null
    return (
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className={`flex items-center gap-2 px-3 py-2 bg-white rounded-xl shadow-sm border border-burgundy-100 ${className}`}
      >
        <Icon className="w-4 h-4 text-burgundy-500 flex-shrink-0" />
        <div className="min-w-0">
          <p className="text-[10px] uppercase tracking-wide text-burgundy-400 font-medium">{label}</p>
          <p className="text-sm font-semibold text-burgundy-800 truncate">{value}</p>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: 20 }}
      transition={{ type: "spring", damping: 25, stiffness: 300 }}
      className="bg-white rounded-2xl md:rounded-3xl shadow-2xl overflow-hidden max-w-full md:max-w-5xl w-full max-h-[90vh] overflow-y-auto"
    >
      {/* Hero Header */}
      <div className={`relative bg-gradient-to-br ${getHeaderGradient()} overflow-hidden`}>
        {/* Decorative elements */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-white rounded-full translate-y-1/2 -translate-x-1/2" />
        </div>
        
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-10 h-10 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-full flex items-center justify-center transition-all hover:scale-110 z-10"
        >
          <X className="w-5 h-5 text-white" />
        </button>
        
        <div className="relative p-6 md:p-8 flex flex-col md:flex-row gap-6 items-center">
          {/* Wine Image */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="w-32 h-40 md:w-40 md:h-52 rounded-2xl bg-white/10 backdrop-blur-sm flex items-center justify-center overflow-hidden flex-shrink-0 shadow-2xl"
          >
            {imageUrl ? (
              <img
                src={imageUrl}
                alt={wine.name}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.style.display = 'none'
                  if (e.target.nextSibling) {
                    e.target.nextSibling.style.display = 'flex'
                  }
                }}
              />
            ) : null}
            <div className={`w-full h-full items-center justify-center flex-col gap-2 ${imageUrl ? 'hidden' : 'flex'}`}>
              <Wine className={`w-16 h-16 ${wineTypeInfo.iconColor}`} />
            </div>
          </motion.div>

          {/* Wine Info */}
          <div className="flex-1 text-center md:text-left min-w-0">
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="flex flex-wrap items-center justify-center md:justify-start gap-2 mb-3"
            >
              <span className={`px-3 py-1.5 ${wineTypeInfo.bgColor} backdrop-blur-sm text-white rounded-full text-sm font-bold`}>
                {wineTypeInfo.label}
              </span>
              {wine.vintage && (
                <span className="px-3 py-1.5 bg-white/20 backdrop-blur-sm text-white rounded-full text-sm font-medium">
                  🍇 {wine.vintage}
                </span>
              )}
              {wine.alcohol_content && (
                <span className="px-3 py-1.5 bg-white/20 backdrop-blur-sm text-white rounded-full text-sm font-medium">
                  {wine.alcohol_content}% vol
                </span>
              )}
            </motion.div>
            
            <motion.h2 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="text-2xl md:text-4xl font-display font-bold text-white mb-3 leading-tight"
            >
              {wine.name}
            </motion.h2>
            
            {(wine.producer || wine.region) && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="flex flex-wrap items-center justify-center md:justify-start gap-3 text-white/80"
              >
                {wine.producer && (
                  <span className="flex items-center gap-1.5 text-sm">
                    <Award className="w-4 h-4" />
                    {wine.producer}
                  </span>
                )}
                {wine.region && (
                  <span className="flex items-center gap-1.5 text-sm">
                    <MapPin className="w-4 h-4" />
                    {wine.region}
                  </span>
                )}
              </motion.div>
            )}
            
            {/* Price Badge */}
            {wine.price && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.6, type: "spring" }}
                className="mt-4 inline-flex items-center gap-1 px-4 py-2 bg-gold-500 text-burgundy-900 rounded-xl text-xl font-bold shadow-lg"
              >
                €{wine.price}
              </motion.div>
            )}
          </div>
        </div>
                </div>

      {/* Content */}
      <div className="p-6 md:p-8 space-y-6">
        
        {/* Motivation/Reason - Hero Section */}
        {wine.reason && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="relative bg-gradient-to-r from-gold-50 to-amber-50 rounded-2xl p-5 border-l-4 border-gold-500 shadow-sm"
          >
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-gold-500 rounded-full flex items-center justify-center flex-shrink-0 shadow-md">
                <Sparkles className="w-5 h-5 text-white" />
                </div>
              <div>
                <h3 className="text-sm font-bold text-burgundy-900 uppercase tracking-wide mb-2">
                  Perché questo vino per te
                </h3>
                <p className="text-burgundy-800 leading-relaxed">
                  {wine.reason}
                </p>
              </div>
            </div>
          </motion.div>
            )}

        {/* Description - Always Visible */}
        {wine.description && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-cream-50 rounded-2xl p-5 border border-burgundy-100"
          >
            <h3 className="text-sm font-bold text-burgundy-900 uppercase tracking-wide mb-3 flex items-center gap-2">
              <Wine className="w-4 h-4 text-burgundy-600" />
              Il Vino
            </h3>
            <p className="text-burgundy-700 leading-relaxed text-base">
              {wine.description}
            </p>
          </motion.div>
        )}

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatBadge icon={Grape} label="Vitigno" value={wine.grape_variety} />
          <StatBadge icon={MapPin} label="Regione" value={wine.region} />
          <StatBadge icon={Calendar} label="Annata" value={wine.vintage} />
          <StatBadge icon={Thermometer} label="Gradazione" value={wine.alcohol_content ? `${wine.alcohol_content}%` : null} />
        </div>

        {/* Sensory Profile */}
        {(wine.body !== null || wine.acidity_level !== null || (isRedWine && wine.tannin_level !== null)) && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-gradient-to-br from-burgundy-50 to-cream-50 rounded-2xl p-5 border border-burgundy-100"
          >
            <h3 className="text-sm font-bold text-burgundy-900 uppercase tracking-wide mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-burgundy-600" />
              Profilo Sensoriale
            </h3>
            <div className="space-y-4">
            {wine.body !== null && wine.body !== undefined && (
                <ProgressBar
                  value={wine.body}
                  label={wine.body <= 3 ? 'Corpo Leggero' : wine.body <= 6 ? 'Corpo Medio' : 'Corpo Pieno'}
                  color="bg-gradient-to-r from-gold-400 to-gold-600"
                  icon={Activity}
                />
            )}
            {wine.acidity_level !== null && wine.acidity_level !== undefined && (
                <ProgressBar
                  value={wine.acidity_level}
                  label={wine.acidity_level <= 3 ? 'Acidità Bassa' : wine.acidity_level <= 6 ? 'Acidità Media' : 'Acidità Vivace'}
                  color="bg-gradient-to-r from-green-400 to-emerald-600"
                  icon={Droplets}
                />
            )}
            {isRedWine && wine.tannin_level !== null && wine.tannin_level !== undefined && (
                <ProgressBar
                  value={wine.tannin_level}
                  label={wine.tannin_level <= 3 ? 'Tannini Morbidi' : wine.tannin_level <= 6 ? 'Tannini Medi' : 'Tannini Potenti'}
                  color="bg-gradient-to-r from-red-400 to-red-600"
                  icon={Activity}
                />
              )}
              </div>
          </motion.div>
            )}

        {/* Two Column: Aromas & Color */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Aromas */}
          {aromasList.length > 0 && (
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 }}
              className="bg-white rounded-2xl p-5 border border-burgundy-100 shadow-sm"
            >
              <h3 className="text-sm font-bold text-burgundy-900 uppercase tracking-wide mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-500" />
                Bouquet Aromatico
              </h3>
              <div className="flex flex-wrap gap-2">
                {aromasList.map((aroma, idx) => (
                  <motion.span
                    key={idx}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.7 + idx * 0.05 }}
                    className="px-3 py-1.5 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 text-burgundy-700 rounded-full text-sm font-medium"
                  >
                    {aroma}
                  </motion.span>
                ))}
              </div>
            </motion.div>
          )}

          {/* Color */}
          {wine.color && (
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 }}
              className="bg-white rounded-2xl p-5 border border-burgundy-100 shadow-sm"
            >
              <h3 className="text-sm font-bold text-burgundy-900 uppercase tracking-wide mb-3 flex items-center gap-2">
                <Droplet className="w-4 h-4 text-burgundy-500" />
                Aspetto Visivo
              </h3>
              <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold ${
                isRedWine ? 'bg-red-100 text-red-800 border border-red-200' :
                isWhiteWine ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                isRoseWine ? 'bg-pink-100 text-pink-800 border border-pink-200' :
                'bg-burgundy-100 text-burgundy-800 border border-burgundy-200'
              }`}>
                <div className={`w-4 h-4 rounded-full ${
                  isRedWine ? 'bg-red-600' :
                  isWhiteWine ? 'bg-amber-400' :
                  isRoseWine ? 'bg-pink-400' :
                  'bg-burgundy-600'
                }`} />
                {wine.color}
            </div>
            </motion.div>
          )}
            </div>

        {/* Tasting Notes */}
        {wine.tasting_notes && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="bg-gradient-to-r from-amber-50 to-yellow-50 rounded-2xl p-5 border border-amber-200"
          >
            <h3 className="text-sm font-bold text-burgundy-900 uppercase tracking-wide mb-3 flex items-center gap-2">
              <Wine className="w-4 h-4 text-amber-600" />
              Note di Degustazione
            </h3>
            <p className="text-burgundy-700 leading-relaxed italic">
              "{wine.tasting_notes}"
            </p>
          </motion.div>
        )}

        {/* Food Pairings */}
        {foodPairings.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-2xl p-5 border border-green-200"
          >
            <h3 className="text-sm font-bold text-burgundy-900 uppercase tracking-wide mb-3 flex items-center gap-2">
              <Utensils className="w-4 h-4 text-green-600" />
              Abbinamenti Consigliati
            </h3>
            <div className="flex flex-wrap gap-2">
              {foodPairings.map((pairing, idx) => (
                <motion.span
                  key={idx}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.9 + idx * 0.05 }}
                  className="px-3 py-1.5 bg-white border border-green-300 text-green-800 rounded-full text-sm font-medium shadow-sm"
                >
                  🍽️ {pairing}
                </motion.span>
              ))}
            </div>
          </motion.div>
          )}
      </div>
    </motion.div>
  )
}

export default WineIdentityCard
