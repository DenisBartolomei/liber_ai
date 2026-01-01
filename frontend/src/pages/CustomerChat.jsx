import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Wine, 
  Send, 
  Sparkles, 
  RefreshCw,
  Users,
  ChevronDown,
  Check,
  X,
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  Search,
  Star
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { venueService, menuService, chatService } from '../services/api'
import { useChat } from '../hooks/useChat'
import { ThinkingMessages } from '../components/ui/LoadingSpinner'
import WineCard from '../components/chat/WineCard'
import AllWinesModal from '../components/chat/AllWinesModal'
import Logo from '../components/ui/Logo'

// Category labels for display
const categoryLabels = {
  'antipasto': 'Antipasti',
  'primo': 'Primi Piatti',
  'secondo': 'Secondi Piatti',
  'contorno': 'Contorni',
  'dolce': 'Dolci',
  'altro': 'Altro'
}

// Wine type options
const wineTypeOptions = [
  { id: 'red', label: 'Rosso', icon: '🍷', description: 'Vini corposi e strutturati' },
  { id: 'white', label: 'Bianco', icon: '🥂', description: 'Vini freschi e aromatici' },
  { id: 'sparkling', label: 'Bollicine', icon: '🍾', description: 'Spumanti e Champagne' },
  { id: 'rose', label: 'Rosato', icon: '🌸', description: 'Vini leggeri e versatili' },
  { id: 'any', label: 'Lascia fare a te', icon: '✨', description: 'Mi affido al sommelier' }
]

// Journey options
const journeyOptions = [
  { id: 'single', label: 'Una sola etichetta', icon: '🍷', description: 'Un vino che accompagni tutta la cena' },
  { id: 'journey', label: 'Percorso di vini', icon: '🗺️', description: 'Più vini scelti per ogni portata' }
]

// Budget: now handled as number input + "Nessuna restrizione" button

// Calculate bottles needed (same logic as backend)
function calculateBottlesNeeded(guestCount, coursesPerPerson = 2.0) {
  const glassesPerPersonPerCourse = 1.5
  const glassesPerBottle = 6.0
  
  // Total glasses needed
  const totalGlasses = guestCount * coursesPerPerson * glassesPerPersonPerCourse
  
  // Bottles needed (with decimal)
  const bottlesDecimal = totalGlasses / glassesPerBottle
  
  // Rounding: if decimal part > 0.5, round up, else round down
  const decimalPart = bottlesDecimal - Math.floor(bottlesDecimal)
  
  if (decimalPart > 0.5) {
    return Math.ceil(bottlesDecimal)
  } else {
    return Math.floor(bottlesDecimal)
  }
}

function CustomerChat() {
  const { venueSlug } = useParams()
  const [venue, setVenue] = useState(null)
  const [menuItems, setMenuItems] = useState([])
  const [venueLoading, setVenueLoading] = useState(true)
  const [venueError, setVenueError] = useState(null)
  
  // Setup flow state - 6 steps: intro -> dishes -> guests -> wineType -> journey -> budget -> chat
  const [flowStep, setFlowStep] = useState('intro')
  const [selectedDishes, setSelectedDishes] = useState([])
  const [guestCount, setGuestCount] = useState(2)
  const [expandedCategories, setExpandedCategories] = useState({})
  
  // New preference states
  const [selectedWineType, setSelectedWineType] = useState(null)
  const [selectedJourney, setSelectedJourney] = useState(null)
  const [selectedBudget, setSelectedBudget] = useState(null) // null = no restriction, number = max price per bottle
  const [budgetInput, setBudgetInput] = useState('')
  const [bottlesCount, setBottlesCount] = useState(2) // Number of bottles for journey
  
  // Track which messages have shown action buttons (to hide after click)
  const [messagesWithActionsHandled, setMessagesWithActionsHandled] = useState(new Set())
  
  // Track selected wines/journeys per message
  const [selectedWineByMessage, setSelectedWineByMessage] = useState({}) // { messageId: wineId }
  const [selectedJourneyByMessage, setSelectedJourneyByMessage] = useState({}) // { messageId: journeyId }
  
  // Feedback state
  const [showFeedback, setShowFeedback] = useState(false)
  const [rating, setRating] = useState(0)
  const [feedbackText, setFeedbackText] = useState('')
  const [submittingFeedback, setSubmittingFeedback] = useState(false)
  
  // Modal state for "Valuta tutti"
  const [showAllWinesModal, setShowAllWinesModal] = useState(false)
  const [modalMessageId, setModalMessageId] = useState(null)
  const [modalWines, setModalWines] = useState([])
  const [loadingRankings, setLoadingRankings] = useState(false)
  
  // Calculate bottles when journey is selected or guest count changes
  useEffect(() => {
    if (selectedJourney === 'journey') {
      const calculated = calculateBottlesNeeded(guestCount)
      setBottlesCount(calculated)
    } else if (selectedJourney === 'single') {
      // Reset to 1 for single bottle option
      setBottlesCount(1)
    }
  }, [selectedJourney, guestCount])
  
  // Chat state
  const [inputValue, setInputValue] = useState('')
  const inputRef = useRef(null)
  
  const { 
    messages, 
    isLoading, 
    error, 
    sendMessage, 
    clearMessages,
    messagesEndRef,
    setInitialContext,
    sessionToken,
    addAssistantMessage,
    fetchWineRankings
  } = useChat(venueSlug, 'b2c')

  useEffect(() => {
    loadVenueAndMenu()
  }, [venueSlug])

  const loadVenueAndMenu = async () => {
    try {
      setVenueError(null)
      // Load venue
      const venueRes = await venueService.getVenue(venueSlug)
      setVenue(venueRes.data)
      
      // Load menu items
      if (venueRes.data?.id) {
        const menuRes = await menuService.getMenu(venueRes.data.id)
        setMenuItems(menuRes.data.items || menuRes.data || [])
        
        // Expand all categories by default
        const expanded = {}
        Object.keys(categoryLabels).forEach(k => expanded[k] = true)
        setExpandedCategories(expanded)
      }
    } catch (err) {
      console.error('Error loading venue/menu:', err)
      setVenueError('Impossibile caricare il ristorante. Verifica il link e riprova.')
    } finally {
      setVenueLoading(false)
    }
  }

  // Toggle dish selection
  const toggleDish = (dish) => {
    setSelectedDishes(prev => 
      prev.find(d => d.id === dish.id)
        ? prev.filter(d => d.id !== dish.id)
        : [...prev, dish]
    )
  }

  // Toggle category expansion
  const toggleCategory = (cat) => {
    setExpandedCategories(prev => ({
      ...prev,
      [cat]: !prev[cat]
    }))
  }

  // Group menu items by category
  const groupedMenu = menuItems.reduce((acc, item) => {
    const cat = item.category || 'altro'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(item)
    return acc
  }, {})

  // Flow navigation - 6 steps: intro -> dishes -> guests -> wineType -> journey -> budget -> chat
  const flowSteps = ['intro', 'dishes', 'guests', 'wineType', 'journey', 'budget', 'chat']
  
  const canProceed = () => {
    switch (flowStep) {
      case 'intro': return true
      case 'dishes': return selectedDishes.length > 0
      case 'guests': return guestCount >= 1
      case 'wineType': return selectedWineType !== null
      case 'journey': return selectedJourney !== null
      case 'budget': return selectedBudget !== null || budgetInput.trim() !== ''
      default: return false
    }
  }

  const nextStep = () => {
    const currentIndex = flowSteps.indexOf(flowStep)
    if (currentIndex < flowSteps.length - 1) {
      const nextStepName = flowSteps[currentIndex + 1]
      if (nextStepName === 'chat') {
        setFlowStep('chat')
        initializeChat()
      } else {
        setFlowStep(nextStepName)
      }
    }
  }

  const prevStep = () => {
    const currentIndex = flowSteps.indexOf(flowStep)
    if (currentIndex > 0) {
      setFlowStep(flowSteps[currentIndex - 1])
    }
  }
  
  // Get current step number for progress indicator (excluding intro and chat)
  const getStepProgress = () => {
    const progressSteps = ['dishes', 'guests', 'wineType', 'journey', 'budget']
    return progressSteps.indexOf(flowStep) + 1
  }

  // Initialize chat with ALL collected preferences
  const initializeChat = () => {
    const context = {
      dishes: selectedDishes.map(d => ({
        name: d.name,
        category: d.category,
        main_ingredient: d.main_ingredient || null,
        cooking_method: d.cooking_method || null
      })),
      guest_count: guestCount,
      // All preferences collected deterministically
      preferences: {
        wine_type: selectedWineType,
        journey_preference: selectedJourney,
        budget: selectedBudget === 'nolimit' || selectedBudget === null 
          ? null 
          : (budgetInput.trim() !== '' ? parseFloat(budgetInput) : (typeof selectedBudget === 'number' ? selectedBudget : null)),
        bottles_count: selectedJourney === 'journey' ? bottlesCount : null // Include bottles count for journey
      }
    }
    
    // Build initial message with all context - this will be hidden from UI
    const dishNames = selectedDishes.map(d => d.name).join(', ')
    const wineTypeLabel = wineTypeOptions.find(o => o.id === selectedWineType)?.label || selectedWineType
    const journeyLabel = journeyOptions.find(o => o.id === selectedJourney)?.label || selectedJourney
    const budgetLabel = selectedBudget === 'nolimit' || selectedBudget === null 
      ? 'Nessuna restrizione' 
      : budgetInput.trim() !== '' 
        ? `€${budgetInput}` 
        : selectedBudget !== null 
          ? `€${selectedBudget}` 
          : 'Nessuna restrizione'
    
    let initialMessage = `Siamo in ${guestCount} al tavolo. Abbiamo ordinato: ${dishNames}. Preferiamo ${wineTypeLabel}. Vogliamo ${journeyLabel}. Budget: ${budgetLabel}.`
    if (selectedJourney === 'journey') {
      initialMessage += ` Vogliamo un percorso di ${bottlesCount} ${bottlesCount === 1 ? 'bottiglia' : 'bottiglie'}.`
    }
    
    // Set context and send initial message (hidden from display)
    // The backend will recognize this as initial context message and use opening prompt
    if (setInitialContext) {
      setInitialContext(context)
    }
    sendMessage(initialMessage, context, { hidden: true })
  }
  
  // Filter messages to hide the initial automatic one
  const visibleMessages = messages.filter(m => !m.hidden)

  // Generate confirmation message with wine names
  const generateConfirmationMessage = (wines) => {
    if (!wines || wines.length === 0) {
      return "Perfetto! Grazie per la consulenza del sommelier. Chiamerò il cameriere per ordinare. Buona cena!"
    }
    
    const wineNames = wines.map(w => w.name || 'vino').join(' e ')
    return `Perfetto! Ho scelto ${wineNames}. Grazie per la consulenza del sommelier. Chiamerò il cameriere per ordinare queste etichette. Buona cena!`
  }

  // Generate continue message
  const generateContinueMessage = () => {
    return "Molto bene! Vorremmo valutare alternative per la selezione. Cos'altro ci proponi?"
  }

  // Handle confirmation button click (legacy, keep for compatibility)
  const handleConfirmSelection = async (messageId, wines) => {
    // Extract wine IDs from the wines array
    const wineIds = wines?.map(w => w.id).filter(id => id != null) || []
    
    // Track wines as confirmed/requested in the backend
    if (sessionToken && wineIds.length > 0) {
      try {
        await chatService.confirmWines(sessionToken, wineIds)
        console.log(`[CustomerChat] Confirmed ${wineIds.length} wines:`, wineIds)
      } catch (error) {
        console.error('[CustomerChat] Error confirming wines:', error)
        // Continue anyway - don't block the user experience
      }
    }
    
    // Send confirmation message to chat
    const confirmationMsg = generateConfirmationMessage(wines)
    sendMessage(confirmationMsg)
    setMessagesWithActionsHandled(prev => new Set([...prev, messageId]))
    
    // Show feedback form after confirmation message is sent
    // Wait a bit for the message to appear in the chat
    setTimeout(() => {
      setShowFeedback(true)
    }, 1000)
  }

  // Handle single wine confirmation with template
  const handleConfirmSingleWine = async (messageId, wineId, wines) => {
    // Find the selected wine
    const selectedWine = wines?.find(w => w.id === wineId) || wines?.[0]
    
    if (!selectedWine) {
      console.error('[CustomerChat] Selected wine not found')
      return
    }
    
    // Track wine as confirmed/requested in the backend
    if (sessionToken && selectedWine.id) {
      try {
        await chatService.confirmWines(sessionToken, [selectedWine.id])
        console.log(`[CustomerChat] Confirmed wine:`, selectedWine.id)
      } catch (error) {
        console.error('[CustomerChat] Error confirming wine:', error)
        // Continue anyway - don't block the user experience
      }
    }
    
    // Generate template confirmation message (from sommelier, not user)
    const confirmationMsg = `Perfetto! Abbiamo scelto ${selectedWine.name}${selectedWine.price ? ` - €${selectedWine.price}` : ''}. Grazie per la fiducia. Adesso potete chiedere al cameriere di portare questa etichetta. Buona cena!`
    
    // Add confirmation message directly as assistant message (NO AI call)
    addAssistantMessage(confirmationMsg)
    setMessagesWithActionsHandled(prev => new Set([...prev, messageId]))
    
    // Show feedback form after confirmation message is shown
    setTimeout(() => {
      setShowFeedback(true)
    }, 500)
  }

  // Handle journey confirmation with template
  const handleConfirmJourney = async (messageId, journeyId, journeys) => {
    // Find the selected journey
    const selectedJourney = journeys?.find(j => j.id === journeyId)
    
    if (!selectedJourney || !selectedJourney.wines || selectedJourney.wines.length === 0) {
      console.error('[CustomerChat] Selected journey not found or empty')
      return
    }
    
    // Extract all wine IDs from the journey
    const wineIds = selectedJourney.wines.map(w => w.id).filter(id => id != null)
    
    // Track wines as confirmed/requested in the backend
    if (sessionToken && wineIds.length > 0) {
      try {
        await chatService.confirmWines(sessionToken, wineIds)
        console.log(`[CustomerChat] Confirmed journey with ${wineIds.length} wines:`, wineIds)
      } catch (error) {
        console.error('[CustomerChat] Error confirming journey wines:', error)
        // Continue anyway - don't block the user experience
      }
    }
    
    // Generate template confirmation message (from sommelier, not user)
    const wineList = selectedJourney.wines
      .map(w => `- ${w.name}${w.price ? ` - €${w.price}` : ''}`)
      .join('\n')
    
    const confirmationMsg = `Perfetto! Abbiamo selezionato il percorso di degustazione:\n${wineList}\n\nChiedete al cameriere di portare queste etichette nell'ordine suggerito. Buona cena!`
    
    // Add confirmation message directly as assistant message (NO AI call)
    addAssistantMessage(confirmationMsg)
    setMessagesWithActionsHandled(prev => new Set([...prev, messageId]))
    
    // Show feedback form after confirmation message is shown
    setTimeout(() => {
      setShowFeedback(true)
    }, 500)
  }
  
  // Handle feedback submission
  const handleSubmitFeedback = async () => {
    if (rating === 0) {
      // Rating is required
      return
    }
    
    setSubmittingFeedback(true)
    try {
      await chatService.submitFeedback(sessionToken, rating, feedbackText)
      setShowFeedback(false)
      // Show thank you message
      const thankYouMsg = "Grazie per il tuo feedback! Buona cena! 🍷"
      sendMessage(thankYouMsg)
    } catch (error) {
      console.error('[CustomerChat] Error submitting feedback:', error)
      // Show error but don't block
    } finally {
      setSubmittingFeedback(false)
    }
  }
  
  // Handle skip feedback
  const handleSkipFeedback = () => {
    setShowFeedback(false)
  }

  // Handle continue button click
  const handleContinueSearch = (messageId) => {
    const continueMsg = generateContinueMessage()
    sendMessage(continueMsg)
    setMessagesWithActionsHandled(prev => new Set([...prev, messageId]))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (inputValue.trim() && !isLoading) {
      sendMessage(inputValue)
      setInputValue('')
    }
  }

  // Error state for venue loading
  if (venueError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-burgundy-950 via-burgundy-900 to-burgundy-950 flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-10 h-10 text-red-400" />
          </div>
          <h2 className="font-display text-2xl font-bold text-cream-50 mb-4">
            Errore di Caricamento
          </h2>
          <p className="text-cream-100/70 mb-6">{venueError}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-gold-500 text-burgundy-900 rounded-xl font-semibold hover:bg-gold-400 transition-colors"
          >
            Riprova
          </button>
        </div>
      </div>
    )
  }

  // Loading state
  if (venueLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-burgundy-950 via-burgundy-900 to-burgundy-950 flex items-center justify-center">
        <div className="text-center">
          <Logo size="xl" animate className="mx-auto mb-4" />
          <p className="text-cream-100/70">Caricamento...</p>
        </div>
      </div>
    )
  }

  // Render setup screens (dishes and guests only)
  if (flowStep !== 'chat') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-burgundy-950 via-burgundy-900 to-burgundy-950">
        {/* Header */}
        <header className="bg-burgundy-900/50 backdrop-blur-sm border-b border-burgundy-800 px-4 py-4">
          <div className="max-w-2xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Logo size="md" className="rounded-xl" />
              <div>
                <h1 className="font-display font-bold text-cream-50">
                  {venue?.name || 'Sommelier AI'}
                </h1>
                <p className="text-xs text-cream-100/70">Il tuo sommelier personale</p>
              </div>
            </div>
          </div>
        </header>

        {/* Progress indicator - 5 main steps (excluding intro) */}
        {flowStep !== 'intro' && (
          <div className="max-w-2xl mx-auto px-4 pt-6">
            <div className="flex gap-2 mb-8">
              {['dishes', 'guests', 'wineType', 'journey', 'budget'].map((step, idx) => (
                <div 
                  key={step}
                  className={`h-1.5 flex-1 rounded-full transition-colors ${
                    getStepProgress() > idx
                      ? 'bg-gold-500'
                      : 'bg-burgundy-700'
                  }`}
                />
              ))}
            </div>
          </div>
        )}

        {/* Step content */}
        <div className="max-w-2xl mx-auto px-4 pb-24">
          <AnimatePresence mode="wait">
            {/* Step 0: Introduction */}
            {flowStep === 'intro' && (
              <motion.div
                key="intro"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="text-center py-8"
              >
                {/* Sommelier Avatar */}
                <motion.div
                  initial={{ scale: 0.8 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: 'spring' }}
                  className="w-28 h-28 bg-gradient-to-br from-gold-400 to-gold-600 rounded-full flex items-center justify-center mx-auto mb-8 shadow-lg"
                >
                  <Wine className="w-14 h-14 text-burgundy-900" />
                </motion.div>
                
                <motion.h2 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.4 }}
                  className="font-display text-3xl font-bold text-cream-50 mb-4"
                >
                  Benvenuto!
                </motion.h2>
                
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.6 }}
                  className="bg-burgundy-800/50 rounded-2xl p-6 max-w-md mx-auto"
                >
                  <p className="text-cream-100 text-lg leading-relaxed mb-4">
                    Sono il <span className="text-gold-400 font-semibold">sommelier virtuale</span> di{' '}
                    <span className="text-gold-400 font-semibold">{venue?.name || 'questo ristorante'}</span>.
                  </p>
                  <p className="text-cream-100/80 leading-relaxed">
                    Vi accompagnerò nella scelta del vino perfetto. 
                    Iniziamo con qualche semplice domanda, e poi procediamo alla selezione.
                  </p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.8 }}
                  className="mt-8 flex justify-center gap-3"
                >
                  <span className="inline-flex items-center gap-2 px-4 py-2 bg-burgundy-800/50 rounded-full text-cream-100/70 text-sm">
                    <Sparkles className="w-4 h-4 text-gold-400" />
                    Powered by Liber
                  </span>
                </motion.div>
              </motion.div>
            )}

            {/* Step 1: Dish Selection */}
            {flowStep === 'dishes' && (
              <motion.div
                key="dishes"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <h2 className="font-display text-2xl font-bold text-cream-50 mb-2">
                  Cosa avete ordinato?
                </h2>
                <p className="text-cream-100/70 mb-6">
                  Seleziona i piatti per ricevere l'abbinamento perfetto
                </p>

                {/* Selected dishes preview */}
                {selectedDishes.length > 0 && (
                  <div className="bg-gold-500/10 border border-gold-500/30 rounded-xl p-4 mb-6">
                    <div className="flex flex-wrap gap-2">
                      {selectedDishes.map(dish => (
                        <span 
                          key={dish.id}
                          className="inline-flex items-center gap-1 px-3 py-1 bg-gold-500 text-burgundy-900 rounded-full text-sm font-medium"
                        >
                          {dish.name}
                          <button 
                            onClick={() => toggleDish(dish)}
                            className="ml-1 hover:bg-burgundy-900/20 rounded-full p-0.5"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Menu categories */}
                <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-2">
                  {Object.entries(categoryLabels).map(([catKey, catLabel]) => {
                    const dishes = groupedMenu[catKey]
                    if (!dishes || dishes.length === 0) return null
                    
                    return (
                      <div key={catKey} className="bg-burgundy-800/50 rounded-xl overflow-hidden">
                        <button
                          onClick={() => toggleCategory(catKey)}
                          className="w-full flex items-center justify-between p-4 text-left"
                        >
                          <span className="font-display font-semibold text-cream-50">
                            {catLabel} 
                            <span className="text-cream-100/50 font-normal ml-2">
                              ({dishes.length})
                            </span>
                          </span>
                          <ChevronDown 
                            className={`w-5 h-5 text-gold-500 transition-transform ${
                              expandedCategories[catKey] ? 'rotate-180' : ''
                            }`} 
                          />
                        </button>
                        
                        <AnimatePresence>
                          {expandedCategories[catKey] && (
                            <motion.div
                              initial={{ height: 0 }}
                              animate={{ height: 'auto' }}
                              exit={{ height: 0 }}
                              className="overflow-hidden"
                            >
                              <div className="px-4 pb-4 space-y-2">
                                {dishes.map(dish => {
                                  const isSelected = selectedDishes.find(d => d.id === dish.id)
                                  return (
                                    <button
                                      key={dish.id}
                                      onClick={() => toggleDish(dish)}
                                      className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all ${
                                        isSelected
                                          ? 'bg-gold-500 text-burgundy-900'
                                          : 'bg-burgundy-700/50 text-cream-50 hover:bg-burgundy-700'
                                      }`}
                                    >
                                      <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center ${
                                        isSelected 
                                          ? 'border-burgundy-900 bg-burgundy-900' 
                                          : 'border-cream-100/30'
                                      }`}>
                                        {isSelected && <Check className="w-3 h-3 text-gold-500" />}
                                      </div>
                                      <span className="flex-1 text-left font-medium">{dish.name}</span>
                                      {dish.price && (
                                        <span className={isSelected ? 'text-burgundy-700' : 'text-gold-400'}>
                                          €{dish.price}
                                        </span>
                                      )}
                                    </button>
                                  )
                                })}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    )
                  })}
                </div>

                {/* Empty menu state */}
                {menuItems.length === 0 && (
                  <div className="text-center py-12">
                    <Wine className="w-12 h-12 text-burgundy-600 mx-auto mb-4" />
                    <p className="text-cream-100/70">
                      Il menu non è ancora stato caricato.
                    </p>
                  </div>
                )}
              </motion.div>
            )}

            {/* Step 2: Guest Count */}
            {flowStep === 'guests' && (
              <motion.div
                key="guests"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="text-center"
              >
                <div className="w-20 h-20 bg-gold-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Users className="w-10 h-10 text-gold-500" />
                </div>
                
                <h2 className="font-display text-2xl font-bold text-cream-50 mb-2">
                  Quanti siete a tavola?
                </h2>
                <p className="text-cream-100/70 mb-8">
                  Ci aiuta a suggerire le quantità giuste
                </p>

                <div className="flex items-center justify-center gap-6">
                  <button
                    onClick={() => setGuestCount(Math.max(1, guestCount - 1))}
                    className="w-14 h-14 rounded-full bg-burgundy-700 text-cream-50 text-2xl font-bold hover:bg-burgundy-600 transition-colors"
                  >
                    −
                  </button>
                  <div className="w-24 h-24 rounded-2xl bg-gold-500 flex items-center justify-center">
                    <span className="text-4xl font-display font-bold text-burgundy-900">
                      {guestCount}
                    </span>
                  </div>
                  <button
                    onClick={() => setGuestCount(Math.min(20, guestCount + 1))}
                    className="w-14 h-14 rounded-full bg-burgundy-700 text-cream-50 text-2xl font-bold hover:bg-burgundy-600 transition-colors"
                  >
                    +
                  </button>
                </div>
                
                <p className="mt-4 text-cream-100/50 text-sm">
                  {guestCount === 1 ? 'persona' : 'persone'}
                </p>

                {/* Bottles suggestion */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="mt-8 bg-burgundy-800/30 rounded-xl p-4 border border-gold-500/20 max-w-md mx-auto"
                >
                  <p className="text-sm text-cream-100/90">
                    Per un percorso di degustazione, suggeriremmo <span className="font-bold text-gold-400">{calculateBottlesNeeded(guestCount)} bottiglie</span> per {guestCount} {guestCount === 1 ? 'persona' : 'persone'} (circa 2 portate a testa).
                  </p>
                </motion.div>
              </motion.div>
            )}

            {/* Step 3: Wine Type Preference */}
            {flowStep === 'wineType' && (
              <motion.div
                key="wineType"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <div className="text-center mb-8">
                  <div className="w-20 h-20 bg-burgundy-700/50 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Wine className="w-10 h-10 text-gold-500" />
                  </div>
                  <h2 className="font-display text-2xl font-bold text-cream-50 mb-2">
                    Che tipo di vino preferite?
                  </h2>
                  <p className="text-cream-100/70">
                    Seleziona la tipologia o lascia scegliere al sommelier
                  </p>
                </div>

                <div className="grid gap-3">
                  {wineTypeOptions.map((option) => (
                    <button
                      key={option.id}
                      onClick={() => setSelectedWineType(option.id)}
                      className={`w-full flex items-center gap-4 p-4 rounded-xl transition-all ${
                        selectedWineType === option.id
                          ? 'bg-gold-500 text-burgundy-900'
                          : 'bg-burgundy-800/50 text-cream-50 hover:bg-burgundy-700/50'
                      }`}
                    >
                      <span className="text-2xl">{option.icon}</span>
                      <div className="text-left flex-1">
                        <div className="font-semibold">{option.label}</div>
                        <div className={`text-sm ${selectedWineType === option.id ? 'text-burgundy-700' : 'text-cream-100/60'}`}>
                          {option.description}
                        </div>
                      </div>
                      {selectedWineType === option.id && (
                        <Check className="w-5 h-5" />
                      )}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Step 4: Single or Journey */}
            {flowStep === 'journey' && (
              <motion.div
                key="journey"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <div className="text-center mb-8">
                  <div className="w-20 h-20 bg-burgundy-700/50 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Sparkles className="w-10 h-10 text-gold-500" />
                  </div>
                  <h2 className="font-display text-2xl font-bold text-cream-50 mb-2">
                    Come volete degustare?
                  </h2>
                  <p className="text-cream-100/70">
                    Un solo vino o un percorso di degustazione?
                  </p>
                </div>

                <div className="grid gap-4 mb-6">
                  {journeyOptions.map((option) => (
                    <button
                      key={option.id}
                      onClick={() => setSelectedJourney(option.id)}
                      className={`w-full flex items-center gap-4 p-5 rounded-xl transition-all ${
                        selectedJourney === option.id
                          ? 'bg-gold-500 text-burgundy-900'
                          : 'bg-burgundy-800/50 text-cream-50 hover:bg-burgundy-700/50'
                      }`}
                    >
                      <span className="text-3xl">{option.icon}</span>
                      <div className="text-left flex-1">
                        <div className="font-semibold text-lg">{option.label}</div>
                        <div className={`text-sm ${selectedJourney === option.id ? 'text-burgundy-700' : 'text-cream-100/60'}`}>
                          {option.description}
                        </div>
                      </div>
                      {selectedJourney === option.id && (
                        <Check className="w-6 h-6" />
                      )}
                    </button>
                  ))}
                </div>

                {/* Bottles count selector - only show when journey is selected */}
                {selectedJourney === 'journey' && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="bg-burgundy-800/30 rounded-xl p-6 border border-gold-500/20 mt-6"
                  >
                    <div className="text-center mb-4">
                      <h3 className="font-semibold text-cream-50 mb-2">
                        Quante bottiglie per il percorso?
                      </h3>
                      <p className="text-sm text-cream-100/70">
                        Abbiamo suggerito <span className="font-bold text-gold-400">{calculateBottlesNeeded(guestCount)} bottiglie</span> per {guestCount} {guestCount === 1 ? 'persona' : 'persone'} (circa 2 portate a testa). Puoi modificare questo numero.
                      </p>
                    </div>
                    
                    <div className="flex items-center justify-center gap-4">
                      <button
                        onClick={() => setBottlesCount(Math.max(1, bottlesCount - 1))}
                        className="w-12 h-12 rounded-full bg-burgundy-700 text-cream-50 text-2xl font-bold hover:bg-burgundy-600 transition-colors"
                      >
                        −
                      </button>
                      <div className="w-20 h-20 rounded-2xl bg-gold-500 flex items-center justify-center">
                        <span className="text-3xl font-display font-bold text-burgundy-900">
                          {bottlesCount}
                        </span>
                      </div>
                      <button
                        onClick={() => setBottlesCount(Math.min(10, bottlesCount + 1))}
                        className="w-12 h-12 rounded-full bg-burgundy-700 text-cream-50 text-2xl font-bold hover:bg-burgundy-600 transition-colors"
                      >
                        +
                      </button>
                    </div>
                    
                    <p className="text-center mt-4 text-cream-100/50 text-xs">
                      {bottlesCount === 1 ? 'bottiglia' : 'bottiglie'}
                    </p>
                  </motion.div>
                )}
              </motion.div>
            )}

            {/* Step 5: Budget */}
            {flowStep === 'budget' && (
              <motion.div
                key="budget"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <div className="text-center mb-8">
                  <h2 className="font-display text-2xl font-bold text-cream-50 mb-2">
                    Budget per bottiglia
                  </h2>
                  <p className="text-cream-100/70">
                    Inserisci il budget massimo o seleziona nessuna restrizione
                  </p>
                </div>

                <div className="space-y-4">
                  {/* Budget input */}
                  <div className="bg-burgundy-800/30 rounded-xl p-5 border border-burgundy-700/30">
                    <label className="block text-cream-50 font-semibold mb-3">
                      Budget per bottiglia (€)
                    </label>
                    <div className="flex gap-3">
                      <div className="flex-1">
                        <div className="relative">
                          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-cream-100/70 font-semibold">€</span>
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            placeholder="Es. 25.00"
                            value={budgetInput}
                            onChange={(e) => {
                              const value = e.target.value
                              setBudgetInput(value)
                              // If user types a number, set it as budget
                              if (value.trim() !== '') {
                                const numValue = parseFloat(value)
                                if (!isNaN(numValue) && numValue > 0) {
                                  setSelectedBudget(numValue)
                                }
                              } else {
                                // Clear budget if input is empty (unless "no limit" is selected)
                                if (selectedBudget !== 'nolimit') {
                                  setSelectedBudget(null)
                                }
                              }
                            }}
                            className="w-full pl-10 pr-4 py-3 bg-burgundy-700/50 border border-burgundy-600 rounded-lg text-cream-50 placeholder-cream-100/40 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                          />
                        </div>
                        <p className="text-xs text-cream-100/60 mt-2">
                          Inserisci il budget massimo per bottiglia
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* No restriction button */}
                  <button
                    onClick={() => {
                      setSelectedBudget('nolimit')
                      setBudgetInput('') // Clear input when "no restriction" is selected
                    }}
                    className={`w-full flex items-center justify-center gap-3 p-5 rounded-xl transition-all ${
                      selectedBudget === 'nolimit'
                        ? 'bg-gold-500 text-burgundy-900'
                        : 'bg-burgundy-800/50 text-cream-50 hover:bg-burgundy-700/50'
                    }`}
                  >
                    <span className="text-2xl">✨</span>
                    <div className="text-left flex-1">
                      <div className="font-semibold text-lg">Nessuna restrizione</div>
                      <div className={`text-sm mt-1 ${selectedBudget === 'nolimit' ? 'text-burgundy-700' : 'text-cream-100/60'}`}>
                        Proponi i migliori vini disponibili
                      </div>
                    </div>
                    {selectedBudget === 'nolimit' && (
                      <Check className="w-6 h-6" />
                    )}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Navigation buttons */}
        <div className="fixed bottom-0 left-0 right-0 bg-burgundy-900/90 backdrop-blur-sm border-t border-burgundy-800 px-4 py-4">
          <div className="max-w-2xl mx-auto flex gap-3">
            {flowStep !== 'intro' && (
              <button
                onClick={prevStep}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-burgundy-700 text-cream-50 rounded-xl hover:bg-burgundy-600 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                Indietro
              </button>
            )}
            <button
              onClick={nextStep}
              disabled={!canProceed()}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gold-500 text-burgundy-900 rounded-xl font-semibold hover:bg-gold-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {flowStep === 'intro' ? (
                <>
                  <Sparkles className="w-5 h-5" />
                  Iniziamo!
                </>
              ) : flowStep === 'budget' ? (
                <>
                  <Sparkles className="w-5 h-5" />
                  Chiedi al Sommelier
                </>
              ) : (
                'Continua'
              )}
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Chat mode
  return (
    <div className="min-h-screen bg-cream-50 flex flex-col">
      {/* Header */}
      <header className="bg-burgundy-900 text-cream-50 px-4 py-4 shadow-lg">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gold-500 rounded-xl flex items-center justify-center">
              <Wine className="w-6 h-6 text-burgundy-900" />
            </div>
            <div>
              <h1 className="font-display font-bold">
                {venue?.name || 'Sommelier AI'}
              </h1>
              <p className="text-xs text-cream-100/70">Il tuo sommelier personale</p>
            </div>
          </div>
          <button
            onClick={() => {
              setFlowStep('dishes')
              clearMessages()
            }}
            className="flex items-center gap-2 px-3 py-2 bg-burgundy-800 rounded-lg hover:bg-burgundy-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span className="text-sm">Ricomincia</span>
          </button>
        </div>
      </header>

      {/* Simplified context summary - only dishes and guests */}
      <div className="bg-burgundy-800 text-cream-100 px-4 py-2 text-sm">
        <div className="max-w-2xl mx-auto flex flex-wrap gap-4">
          <span className="flex items-center gap-1">
            <Users className="w-4 h-4 text-gold-400" />
            {guestCount} {guestCount === 1 ? 'persona' : 'persone'}
          </span>
          <span className="flex items-center gap-1 text-cream-100/70">
            <Wine className="w-4 h-4 text-gold-400" />
            {selectedDishes.length} piatti selezionati
          </span>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-2xl mx-auto space-y-4">
          <AnimatePresence mode="popLayout">
            {visibleMessages.map((message, msgIdx) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={message.role === 'user' ? 'flex justify-end' : 'flex justify-start'}
              >
                {message.role === 'assistant' ? (
                  <div className="flex gap-3 max-w-[85%]">
                    <div className="w-10 h-10 bg-gradient-to-br from-gold-400 to-gold-600 rounded-full flex items-center justify-center flex-shrink-0 shadow-md">
                      <Wine className="w-5 h-5 text-burgundy-900" />
                    </div>
                    <div className="space-y-3">
                      {/* Render message content - always show if exists or if we have wines/journeys */}
                      {(message.content && message.content.trim()) || (message.wines && message.wines.length > 0) || (message.journeys && message.journeys.length > 0) ? (
                        message.content && message.content.trim() ? (
                      <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-burgundy-100">
                        {/* Render markdown formatted message */}
                        <div className="text-burgundy-800 leading-relaxed prose prose-burgundy prose-sm max-w-none">
                          <ReactMarkdown
                            components={{
                              // Style paragraphs
                              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                              // Style bold text
                              strong: ({ children }) => <strong className="font-semibold text-burgundy-900">{children}</strong>,
                              // Style italic text
                              em: ({ children }) => <em className="italic text-burgundy-700">{children}</em>,
                              // Style lists
                              ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                              ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                              li: ({ children }) => <li className="text-burgundy-800">{children}</li>,
                              // Style horizontal rules
                              hr: () => <hr className="my-3 border-burgundy-200" />,
                              // Style headings (for wine sections)
                              h3: ({ children }) => <h3 className="font-semibold text-burgundy-900 mt-3 mb-1">{children}</h3>,
                              // Style links if any
                              a: ({ children, href }) => <a href={href} className="text-gold-600 hover:underline">{children}</a>,
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      </div>
                        ) : (
                          // Show fallback message if content is empty but we have wines/journeys
                          <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-burgundy-100">
                            <p className="text-burgundy-800 leading-relaxed">
                              Ecco le mie raccomandazioni per voi.
                            </p>
                          </div>
                        )
                      ) : null}
                      
                      {/* Wine suggestions - SINGLE mode (wines array) */}
                      {message.mode !== 'journey' && message.wines && message.wines.length > 0 && (
                        <motion.div 
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.3 }}
                          className="space-y-3"
                        >
                          <p className="text-xs text-burgundy-500 font-medium uppercase tracking-wide flex items-center gap-1">
                            <Sparkles className="w-3 h-3" />
                            I miei consigli per voi
                          </p>
                          
                          {/* All recommended wines - show all as selectable cards */}
                          {message.wines.length > 0 && (
                            <div className="space-y-2">
                              {message.wines.map((wine, idx) => (
                                <WineCard 
                                  key={wine.id || idx}
                                  wine={wine} 
                                  isMainRecommendation={wine.best === true || (wine.best === undefined && idx === 0)}
                                  selected={selectedWineByMessage[message.id] === wine.id || 
                                           (selectedWineByMessage[message.id] === undefined && (wine.best === true || (wine.best === undefined && idx === 0)) && wine.id)}
                                  onClick={() => setSelectedWineByMessage(prev => ({
                                    ...prev,
                                    [message.id]: wine.id
                                  }))}
                                />
                              ))}
                            </div>
                          )}
                          
                          {/* Action buttons - only show if not already handled */}
                          {!messagesWithActionsHandled.has(message.id) && (
                            <motion.div
                              initial={{ opacity: 0, y: 5 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: 0.5 }}
                              className="flex gap-3 pt-2"
                            >
                              <button
                                onClick={() => {
                                  const selectedWineId = selectedWineByMessage[message.id] || message.wines[0]?.id
                                  if (selectedWineId) {
                                    handleConfirmSingleWine(message.id, selectedWineId, message.wines)
                                  }
                                }}
                                disabled={isLoading || (!selectedWineByMessage[message.id] && !message.wines[0]?.id)}
                                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                              >
                                <CheckCircle2 className="w-5 h-5" />
                                Conferma questa etichetta
                              </button>
                              <button
                                onClick={async () => {
                                  setModalMessageId(message.id)
                                  setLoadingRankings(true)
                                  setShowAllWinesModal(true)
                                  
                                  // Fetch rankings from API using message_id from server
                                  try {
                                    const messageId = message.message_id || message.id
                                    if (messageId) {
                                      const rankings = await fetchWineRankings(messageId)
                                      if (rankings && rankings.length > 0) {
                                        setModalWines(rankings)
                                      } else {
                                        // Fallback to all_rankings from message
                                        const messageRankings = message.all_rankings || message.wines || []
                                        setModalWines(messageRankings)
                                      }
                                    } else {
                                      // No message_id available, use fallback
                                      const messageRankings = message.all_rankings || message.wines || []
                                      setModalWines(messageRankings)
                                    }
                                  } catch (err) {
                                    console.error('Error fetching rankings:', err)
                                    // Fallback to all_rankings from message
                                    const messageRankings = message.all_rankings || message.wines || []
                                    setModalWines(messageRankings)
                                  } finally {
                                    setLoadingRankings(false)
                                  }
                                }}
                                disabled={isLoading}
                                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gold-500 text-burgundy-900 rounded-xl font-semibold hover:bg-gold-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                              >
                                <Star className="w-5 h-5" />
                                Valuta tutti i vini
                              </button>
                            </motion.div>
                          )}
                        </motion.div>
                      )}
                      
                      {/* Journey suggestions - JOURNEY mode */}
                      {message.mode === 'journey' && message.journeys && message.journeys.length > 0 && (
                        <motion.div 
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.3 }}
                          className="space-y-4"
                        >
                          <p className="text-xs text-burgundy-500 font-medium uppercase tracking-wide flex items-center gap-1">
                            <Sparkles className="w-3 h-3" />
                            I miei percorsi per voi
                          </p>
                          
                          {message.journeys.map((journey, journeyIdx) => (
                            <div 
                              key={journey.id || journeyIdx}
                              className={`p-4 rounded-xl border-2 transition-all ${
                                selectedJourneyByMessage[message.id] === journey.id
                                  ? 'border-gold-500 bg-gold-50/30 shadow-md'
                                  : 'border-burgundy-100 bg-white'
                              }`}
                            >
                              <div className="flex items-start justify-between mb-3">
                                <div>
                                  <h4 className="font-display font-semibold text-burgundy-900 text-lg">
                                    {journey.name || `Percorso ${journeyIdx + 1}`}
                                  </h4>
                                  {(journey.reason || journey.description) && (
                                    <p className="text-sm text-burgundy-600 mt-1">{journey.reason || journey.description}</p>
                                  )}
                                </div>
                                <button
                                  onClick={() => setSelectedJourneyByMessage(prev => ({
                                    ...prev,
                                    [message.id]: journey.id
                                  }))}
                                  className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                                    selectedJourneyByMessage[message.id] === journey.id
                                      ? 'bg-gold-500 text-burgundy-900'
                                      : 'bg-burgundy-700 text-cream-50 hover:bg-burgundy-600'
                                  }`}
                                >
                                  {selectedJourneyByMessage[message.id] === journey.id ? 'Selezionato' : 'Seleziona questo percorso'}
                                </button>
                              </div>
                              
                              <div className="space-y-2">
                                {journey.wines && journey.wines.map((wine, wineIdx) => (
                                  <WineCard key={wine.id || wineIdx} wine={wine} />
                                ))}
                              </div>
                            </div>
                          ))}
                          
                          {/* Action buttons - only show if not already handled */}
                          {!messagesWithActionsHandled.has(message.id) && (
                            <motion.div
                              initial={{ opacity: 0, y: 5 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: 0.5 }}
                              className="flex gap-3 pt-2"
                            >
                              <button
                                onClick={() => {
                                  const selectedJourneyId = selectedJourneyByMessage[message.id]
                                  if (selectedJourneyId) {
                                    handleConfirmJourney(message.id, selectedJourneyId, message.journeys)
                                  }
                                }}
                                disabled={isLoading || !selectedJourneyByMessage[message.id]}
                                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                              >
                                <CheckCircle2 className="w-5 h-5" />
                                Conferma questo percorso
                              </button>
                            </motion.div>
                          )}
                        </motion.div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="bg-burgundy-800 text-cream-50 rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm max-w-[80%]">
                    <p className="leading-relaxed">{message.content}</p>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Loading indicator */}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-3"
            >
              <div className="w-8 h-8 bg-burgundy-900 rounded-full flex items-center justify-center">
                <Wine className="w-4 h-4 text-gold-500" />
              </div>
              <div className="chat-bubble-ai">
                <ThinkingMessages />
              </div>
            </motion.div>
          )}

          {/* Error message - clear and actionable */}
          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-3"
            >
              <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center flex-shrink-0">
                <AlertCircle className="w-4 h-4 text-white" />
              </div>
              <div className="bg-red-50 border border-red-200 rounded-2xl rounded-tl-sm px-4 py-3 max-w-[85%]">
                <p className="text-red-800 font-medium mb-1">Errore di connessione</p>
                <p className="text-red-600 text-sm">{error}</p>
                <button
                  onClick={() => sendMessage(inputValue || 'Riprova')}
                  className="mt-2 text-sm text-red-700 underline hover:text-red-900"
                >
                  Riprova
                </button>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
          
          {/* Feedback Form - Show after confirmation */}
          <AnimatePresence>
            {showFeedback && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mt-6 p-6 bg-gradient-to-br from-burgundy-800 to-burgundy-900 rounded-2xl border-2 border-gold-500/30 shadow-xl"
              >
                <div className="text-center mb-6">
                  <h3 className="font-display text-xl font-bold text-cream-50 mb-2">
                    Come è stata la tua esperienza?
                  </h3>
                  <p className="text-sm text-cream-100/70">
                    Il tuo feedback ci aiuta a migliorare
                  </p>
                </div>
                
                {/* Star Rating */}
                <div className="flex justify-center gap-2 mb-6">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setRating(star)}
                      className="transition-transform hover:scale-110 active:scale-95"
                      type="button"
                    >
                      <Star
                        className={`w-10 h-10 ${
                          star <= rating
                            ? 'fill-gold-500 text-gold-500'
                            : 'fill-burgundy-700 text-burgundy-600'
                        } transition-colors`}
                      />
                    </button>
                  ))}
                </div>
                
                {/* Feedback Text */}
                <div className="mb-4">
                  <textarea
                    value={feedbackText}
                    onChange={(e) => setFeedbackText(e.target.value)}
                    placeholder="Vuoi aggiungere un commento? (opzionale)"
                    className="w-full p-3 rounded-xl bg-burgundy-700/50 border border-burgundy-600 text-cream-50 placeholder-cream-300/50 focus:outline-none focus:ring-2 focus:ring-gold-500 resize-none"
                    rows={3}
                  />
                </div>
                
                {/* Action Buttons */}
                <div className="flex gap-3">
                  <button
                    onClick={handleSkipFeedback}
                    disabled={submittingFeedback}
                    className="flex-1 px-4 py-3 bg-burgundy-700 text-cream-50 rounded-xl font-semibold hover:bg-burgundy-600 transition-colors disabled:opacity-50"
                  >
                    Salta
                  </button>
                  <button
                    onClick={handleSubmitFeedback}
                    disabled={rating === 0 || submittingFeedback}
                    className="flex-1 px-4 py-3 bg-gold-500 text-burgundy-900 rounded-xl font-semibold hover:bg-gold-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {submittingFeedback ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        Invio...
                      </>
                    ) : (
                      <>
                        <Check className="w-4 h-4" />
                        Invia Feedback
                      </>
                    )}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* All Wines Modal */}
      {modalMessageId && (
        <AllWinesModal
          isOpen={showAllWinesModal}
          onClose={() => {
            setShowAllWinesModal(false)
            setModalMessageId(null)
            setModalWines([])
          }}
          wines={loadingRankings ? [] : (modalWines.length > 0 ? modalWines : (() => {
            // Fallback: try to get from message if API didn't return data
            const message = visibleMessages.find(m => m.id === modalMessageId)
            return message?.all_rankings || message?.wines || []
          })())}
          isLoading={loadingRankings}
          onSelectWine={(wineId) => {
            if (modalMessageId) {
              setSelectedWineByMessage(prev => ({
                ...prev,
                [modalMessageId]: wineId
              }))
              setShowAllWinesModal(false)
              setModalMessageId(null)
              setModalWines([])
            }
          }}
          selectedWineId={modalMessageId ? selectedWineByMessage[modalMessageId] : null}
        />
      )}

      {/* Input Form */}
      <div className="border-t border-burgundy-100 bg-white px-4 py-4">
        <form onSubmit={handleSubmit} className="max-w-2xl mx-auto">
          <div className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Rispondi al sommelier..."
              className="input-field flex-1"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="btn-primary px-4 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CustomerChat

