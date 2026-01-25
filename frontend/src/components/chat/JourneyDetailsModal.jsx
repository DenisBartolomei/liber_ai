import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import { useTranslation } from 'react-i18next'

function JourneyDetailsModal({ journey, isOpen, onClose }) {
  const { t } = useTranslation()
  if (!isOpen || !journey) return null

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
            className="fixed inset-0 bg-burgundy-900/50 backdrop-blur-sm z-50"
          />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-burgundy-200">
                <h3 className="font-display text-xl font-semibold text-burgundy-900">
                  {journey.name || t('customerChat:journey.detailsTitle')}
                </h3>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-burgundy-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-burgundy-600" />
                </button>
              </div>
              
              {/* Content */}
              <div className="p-6 overflow-y-auto flex-1">
                {(journey.reason || journey.description) && (
                  <div className="mb-6">
                    <h4 className="font-semibold text-burgundy-900 mb-2">{t('customerChat:journey.description')}</h4>
                    <p className="text-burgundy-700 leading-relaxed">
                      {journey.reason || journey.description}
                    </p>
                  </div>
                )}
                
                {journey.wines && journey.wines.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-burgundy-900 mb-3">{t('customerChat:journey.winesInJourney')}</h4>
                    <div className="space-y-3">
                      {journey.wines.map((wine, idx) => (
                        <div key={wine.id || idx} className="p-3 bg-cream-50 rounded-lg border border-burgundy-100">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h5 className="font-semibold text-burgundy-900">{wine.name}</h5>
                              {wine.type && (
                                <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium bg-burgundy-100 text-burgundy-700">
                                  {wine.type === 'red' ? t('customerChat:wineType.options.red.label') :
                                   wine.type === 'white' ? t('customerChat:wineType.options.white.label') :
                                   wine.type === 'rose' ? t('customerChat:wineType.options.rose.label') :
                                   wine.type === 'sparkling' ? t('customerChat:wineType.options.sparkling.label') : wine.type}
                                </span>
                              )}
                            </div>
                            {wine.price && (
                              <span className="text-gold-600 font-semibold ml-3">
                                €{parseFloat(wine.price).toFixed(2)}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              {/* Footer */}
              <div className="p-6 border-t border-burgundy-200">
                <button
                  onClick={onClose}
                  className="w-full px-4 py-2 bg-burgundy-900 text-cream-50 rounded-lg font-semibold hover:bg-burgundy-800 transition-colors"
                >
                  {t('common:buttons.close')}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default JourneyDetailsModal

