import { motion, AnimatePresence } from 'framer-motion'
import { X, Star } from 'lucide-react'
import WineCard from './WineCard'

function AllWinesModal({ isOpen, onClose, wines, onSelectWine, selectedWineId, isLoading = false }) {
  if (!isOpen) return null

  const getRankLabel = (wine) => {
    const rank = wine.rank || 1
    if (rank === 1) return '1° - Consiglio del Sommelier'
    if (rank === 2) return '2°'
    if (rank === 3) return '3°'
    return `${rank}°`
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-2 md:p-4 overflow-y-auto"
          >
            {/* Modal Content - Fullscreen */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full h-full max-w-full md:max-w-6xl max-h-[95vh] md:max-h-[90vh] bg-cream-50 rounded-xl md:rounded-2xl shadow-2xl flex flex-col overflow-hidden mx-0 md:mx-4"
            >
              {/* Header */}
              <div className="bg-gradient-to-r from-burgundy-900 to-burgundy-800 text-cream-50 px-4 md:px-6 py-3 md:py-4 flex items-center justify-between border-b border-burgundy-700">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gold-500 rounded-xl flex items-center justify-center">
                    <Star className="w-6 h-6 text-burgundy-900" />
                  </div>
                  <div>
                    <h2 className="font-display text-lg md:text-2xl font-bold">
                      Valuta tutti i vini
                    </h2>
                    <p className="text-xs md:text-sm text-cream-100/70">
                      {wines?.length || 0} vini disponibili per la tua selezione
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="w-10 h-10 rounded-full bg-burgundy-700 hover:bg-burgundy-600 flex items-center justify-center transition-colors"
                  aria-label="Chiudi"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content - Scrollable */}
              <div className="flex-1 overflow-y-auto p-3 md:p-6">
                {isLoading ? (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-burgundy-700 mb-4"></div>
                      <p className="text-burgundy-600">Caricamento vini...</p>
                    </div>
                  </div>
                ) : wines && wines.length > 0 ? (
                  <div className="space-y-4 overflow-x-hidden">
                    {wines.map((wine, index) => {
                      const rank = wine.rank || (index + 1)
                      const isSelected = selectedWineId === wine.id
                      
                      return (
                        <motion.div
                          key={wine.id || index}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className="relative overflow-x-hidden"
                        >
                          {/* Rank Badge - Inline on mobile, absolute on desktop */}
                          <div className="mb-2 md:absolute md:-top-2 md:-left-2 md:mb-0 z-10">
                            <div className={`inline-block px-2 md:px-3 py-1 rounded-full text-xs font-bold ${
                              rank === 1
                                ? 'bg-gold-500 text-burgundy-900'
                                : 'bg-burgundy-700 text-cream-50'
                            }`}>
                              {getRankLabel(wine)}
                            </div>
                          </div>

                          {/* Wine Card with Reason */}
                          <div
                            onClick={() => {
                              if (onSelectWine) {
                                onSelectWine(wine.id)
                              }
                            }}
                            className="cursor-pointer overflow-x-hidden"
                          >
                            <WineCard
                              wine={wine}
                              selected={isSelected}
                              isMainRecommendation={rank === 1}
                            />
                            
                            {/* Motivation/Reason */}
                            {wine.reason && (
                              <div className="mt-2 p-3 bg-burgundy-50 border-l-4 border-burgundy-300 rounded-r overflow-x-hidden">
                                <p className="text-xs font-medium text-burgundy-700 uppercase tracking-wide mb-1">
                                  Motivazione
                                </p>
                                <p className="text-sm text-burgundy-800 leading-relaxed break-words overflow-wrap-anywhere">
                                  {wine.reason}
                                </p>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-center">
                    <div>
                      <p className="text-burgundy-600 text-lg mb-2">
                        Nessun vino disponibile
                      </p>
                      <p className="text-burgundy-400 text-sm">
                        Non ci sono vini da mostrare
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="border-t border-burgundy-200 bg-cream-100 px-4 md:px-6 py-3 md:py-4">
                <p className="text-xs md:text-sm text-burgundy-600 text-center">
                  Clicca su un vino per selezionarlo
                </p>
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default AllWinesModal

