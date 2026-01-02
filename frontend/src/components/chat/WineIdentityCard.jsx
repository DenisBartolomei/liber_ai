import { motion } from 'framer-motion'
import { X, Droplet, Sparkles, Activity, Droplets } from 'lucide-react'

function WineIdentityCard({ wine, onClose }) {
  // Get image URL - support both relative and absolute paths
  const getImageUrl = () => {
    if (!wine.image_url) return null
    if (wine.image_url.startsWith('http')) return wine.image_url
    if (wine.image_url.startsWith('/')) return wine.image_url
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

  const aromasList = getAromasList()
  const isRedWine = wine.type?.toLowerCase() === 'red'
  
  // Helper to get color badge style based on wine color description
  const getColorBadgeStyle = (colorText) => {
    if (!colorText) return 'bg-gray-200 text-gray-700'
    const colorLower = colorText.toLowerCase()
    if (colorLower.includes('rosso') || colorLower.includes('rubino') || colorLower.includes('rosso')) {
      return 'bg-red-600 text-white'
    } else if (colorLower.includes('giallo') || colorLower.includes('paglierino') || colorLower.includes('dorato')) {
      return 'bg-yellow-400 text-yellow-900'
    } else if (colorLower.includes('rosa') || colorLower.includes('rosato') || colorLower.includes('salmon')) {
      return 'bg-pink-400 text-pink-900'
    } else if (colorLower.includes('ambra') || colorLower.includes('oro')) {
      return 'bg-amber-500 text-amber-900'
    }
    return 'bg-burgundy-200 text-burgundy-900'
  }

  // Progress bar component
  const ProgressBar = ({ value, max = 10, label, color = 'bg-gold-500' }) => {
    if (value === null || value === undefined) return null
    
    const percentage = (value / max) * 100
    
    return (
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-burgundy-700">{label}</span>
          <span className="text-xs text-burgundy-500">{value}/{max}</span>
        </div>
        <div className="w-full bg-burgundy-100 rounded-full h-2.5 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className={`h-full ${color} rounded-full`}
          />
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="bg-white rounded-xl md:rounded-2xl shadow-2xl overflow-hidden max-w-full md:max-w-4xl w-full"
    >
      {/* Header with close button */}
      <div className="relative bg-gradient-to-br from-burgundy-900 to-burgundy-700 p-4 md:p-6 overflow-x-hidden">
        <button
          onClick={onClose}
          className="absolute top-3 md:top-4 right-3 md:right-4 w-8 h-8 md:w-10 md:h-10 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center transition-colors flex-shrink-0 z-10"
        >
          <X className="w-4 h-4 md:w-5 md:h-5 text-white" />
        </button>
        
        <div className="pr-10 md:pr-12 min-w-0">
          <h2 className="text-xl md:text-3xl font-display font-bold text-white mb-2 break-words overflow-wrap-anywhere">
            {wine.name}
          </h2>
          <div className="flex items-center gap-2 md:gap-3 flex-wrap">
            <span className="px-2 md:px-3 py-1 bg-white/20 backdrop-blur-sm text-white rounded-full text-xs md:text-sm font-medium break-words">
              {wine.type === 'red' ? 'Rosso' : 
               wine.type === 'white' ? 'Bianco' : 
               wine.type === 'rose' ? 'Rosato' : 
               wine.type === 'sparkling' ? 'Spumante' : wine.type}
            </span>
            {wine.vintage && (
              <span className="px-2 md:px-3 py-1 bg-white/20 backdrop-blur-sm text-white rounded-full text-xs md:text-sm break-words">
                {wine.vintage}
              </span>
            )}
            {wine.price && (
              <span className="px-2 md:px-3 py-1 bg-gold-500 text-burgundy-900 rounded-full text-xs md:text-sm font-bold break-words">
                €{wine.price}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Motivation/Reason Section */}
      {wine.reason && (
        <div className="px-4 md:px-6 pt-4 md:pt-6 pb-0 overflow-x-hidden">
          <div className="bg-gold-50 border-l-4 border-gold-500 rounded-r-lg p-3 md:p-4">
            <h3 className="text-xs md:text-sm font-semibold text-burgundy-900 uppercase tracking-wide mb-2">
              Motivazione
            </h3>
            <p className="text-sm md:text-base text-burgundy-800 leading-relaxed break-words overflow-wrap-anywhere">
              {wine.reason}
            </p>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-4 md:p-6 overflow-x-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
          {/* Left: Bottle Image */}
          <div className="flex items-center justify-center bg-gradient-to-br from-cream-50 to-burgundy-50 rounded-lg md:rounded-xl p-4 md:p-8 min-h-[300px] md:min-h-[400px] overflow-x-hidden">
            {imageUrl ? (
              <img
                src={imageUrl}
                alt={wine.name}
                className="max-w-full max-h-[500px] object-contain drop-shadow-2xl"
                onError={(e) => {
                  e.target.style.display = 'none'
                  if (e.target.nextSibling) {
                    e.target.nextSibling.style.display = 'flex'
                  }
                }}
              />
            ) : null}
            <div className={`w-full h-full items-center justify-center ${imageUrl ? 'hidden' : 'flex'}`}>
              <div className="text-center">
                <Droplet className="w-24 h-24 text-burgundy-300 mx-auto mb-4" />
                <p className="text-burgundy-500 text-sm">Immagine non disponibile</p>
              </div>
            </div>
          </div>

          {/* Right: Structured Data */}
          <div className="space-y-4 md:space-y-6 overflow-x-hidden">
            {/* Color */}
            {wine.color && (
              <div className="bg-cream-50 rounded-xl p-3 md:p-4 border border-burgundy-100 overflow-x-hidden">
                <div className="flex items-center gap-2 mb-2">
                  <Droplet className="w-4 h-4 md:w-5 md:h-5 text-burgundy-600 flex-shrink-0" />
                  <h3 className="font-semibold text-burgundy-900 text-sm md:text-base break-words">Colore</h3>
                </div>
                <span className={`inline-block px-2 md:px-3 py-1 md:py-1.5 rounded-lg text-xs md:text-sm font-medium break-words ${getColorBadgeStyle(wine.color)}`}>
                  {wine.color}
                </span>
              </div>
            )}

            {/* Aromas */}
            {aromasList.length > 0 && (
              <div className="bg-cream-50 rounded-xl p-3 md:p-4 border border-burgundy-100 overflow-x-hidden">
                <div className="flex items-center gap-2 mb-2 md:mb-3">
                  <Sparkles className="w-4 h-4 md:w-5 md:h-5 text-burgundy-600 flex-shrink-0" />
                  <h3 className="font-semibold text-burgundy-900 text-sm md:text-base break-words">Aromi</h3>
                </div>
                <div className="flex flex-wrap gap-1.5 md:gap-2">
                  {aromasList.map((aroma, idx) => (
                    <span
                      key={idx}
                      className="px-2 md:px-3 py-1 md:py-1.5 bg-white border border-burgundy-200 text-burgundy-700 rounded-md md:rounded-lg text-xs md:text-sm font-medium break-words"
                    >
                      {aroma}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Body */}
            {wine.body !== null && wine.body !== undefined && (
              <div className="bg-cream-50 rounded-xl p-3 md:p-4 border border-burgundy-100 overflow-x-hidden">
                <div className="flex items-center gap-2 mb-2 md:mb-3">
                  <Activity className="w-4 h-4 md:w-5 md:h-5 text-gold-600 flex-shrink-0" />
                  <h3 className="font-semibold text-burgundy-900 text-sm md:text-base break-words">Corpo</h3>
                </div>
                <ProgressBar
                  value={wine.body}
                  label={`${wine.body <= 3 ? 'Leggero' : wine.body <= 6 ? 'Medio' : 'Pieno'}`}
                  color="bg-gold-500"
                />
              </div>
            )}

            {/* Acidity */}
            {wine.acidity_level !== null && wine.acidity_level !== undefined && (
              <div className="bg-cream-50 rounded-xl p-3 md:p-4 border border-burgundy-100 overflow-x-hidden">
                <div className="flex items-center gap-2 mb-2 md:mb-3">
                  <Droplets className="w-4 h-4 md:w-5 md:h-5 text-green-600 flex-shrink-0" />
                  <h3 className="font-semibold text-burgundy-900 text-sm md:text-base break-words">Acidità</h3>
                </div>
                <ProgressBar
                  value={wine.acidity_level}
                  label={`${wine.acidity_level <= 3 ? 'Bassa' : wine.acidity_level <= 6 ? 'Media' : 'Alta'}`}
                  color="bg-green-500"
                />
              </div>
            )}

            {/* Tannins (only for red wines) */}
            {isRedWine && wine.tannin_level !== null && wine.tannin_level !== undefined && (
              <div className="bg-cream-50 rounded-xl p-3 md:p-4 border border-burgundy-100 overflow-x-hidden">
                <div className="flex items-center gap-2 mb-2 md:mb-3">
                  <Activity className="w-4 h-4 md:w-5 md:h-5 text-red-600 flex-shrink-0" />
                  <h3 className="font-semibold text-burgundy-900 text-sm md:text-base break-words">Tannini</h3>
                </div>
                <ProgressBar
                  value={wine.tannin_level}
                  label={`${wine.tannin_level <= 3 ? 'Morbidi' : wine.tannin_level <= 6 ? 'Medi' : 'Potenti'}`}
                  color="bg-red-500"
                />
              </div>
            )}

            {/* Fallback: Description if structured data not available */}
            {!wine.color && !aromasList.length && wine.body === null && wine.acidity_level === null && wine.description && (
              <div className="bg-cream-50 rounded-xl p-3 md:p-4 border border-burgundy-100 overflow-x-hidden">
                <h3 className="font-semibold text-burgundy-900 mb-2 text-sm md:text-base break-words">Descrizione</h3>
                <p className="text-burgundy-700 text-xs md:text-sm leading-relaxed whitespace-pre-wrap break-words overflow-wrap-anywhere">
                  {wine.description}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Additional Info */}
        <div className="mt-4 md:mt-6 pt-4 md:pt-6 border-t border-burgundy-100 grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 text-xs md:text-sm overflow-x-hidden">
          {wine.region && (
            <div className="overflow-x-hidden">
              <span className="text-burgundy-500 font-medium">Regione</span>
              <p className="text-burgundy-700 break-words overflow-wrap-anywhere">{wine.region}</p>
            </div>
          )}
          {wine.grape_variety && (
            <div className="overflow-x-hidden">
              <span className="text-burgundy-500 font-medium">Vitigno</span>
              <p className="text-burgundy-700 break-words overflow-wrap-anywhere">{wine.grape_variety}</p>
            </div>
          )}
          {wine.producer && (
            <div className="overflow-x-hidden">
              <span className="text-burgundy-500 font-medium">Produttore</span>
              <p className="text-burgundy-700 break-words overflow-wrap-anywhere">{wine.producer}</p>
            </div>
          )}
          {wine.alcohol_content && (
            <div className="overflow-x-hidden">
              <span className="text-burgundy-500 font-medium">Gradazione</span>
              <p className="text-burgundy-700 break-words overflow-wrap-anywhere">{wine.alcohol_content}%</p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export default WineIdentityCard

