import { motion, AnimatePresence } from 'framer-motion'
import { Wine, MapPin, Grape, Calendar, Euro, Check, Info } from 'lucide-react'
import { useState, useEffect } from 'react'
import WineIdentityCard from './WineIdentityCard'

function WineCard({ wine, expanded = false, selected = false, onClick, isMainRecommendation = null }) {
  // Use wine.best if provided, otherwise fall back to isMainRecommendation prop
  const isBest = isMainRecommendation !== null ? isMainRecommendation : (wine.best === true)
  const [showReason, setShowReason] = useState(false)
  const [showIdentityCard, setShowIdentityCard] = useState(false)

  // Lock body scroll when overlay is open
  useEffect(() => {
    if (showIdentityCard) {
      // Save current scroll position
      const scrollY = window.scrollY
      // Lock body scroll
      document.body.style.position = 'fixed'
      document.body.style.top = `-${scrollY}px`
      document.body.style.width = '100%'
      document.body.style.overflow = 'hidden'
      
      return () => {
        // Restore scroll position when closing
        document.body.style.position = ''
        document.body.style.top = ''
        document.body.style.width = ''
        document.body.style.overflow = ''
        window.scrollTo(0, scrollY)
      }
    }
  }, [showIdentityCard])
  const getWineBadgeClass = (type) => {
    switch (type?.toLowerCase()) {
      case 'red':
        return 'wine-badge-red'
      case 'white':
        return 'wine-badge-white'
      case 'rose':
        return 'wine-badge-rose'
      case 'sparkling':
        return 'wine-badge-sparkling'
      default:
        return 'wine-badge-red'
    }
  }

  const getWineTypeLabel = (type) => {
    switch (type?.toLowerCase()) {
      case 'red':
        return 'Rosso'
      case 'white':
        return 'Bianco'
      case 'rose':
        return 'Rosato'
      case 'sparkling':
        return 'Spumante'
      default:
        return type
    }
  }

  const cardClasses = onClick 
    ? `card-wine cursor-pointer transition-all ${
        selected 
          ? 'ring-2 ring-gold-500 shadow-lg bg-gold-50/50' 
          : 'hover:ring-2 hover:ring-gold-300 hover:shadow-md'
      }`
    : 'card-wine'

  return (
    <motion.div
      whileHover={onClick ? { scale: 1.01 } : {}}
      onClick={onClick}
      className={cardClasses}
    >
      <div className="flex gap-2 md:gap-4">
        {/* Wine Image or Icon */}
        <div className="w-12 h-12 md:w-14 md:h-14 rounded-xl flex items-center justify-center flex-shrink-0 overflow-hidden bg-burgundy-100">
          {(() => {
            const getImageUrl = () => {
              if (!wine.image_url) return null
              if (wine.image_url.startsWith('http')) return wine.image_url
              if (wine.image_url.startsWith('/')) return wine.image_url
              return `/${wine.image_url}`
            }
            const imageUrl = getImageUrl()
            
            if (imageUrl) {
              return (
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
              )
            }
            return null
          })()}
          <div className={`w-full h-full items-center justify-center ${wine.image_url ? 'hidden' : 'flex'}`}>
            <Wine className={`w-7 h-7 ${
              wine.type === 'white' ? 'text-amber-600' :
              wine.type === 'rose' ? 'text-pink-600' :
              wine.type === 'sparkling' ? 'text-yellow-600' :
              'text-burgundy-900'
            }`} />
          </div>
        </div>

        {/* Wine Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="font-display font-semibold text-burgundy-900 leading-tight">
                  {wine.name}
                </h3>
                {selected && (
                  <Check className="w-5 h-5 text-gold-600 flex-shrink-0" />
                )}
              </div>
              <div className="flex items-center gap-2 mt-1">
                {isBest && (
                  <span className="px-2 py-0.5 bg-gold-500 text-burgundy-900 rounded-full text-xs font-semibold">
                    Consiglio del Sommelier
                  </span>
                )}
                <span className={`${getWineBadgeClass(wine.type)} inline-block`}>
                  {getWineTypeLabel(wine.type)}
                </span>
                {(wine.reason || wine.color || wine.aromas || wine.body !== null || wine.acidity_level !== null) && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setShowIdentityCard(true)
                    }}
                    className="ml-auto p-1.5 text-burgundy-500 hover:text-burgundy-700 hover:bg-burgundy-50 rounded-lg transition-all"
                    title="Carta di identità del vino"
                  >
                    <Info className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
            {wine.price && (
              <div className="flex items-center text-gold-600 font-bold flex-shrink-0 ml-2">
                <Euro className="w-4 h-4" />
                <span className="truncate max-w-[80px] md:max-w-none">{wine.price}</span>
              </div>
            )}
          </div>

          {/* Details */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-burgundy-600">
            {wine.region && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5" />
                {wine.region}
              </span>
            )}
            {wine.grape_variety && (
              <span className="flex items-center gap-1">
                <Grape className="w-3.5 h-3.5" />
                {wine.grape_variety}
              </span>
            )}
            {wine.vintage && (
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                {wine.vintage}
              </span>
            )}
          </div>

          {/* Reason (why this wine is recommended) */}
          {(showReason || expanded) && wine.reason && (
            <div className="mt-3 p-3 bg-gold-50 border-l-4 border-gold-500 rounded-r">
              <p className="text-xs font-medium text-burgundy-700 uppercase tracking-wide mb-1">
                Perché questo vino
              </p>
              <p className="text-sm text-burgundy-700 leading-relaxed">
                {wine.reason}
              </p>
            </div>
          )}

          {/* Description */}
          {(expanded || wine.description) && wine.description && (
            <p className="mt-3 text-sm text-burgundy-700 leading-relaxed">
              {wine.description}
            </p>
          )}

          {/* Tasting Notes */}
          {expanded && wine.tasting_notes && (
            <div className="mt-3 pt-3 border-t border-burgundy-100">
              <p className="text-xs font-medium text-burgundy-500 uppercase tracking-wide mb-1">
                Note di Degustazione
              </p>
              <p className="text-sm text-burgundy-700">{wine.tasting_notes}</p>
            </div>
          )}

          {/* Food Pairings */}
          {expanded && wine.food_pairings && wine.food_pairings.length > 0 && (
            <div className="mt-3 pt-3 border-t border-burgundy-100">
              <p className="text-xs font-medium text-burgundy-500 uppercase tracking-wide mb-2">
                Abbinamenti
              </p>
              <div className="flex flex-wrap gap-2">
                {wine.food_pairings.map((pairing, idx) => (
                  <span 
                    key={idx}
                    className="px-2 py-1 bg-cream-100 text-burgundy-700 rounded-md text-xs"
                  >
                    {pairing}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Wine Identity Card Modal */}
      <AnimatePresence>
        {showIdentityCard && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowIdentityCard(false)}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100] flex items-center justify-center p-2 md:p-4 overflow-y-auto"
            >
              {/* Modal Content */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ type: "spring", damping: 25, stiffness: 300 }}
                onClick={(e) => e.stopPropagation()}
                className="w-full max-w-full md:max-w-4xl mx-2 md:mx-4"
              >
                <WineIdentityCard
                  wine={wine}
                  onClose={() => setShowIdentityCard(false)}
                />
              </motion.div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default WineCard

