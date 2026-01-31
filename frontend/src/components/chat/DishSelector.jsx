/**
 * DishSelector - Componente ottimizzato per selezione piatti su mobile
 *
 * Features:
 * - Tabs orizzontali per categorie (scroll touch-friendly)
 * - Chips/pills per selezione rapida
 * - Riepilogo sticky dei piatti selezionati
 * - Animazioni smooth
 */
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, X, ChefHat, Utensils } from 'lucide-react'
import { useTranslation } from 'react-i18next'

const DishSelector = ({
  menuItems = [],
  selectedDishes = [],
  onToggleDish,
  categoryLabels = {}
}) => {
  const { t } = useTranslation()
  const [activeCategory, setActiveCategory] = useState(null)
  const tabsRef = useRef(null)
  const contentRef = useRef(null)

  // Group menu items by category
  const groupedMenu = menuItems.reduce((acc, item) => {
    const cat = item.category || 'altro'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(item)
    return acc
  }, {})

  // Get categories that have items
  const availableCategories = Object.entries(categoryLabels)
    .filter(([key]) => groupedMenu[key]?.length > 0)

  // Auto-select first category on mount
  useEffect(() => {
    if (!activeCategory && availableCategories.length > 0) {
      setActiveCategory(availableCategories[0][0])
    }
  }, [availableCategories, activeCategory])

  // Scroll active tab into view
  useEffect(() => {
    if (tabsRef.current && activeCategory) {
      const activeTab = tabsRef.current.querySelector(`[data-category="${activeCategory}"]`)
      if (activeTab) {
        activeTab.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
      }
    }
  }, [activeCategory])

  const currentDishes = activeCategory ? (groupedMenu[activeCategory] || []) : []

  const removeDish = (dish, e) => {
    e.stopPropagation()
    onToggleDish(dish)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Selected dishes summary - Sticky top */}
      <AnimatePresence>
        {selectedDishes.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="sticky top-0 z-10 bg-burgundy-900/95 backdrop-blur-sm border-b border-gold-500/20 -mx-4 px-4 pb-3"
          >
            <div className="flex items-center gap-2 mb-2 pt-1">
              <Utensils className="w-4 h-4 text-gold-500" />
              <span className="text-sm font-medium text-gold-400">
                {t('customerChat:dishes.selected', { count: selectedDishes.length })}
              </span>
            </div>

            {/* Horizontal scroll for selected dishes */}
            <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-hide">
              {selectedDishes.map(dish => (
                <motion.div
                  key={dish.id}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  className="flex-shrink-0 flex items-center gap-1.5 bg-gold-500 text-burgundy-900
                             pl-3 pr-1.5 py-1.5 rounded-full text-sm font-medium"
                >
                  <span className="truncate max-w-[120px]">{dish.name}</span>
                  <button
                    onClick={(e) => removeDish(dish, e)}
                    className="w-5 h-5 rounded-full bg-burgundy-900/20 hover:bg-burgundy-900/40
                               flex items-center justify-center transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Category tabs - Horizontal scroll */}
      <div
        ref={tabsRef}
        className="flex gap-2 overflow-x-auto py-3 -mx-4 px-4 scrollbar-hide sticky top-0 z-10
                   bg-gradient-to-b from-burgundy-900 via-burgundy-900 to-transparent"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {availableCategories.map(([catKey, catLabel]) => {
          const isActive = activeCategory === catKey
          const count = groupedMenu[catKey]?.length || 0
          const selectedInCategory = selectedDishes.filter(
            d => (d.category || 'altro') === catKey
          ).length

          return (
            <button
              key={catKey}
              data-category={catKey}
              onClick={() => setActiveCategory(catKey)}
              className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all
                         flex items-center gap-2 ${
                isActive
                  ? 'bg-gold-500 text-burgundy-900 shadow-lg shadow-gold-500/25'
                  : 'bg-burgundy-800/70 text-cream-100 hover:bg-burgundy-700'
              }`}
            >
              {catLabel}
              <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                isActive
                  ? 'bg-burgundy-900/20'
                  : selectedInCategory > 0
                    ? 'bg-gold-500 text-burgundy-900'
                    : 'bg-burgundy-700'
              }`}>
                {selectedInCategory > 0 ? `${selectedInCategory}/${count}` : count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Dishes grid */}
      <div
        ref={contentRef}
        className="flex-1 overflow-y-auto -mx-4 px-4 pb-4"
        style={{
          scrollbarWidth: 'thin',
          WebkitOverflowScrolling: 'touch'
        }}
      >
        <motion.div
          key={activeCategory}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="grid grid-cols-2 gap-2 sm:grid-cols-3"
        >
          {currentDishes.map(dish => {
            const isSelected = selectedDishes.some(d => d.id === dish.id)

            return (
              <motion.button
                key={dish.id}
                onClick={() => onToggleDish(dish)}
                whileTap={{ scale: 0.95 }}
                className={`relative p-3 rounded-xl text-left transition-all
                           flex flex-col justify-between min-h-[80px] ${
                  isSelected
                    ? 'bg-gold-500 text-burgundy-900 ring-2 ring-gold-400 ring-offset-2 ring-offset-burgundy-900'
                    : 'bg-burgundy-800/60 text-cream-50 hover:bg-burgundy-700/80 active:bg-burgundy-700'
                }`}
              >
                {/* Selection indicator */}
                <div className={`absolute top-2 right-2 w-5 h-5 rounded-full
                                flex items-center justify-center transition-all ${
                  isSelected
                    ? 'bg-burgundy-900'
                    : 'border-2 border-cream-100/30'
                }`}>
                  {isSelected && <Check className="w-3 h-3 text-gold-500" />}
                </div>

                {/* Dish name */}
                <span className={`text-sm font-medium pr-6 line-clamp-2 ${
                  isSelected ? 'text-burgundy-900' : 'text-cream-50'
                }`}>
                  {dish.name}
                </span>

                {/* Price if available */}
                {dish.price && (
                  <span className={`text-xs mt-1 ${
                    isSelected ? 'text-burgundy-700' : 'text-gold-400'
                  }`}>
                    €{dish.price}
                  </span>
                )}
              </motion.button>
            )
          })}
        </motion.div>

        {/* Empty state */}
        {currentDishes.length === 0 && activeCategory && (
          <div className="text-center py-12">
            <ChefHat className="w-12 h-12 text-burgundy-600 mx-auto mb-4" />
            <p className="text-cream-100/50">
              {t('customerChat:dishes.emptyCategory')}
            </p>
          </div>
        )}
      </div>

      {/* Quick stats footer */}
      {menuItems.length > 0 && (
        <div className="pt-3 border-t border-burgundy-700/50 -mx-4 px-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-cream-100/50">
              {availableCategories.length} {t('customerChat:dishes.categoriesLabel')}
            </span>
            <span className="text-cream-100/50">
              {menuItems.length} {t('customerChat:dishes.totalDishes')}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default DishSelector
