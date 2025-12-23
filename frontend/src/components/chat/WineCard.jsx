import { motion } from 'framer-motion'
import { Wine, MapPin, Grape, Calendar, Euro, Check } from 'lucide-react'

function WineCard({ wine, expanded = false, selected = false, onClick, isMainRecommendation = false }) {
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
      <div className="flex gap-4">
        {/* Wine Icon */}
        <div className="w-14 h-14 bg-burgundy-100 rounded-xl flex items-center justify-center flex-shrink-0">
          <Wine className={`w-7 h-7 ${
            wine.type === 'white' ? 'text-amber-600' :
            wine.type === 'rose' ? 'text-pink-600' :
            wine.type === 'sparkling' ? 'text-yellow-600' :
            'text-burgundy-900'
          }`} />
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
                {isMainRecommendation && (
                  <span className="px-2 py-0.5 bg-gold-500 text-burgundy-900 rounded-full text-xs font-semibold">
                    Consiglio del Sommelier
                  </span>
                )}
                <span className={`${getWineBadgeClass(wine.type)} inline-block`}>
                  {getWineTypeLabel(wine.type)}
                </span>
              </div>
            </div>
            {wine.price && (
              <div className="flex items-center text-gold-600 font-bold whitespace-nowrap">
                <Euro className="w-4 h-4" />
                <span>{wine.price}</span>
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
    </motion.div>
  )
}

export default WineCard

