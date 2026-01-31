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
  Star,
  ArrowUp
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useTranslation } from 'react-i18next'
import { venueService, menuService, chatService } from '../services/api'
import { useChat } from '../hooks/useChat'
import { ThinkingMessages } from '../components/ui/LoadingSpinner'
import WineCard from '../components/chat/WineCard'
import AllWinesModal from '../components/chat/AllWinesModal'
import JourneyDetailsModal from '../components/chat/JourneyDetailsModal'
import DishSelector from '../components/chat/DishSelector'
import Logo from '../components/ui/Logo'
import LanguageSwitcher from '../components/ui/LanguageSwitcher'
import { useLanguageStore } from '../stores/languageStore'

// Category labels for display - now using translations
const getCategoryLabels = (t) => ({
  'antipasto': t('customerChat:dishes.categories.antipasto'),
  'primo': t('customerChat:dishes.categories.primo'),
  'secondo': t('customerChat:dishes.categories.secondo'),
  'contorno': t('customerChat:dishes.categories.contorno'),
  'dolce': t('customerChat:dishes.categories.dolce'),
  'altro': t('customerChat:dishes.categories.altro')
})

// Wine type options - now using translations
const getWineTypeOptions = (t) => [
  { id: 'red', label: t('customerChat:wineType.options.red.label'), icon: '🍷', description: t('customerChat:wineType.options.red.description') },
  { id: 'white', label: t('customerChat:wineType.options.white.label'), icon: '🥂', description: t('customerChat:wineType.options.white.description') },
  { id: 'sparkling', label: t('customerChat:wineType.options.sparkling.label'), icon: '🍾', description: t('customerChat:wineType.options.sparkling.description') },
  { id: 'rose', label: t('customerChat:wineType.options.rose.label'), icon: '🌸', description: t('customerChat:wineType.options.rose.description') },
  { id: 'any', label: t('customerChat:wineType.options.any.label'), icon: '✨', description: t('customerChat:wineType.options.any.description') }
]

// Journey options - now using translations
const getJourneyOptions = (t) => [
  { id: 'single', label: t('customerChat:journey.options.single.label'), icon: '🍷', description: t('customerChat:journey.options.single.description') },
  { id: 'journey', label: t('customerChat:journey.options.journey.label'), icon: '🗺️', description: t('customerChat:journey.options.journey.description') }
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
  const { t, i18n } = useTranslation()
  const { language, setLanguage } = useLanguageStore()

  // Get translated options
  const categoryLabels = getCategoryLabels(t)
  const wineTypeOptions = getWineTypeOptions(t)
  const journeyOptions = getJourneyOptions(t)

  const [venue, setVenue] = useState(null)
  const [menuItems, setMenuItems] = useState([])
  const [venueLoading, setVenueLoading] = useState(true)
  const [venueError, setVenueError] = useState(null)

  // Access token state
  const [accessToken, setAccessToken] = useState(null)
  const [tokenLoading, setTokenLoading] = useState(true)
  const [tokenError, setTokenError] = useState(null)

  // Setup flow state - 6 steps: intro -> dishes -> guests -> wineType -> journey -> budget -> chat
  const [flowStep, setFlowStep] = useState('intro')
  const [selectedDishes, setSelectedDishes] = useState([])
  const [guestCount, setGuestCount] = useState(2)
  const [expandedCategories, setExpandedCategories] = useState({})

  // New preference states
  const [selectedWineType, setSelectedWineType] = useState(null)
  const [selectedJourney, setSelectedJourney] = useState('single') // Default to 'single' - journey selection hidden
  const [selectedBudget, setSelectedBudget] = useState(null) // null = no restriction, number = max price per bottle
  const [budgetInput, setBudgetInput] = useState('')
  const [bottlesCount, setBottlesCount] = useState(2) // Number of bottles for journey
  
  // Track which messages have shown action buttons (to hide after click)
  const [messagesWithActionsHandled, setMessagesWithActionsHandled] = useState(new Set())
  
  // Track selected wines/journeys per message
  const [selectedWineByMessage, setSelectedWineByMessage] = useState({}) // { messageId: wineId }
  const [selectedJourneyByMessage, setSelectedJourneyByMessage] = useState({}) // { messageId: journeyId }
  const [selectedJourneyDetails, setSelectedJourneyDetails] = useState({}) // { messageId: journeyId } - which journey shows details modal
  
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
  const [showProceedButton, setShowProceedButton] = useState(false)
  const [proceedLoading, setProceedLoading] = useState(false)
  const [precomputeStatus, setPrecomputeStatus] = useState(null)
  const [showClarificationHint, setShowClarificationHint] = useState(false)
  
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
  
  // Get or create access token on mount
  useEffect(() => {
    const getOrCreateAccessToken = async () => {
      if (!venueSlug) {
        setTokenLoading(false)
        return
      }
      
      const storageKey = `access_token_${venueSlug}`
      const expiresKey = `access_token_${venueSlug}_expires`
      
      // Check localStorage for existing token
      const storedToken = localStorage.getItem(storageKey)
      const storedExpiry = localStorage.getItem(expiresKey)
      
      // Verify if stored token is still valid
      if (storedToken && storedExpiry) {
        const expiryDate = new Date(storedExpiry)
        if (expiryDate > new Date()) {
          // Token still valid, use it
          setAccessToken(storedToken)
          setTokenLoading(false)
          return
        } else {
          // Token expired, remove it
          localStorage.removeItem(storageKey)
          localStorage.removeItem(expiresKey)
        }
      }
      
      // Create new token
      try {
        setTokenLoading(true)
        const response = await chatService.createStartToken(venueSlug)
        const newToken = response.data.access_token
        const expiresAt = response.data.expires_at
        
        setAccessToken(newToken)
        setTokenError(null)
        
        // Save to localStorage
        localStorage.setItem(storageKey, newToken)
        localStorage.setItem(expiresKey, expiresAt)
        
        setTokenLoading(false)
      } catch (error) {
        console.error('Error creating access token:', error)
        
        // Check if it's a WiFi verification error
        if (error.response?.data?.error_code === 'WIFI_VERIFICATION_FAILED') {
          setTokenError(t('customerChat:errors.wifiRequired'))
        } else {
          setTokenError(error.response?.data?.message || t('customerChat:errors.tokenError'))
        }
        setTokenLoading(false)
      }
    }
    
    getOrCreateAccessToken()
  }, [venueSlug])

  const { 
    messages, 
    isLoading, 
    error, 
    sendMessage, 
    clearMessages,
    messagesEndRef,
    setInitialContext,
    sessionToken,
    context: chatContext,
    addAssistantMessage,
    addUserMessage,
    fetchWineRankings,
    precomputeRankings,
    proceedRecommendations
  } = useChat(venueSlug, 'b2c', accessToken, language)

  const [recommendedState, setRecommendedState] = useState({
    messageId: null,
    mode: null,
    wines: [],
    journeys: [],
    wineIds: []
  })

  useEffect(() => {
    loadVenueAndMenu()
  }, [venueSlug])

  useEffect(() => {
    // Reset recommended state when starting a new session or leaving chat
    if (!sessionToken || flowStep !== 'chat') {
      setRecommendedState({
        messageId: null,
        mode: null,
        wines: [],
        journeys: [],
        wineIds: []
      })
    }
  }, [sessionToken, flowStep])

  useEffect(() => {
    if (recommendedState.messageId) return
    const firstRecommendation = messages.find(
      msg =>
        msg.role === 'assistant' &&
        msg.metadata?.is_recommending &&
        ((msg.wines && msg.wines.length > 0) || (msg.journeys && msg.journeys.length > 0))
    )
    if (firstRecommendation) {
      setRecommendedState({
        messageId: firstRecommendation.id || firstRecommendation.message_id,
        mode: firstRecommendation.mode || (firstRecommendation.journeys?.length ? 'journey' : 'single'),
        wines: firstRecommendation.wines || [],
        journeys: firstRecommendation.journeys || [],
        wineIds: firstRecommendation.wine_ids || []
      })
    }
  }, [messages, recommendedState.messageId])

  // Show clarification hint when in clarification mode and recommendations exist
  useEffect(() => {
    if (messages.length === 0) {
      setShowClarificationHint(false)
      return
    }
    
    const lastMessage = messages[messages.length - 1]
    const isClarification = lastMessage?.metadata?.is_clarification === true
    const hasRecommendations = recommendedState.messageId !== null
    
    // Show hint if in clarification mode and recommendations exist
    setShowClarificationHint(isClarification && hasRecommendations)
  }, [messages, recommendedState.messageId])

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
      setVenueError(t('customerChat:errors.loadingVenue'))
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

  // Flow navigation - 5 steps: intro -> dishes -> guests -> wineType -> budget -> chat (journey step removed, defaults to 'single')
  const flowSteps = ['intro', 'dishes', 'guests', 'wineType', 'budget', 'chat']
  
  const canProceed = () => {
    switch (flowStep) {
      case 'intro': return true
      case 'dishes': return selectedDishes.length > 0
      case 'guests': return guestCount >= 1
      case 'wineType': return selectedWineType !== null
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
    const progressSteps = ['dishes', 'guests', 'wineType', 'budget']
    return progressSteps.indexOf(flowStep) + 1
  }

  // Track if we should send initial message
  const [shouldSendInitialMessage, setShouldSendInitialMessage] = useState(false)

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
    
    // Set context first
    if (setInitialContext) {
      setInitialContext(context)
    }
    
    // Mark that we should send initial message when sessionToken is ready
    setShouldSendInitialMessage(true)
  }
  
  // Send initial message when sessionToken is available
  useEffect(() => {
    if (shouldSendInitialMessage && sessionToken && chatContext) {
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
        const bottleWord = bottlesCount === 1 ? t('customerChat:guests.bottle') : t('customerChat:guests.bottles')
        initialMessage += ` Vogliamo un percorso di ${bottlesCount} ${bottleWord}.`
      }
      
      // Send initial message (hidden from display)
      // The backend will recognize this as initial context message and use opening prompt
      sendMessage(initialMessage, chatContext, { hidden: true })
      
      // Reset flag
      setShouldSendInitialMessage(false)
    }
  }, [shouldSendInitialMessage, sessionToken, chatContext, sendMessage, selectedDishes, guestCount, selectedWineType, selectedJourney, selectedBudget, budgetInput, bottlesCount])

  useEffect(() => {
    if (flowStep === 'chat' && sessionToken && chatContext && !precomputeStatus) {
      setPrecomputeStatus('loading')
      console.log('[CustomerChat] Starting precompute rankings...')
      precomputeRankings(chatContext).then((res) => {
        console.log('[CustomerChat] Precompute response:', res)
        if (res?.status === 'ready') {
          setPrecomputeStatus('ready')
          console.log('[CustomerChat] Precompute ready, wines:', res.wines_count, 'journeys:', res.journeys_count)
        } else if (res?.status === 'error') {
          setPrecomputeStatus('error')
          console.error('[CustomerChat] Precompute error:', res.error || res.message)
        } else {
          // Fallback - treat as ready to allow proceed to compute on-demand
          setPrecomputeStatus('ready')
          console.log('[CustomerChat] Precompute fallback to ready')
        }
      }).catch((err) => {
        console.error('[CustomerChat] Precompute failed:', err)
        setPrecomputeStatus('error')
      })
    }
  }, [flowStep, sessionToken, chatContext, precomputeStatus, precomputeRankings])

  useEffect(() => {
    if (!messages.length) return
    const lastMessage = messages[messages.length - 1]
    
    console.log('[CustomerChat] Last message check:', {
      role: lastMessage?.role,
      is_opening: lastMessage?.metadata?.is_opening,
      wines: lastMessage?.wines?.length,
      journeys: lastMessage?.journeys?.length
    })

    // Show button after opening message (or any assistant message without wines/journeys)
    if (lastMessage?.role === 'assistant') {
      const hasWines = lastMessage?.wines && lastMessage.wines.length > 0
      const hasJourneys = lastMessage?.journeys && lastMessage.journeys.length > 0
      
      if (hasWines || hasJourneys) {
        // Recommendations received - hide button
        console.log('[CustomerChat] Recommendations received, hiding proceed button')
        setShowProceedButton(false)
      } else if (lastMessage.metadata?.is_opening || (!hasWines && !hasJourneys && !lastMessage.metadata?.is_clarification)) {
        // Opening message or simple response without wines - show button
        console.log('[CustomerChat] Opening or simple message, showing proceed button')
        setShowProceedButton(true)
      }
    }
  }, [messages])
  
  // Filter messages to hide the initial automatic one
  const visibleMessages = messages.filter(m => !m.hidden)

  // Generate confirmation message with wine names
  const generateConfirmationMessage = (wines) => {
    if (!wines || wines.length === 0) {
      return t('customerChat:confirmations.multipleWinesSelected', { wineNames: '' })
    }

    const wineNames = wines.map(w => w.name || 'vino').join(' e ')
    return t('customerChat:confirmations.multipleWinesSelected', { wineNames })
  }

  // Generate continue message
  const generateContinueMessage = () => {
    return "Molto bene! Vorremmo valutare alternative per la selezione. Cos'altro ci proponi?"
  }

  const handleProceedSuggestions = async (userText = null) => {
    if (proceedLoading) return
    setProceedLoading(true)

    const autoUserText = (userText && userText.trim()) ? userText.trim() : 'Nessuna esigenza, procedi pure'
    console.log('[CustomerChat] handleProceedSuggestions called with:', autoUserText)
    
    // Show the user message in chat
    addUserMessage(autoUserText)

    try {
      console.log('[CustomerChat] Calling proceedRecommendations...')
      const response = await proceedRecommendations(autoUserText)
      console.log('[CustomerChat] proceedRecommendations response:', response)
      
      if (!response) {
        console.error('[CustomerChat] proceedRecommendations returned null/undefined')
        addAssistantMessage(t('customerChat:errors.loadingSuggestions'))
      } else if (response.status >= 400) {
        console.error('[CustomerChat] proceedRecommendations error status:', response.status)
        const errorMsg = response.data?.message || t('customerChat:errors.loadingSuggestionsError')
        addAssistantMessage(`⚠️ ${errorMsg}`)
      } else {
        console.log('[CustomerChat] Got recommendations, wines:', response.data?.wines?.length, 'hiding proceed button')
        setShowProceedButton(false)
      }
    } catch (err) {
      console.error('[CustomerChat] Error in handleProceedSuggestions:', err)
      const errorMsg = err.response?.data?.message || t('customerChat:errors.generic')
      addAssistantMessage(`⚠️ ${errorMsg}`)
    }
    
    setProceedLoading(false)
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
    const confirmationMsg = t('customerChat:confirmations.wineSelected', {
      wineName: selectedWine.name,
      price: selectedWine.price ? ` - €${selectedWine.price}` : ''
    })

    // Add confirmation message directly as assistant message (NO AI call)
    addAssistantMessage(confirmationMsg)
    setMessagesWithActionsHandled(prev => new Set([...prev, messageId]))
    
    // Hide proceed button after confirmation
    setShowProceedButton(false)
    
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

    const confirmationMsg = t('customerChat:confirmations.journeySelected', { wineList })

    // Add confirmation message directly as assistant message (NO AI call)
    addAssistantMessage(confirmationMsg)
    setMessagesWithActionsHandled(prev => new Set([...prev, messageId]))
    
    // Hide proceed button after confirmation
    setShowProceedButton(false)
    
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
      const thankYouMsg = t('customerChat:feedback.thankYou')
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
      // If we are still in opening stage (CTA visible), treat user input as "proceed"
      if (showProceedButton) {
        const text = inputValue.trim()
        setInputValue('')
        handleProceedSuggestions(text)
        return
      }

      sendMessage(inputValue)
      setInputValue('')
    }
  }

  // Show token error if any
  if (tokenError) {
    const isWifiError = tokenError === t('customerChat:errors.wifiRequired')

    return (
      <div className="min-h-screen bg-gradient-to-br from-burgundy-950 via-burgundy-900 to-burgundy-950 flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-10 h-10 text-red-400" />
          </div>
          <h2 className="font-display text-2xl font-bold text-cream-50 mb-4">
            {isWifiError ? t('customerChat:errors.wifiErrorTitle') : t('customerChat:errors.accessErrorTitle')}
          </h2>
          <p className="text-cream-100/70 mb-6">
            {isWifiError
              ? t('customerChat:errors.wifiErrorDescription')
              : tokenError
            }
          </p>
          {isWifiError && (
            <div className="bg-burgundy-800/50 rounded-xl p-4 mb-6 text-left">
              <p className="text-sm text-cream-100/80 mb-2">
                <strong className="text-gold-400">{t('customerChat:errors.wifiHowToTitle')}</strong>
              </p>
              <ol className="text-sm text-cream-100/70 list-decimal list-inside space-y-1">
                <li>{t('customerChat:errors.wifiHowToStep1')}</li>
                <li>{t('customerChat:errors.wifiHowToStep2')}</li>
                <li>{t('customerChat:errors.wifiHowToStep3')}</li>
              </ol>
            </div>
          )}
          {!isWifiError && (
            <p className="text-sm text-cream-100/50 mb-6">
              {t('customerChat:errors.scanAgain')}
            </p>
          )}
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-gold-500 text-burgundy-900 rounded-xl font-semibold hover:bg-gold-400 transition-colors"
          >
            {isWifiError ? t('common:buttons.retry') : t('customerChat:errors.reloadPage')}
          </button>
        </div>
      </div>
    )
  }
  
  // Show loading if token is still loading
  if (tokenLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-burgundy-950 via-burgundy-900 to-burgundy-950 flex items-center justify-center">
        <div className="text-center">
          <Logo size="xl" animate className="mx-auto mb-4" />
          <p className="text-cream-100/70">{t('common:loading')}</p>
        </div>
      </div>
    )
  }
  
  // Don't show venue if token is not available
  if (!accessToken) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-burgundy-950 via-burgundy-900 to-burgundy-950 flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-10 h-10 text-red-400" />
          </div>
          <h2 className="font-display text-2xl font-bold text-cream-50 mb-4">
            {t('customerChat:errors.accessTokenRequired')}
          </h2>
          <p className="text-cream-100/70 mb-6">
            {t('customerChat:errors.accessTokenDescription')}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-gold-500 text-burgundy-900 rounded-xl font-semibold hover:bg-gold-400 transition-colors"
          >
            {t('customerChat:errors.reloadPage')}
          </button>
        </div>
      </div>
    )
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
            {t('common:error')}
          </h2>
          <p className="text-cream-100/70 mb-6">{venueError}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-gold-500 text-burgundy-900 rounded-xl font-semibold hover:bg-gold-400 transition-colors"
          >
            {t('common:buttons.retry')}
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
          <p className="text-cream-100/70">{t('common:loading')}</p>
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
                <p className="text-xs text-cream-100/70">{t('customerChat:intro.subtitle')}</p>
              </div>
            </div>
            <LanguageSwitcher disabled={!!sessionToken} />
          </div>
        </header>

        {/* Progress indicator - 4 main steps (excluding intro and journey) */}
        {flowStep !== 'intro' && (
          <div className="max-w-2xl mx-auto px-4 pt-6">
            <div className="flex gap-2 mb-8">
              {['dishes', 'guests', 'wineType', 'budget'].map((step, idx) => (
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
                  {t('customerChat:intro.welcome')}
                </motion.h2>

                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.6 }}
                  className="bg-burgundy-800/50 rounded-2xl p-6 max-w-md mx-auto"
                >
                  <p className="text-cream-100 text-lg leading-relaxed mb-4" dangerouslySetInnerHTML={{
                    __html: t('customerChat:intro.description', { venueName: venue?.name || 'questo ristorante' })
                  }} />
                  <p className="text-cream-100/80 leading-relaxed">
                    {t('customerChat:intro.descriptionDetails')}
                  </p>
                </motion.div>

                {/* Language Selection */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.8 }}
                  className="mt-8"
                >
                  <p className="text-cream-100/70 text-sm mb-3">
                    {t('customerChat:intro.selectLanguage')}
                  </p>
                  <div className="flex justify-center gap-4">
                    <button
                      onClick={() => {
                        i18n.changeLanguage('it')
                        setLanguage('it')
                      }}
                      className={`flex items-center gap-3 px-6 py-3 rounded-xl transition-all ${
                        language === 'it'
                          ? 'bg-gold-500 text-burgundy-900 shadow-lg scale-105'
                          : 'bg-burgundy-800/50 text-cream-50 hover:bg-burgundy-700/50'
                      }`}
                    >
                      <span className="text-3xl">🇮🇹</span>
                      <span className="font-semibold">Italiano</span>
                    </button>
                    <button
                      onClick={() => {
                        i18n.changeLanguage('en')
                        setLanguage('en')
                      }}
                      className={`flex items-center gap-3 px-6 py-3 rounded-xl transition-all ${
                        language === 'en'
                          ? 'bg-gold-500 text-burgundy-900 shadow-lg scale-105'
                          : 'bg-burgundy-800/50 text-cream-50 hover:bg-burgundy-700/50'
                      }`}
                    >
                      <span className="text-3xl">🇬🇧</span>
                      <span className="font-semibold">English</span>
                    </button>
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1.0 }}
                  className="mt-6 flex justify-center gap-3"
                >
                  <span className="inline-flex items-center gap-2 px-4 py-2 bg-burgundy-800/50 rounded-full text-cream-100/70 text-sm">
                    <Sparkles className="w-4 h-4 text-gold-400" />
                    {t('customerChat:intro.poweredBy')}
                  </span>
                </motion.div>
              </motion.div>
            )}

            {/* Step 1: Dish Selection - Mobile Optimized */}
            {flowStep === 'dishes' && (
              <motion.div
                key="dishes"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="flex flex-col h-[65vh] md:h-[60vh]"
              >
                <div className="mb-4">
                  <h2 className="font-display text-2xl font-bold text-cream-50 mb-1">
                    {t('customerChat:dishes.title')}
                  </h2>
                  <p className="text-cream-100/70 text-sm">
                    {t('customerChat:dishes.subtitle')}
                  </p>
                </div>

                {menuItems.length > 0 ? (
                  <DishSelector
                    menuItems={menuItems}
                    selectedDishes={selectedDishes}
                    onToggleDish={toggleDish}
                    categoryLabels={categoryLabels}
                  />
                ) : (
                  <div className="text-center py-12 flex-1 flex flex-col items-center justify-center">
                    <Wine className="w-12 h-12 text-burgundy-600 mx-auto mb-4" />
                    <p className="text-cream-100/70">
                      {t('customerChat:dishes.emptyMenu')}
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
                  {t('customerChat:guests.title')}
                </h2>
                <p className="text-cream-100/70 mb-8">
                  {t('customerChat:guests.subtitle')}
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
                  {t('common:guest', { count: guestCount })}
                </p>

                {/* Bottles suggestion */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="mt-8 bg-burgundy-800/30 rounded-xl p-4 border border-gold-500/20 max-w-md mx-auto"
                >
                  <p className="text-sm text-cream-100/90" dangerouslySetInnerHTML={{
                    __html: t('customerChat:guests.bottlesSuggestion', {
                      bottlesCount: calculateBottlesNeeded(guestCount),
                      bottlesWord: calculateBottlesNeeded(guestCount) === 1 ? t('customerChat:guests.bottle') : t('customerChat:guests.bottles'),
                      guestCount: guestCount,
                      guestsWord: t('common:guest', { count: guestCount })
                    })
                  }} />
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
                    {t('customerChat:wineType.title')}
                  </h2>
                  <p className="text-cream-100/70">
                    {t('customerChat:wineType.subtitle')}
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

            {/* Step 4: Journey selection removed - defaulting to 'single' label only */}
            {/* Journey step UI commented out - will be developed in the future for multi-label support */}

            {/* Step 4: Budget (renumbered from Step 5) */}
            {flowStep === 'budget' && (
              <motion.div
                key="budget"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <div className="text-center mb-8">
                  <h2 className="font-display text-2xl font-bold text-cream-50 mb-2">
                    {t('customerChat:budget.title')}
                  </h2>
                  <p className="text-cream-100/70">
                    {t('customerChat:budget.subtitle')}
                  </p>
                </div>

                <div className="space-y-4">
                  {/* Budget input */}
                  <div className="bg-burgundy-800/30 rounded-xl p-5 border border-burgundy-700/30">
                    <label className="block text-cream-50 font-semibold mb-3">
                      {t('customerChat:budget.inputLabel')}
                    </label>
                    <div className="flex gap-3">
                      <div className="flex-1">
                        <div className="relative">
                          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-cream-100/70 font-semibold">€</span>
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            placeholder={t('customerChat:budget.inputPlaceholder')}
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
                          {t('customerChat:budget.inputHint')}
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
                      <div className="font-semibold text-lg">{t('customerChat:budget.noRestriction')}</div>
                      <div className={`text-sm mt-1 ${selectedBudget === 'nolimit' ? 'text-burgundy-700' : 'text-cream-100/60'}`}>
                        {t('customerChat:budget.noRestrictionDescription')}
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
                {t('common:buttons.back')}
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
                  {t('customerChat:intro.startButton')}
                </>
              ) : flowStep === 'budget' ? (
                <>
                  <Sparkles className="w-5 h-5" />
                  {t('customerChat:buttons.askSommelier')}
                </>
              ) : (
                t('customerChat:buttons.continue')
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
              <p className="text-xs text-cream-100/70">{t('customerChat:chat.personalSommelier')}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Simplified context summary - only dishes and guests */}
      <div className="bg-burgundy-800 text-cream-100 px-4 py-2 text-sm">
        <div className="max-w-2xl mx-auto flex flex-wrap gap-4">
          <span className="flex items-center gap-1">
            <Users className="w-4 h-4 text-gold-400" />
            {guestCount} {t('common:guest', { count: guestCount })}
          </span>
          <span className="flex items-center gap-1 text-cream-100/70">
            <Wine className="w-4 h-4 text-gold-400" />
            {selectedDishes.length} {t('customerChat:chat.dishesSelected')}
          </span>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-2 md:px-4 py-4 md:py-6">
        <div className="max-w-2xl mx-auto space-y-4 w-full">
          <AnimatePresence mode="popLayout">
            {visibleMessages.map((message, msgIdx) => {
              const isAssistant = message.role === 'assistant'
              
              // Show cards ONLY in the message from communication model (is_recommending)
              const isRecommendationMessage = isAssistant && message.metadata?.is_recommending === true
              const displayMode = isRecommendationMessage ? (message.mode || 'single') : null
              const displayWines = isRecommendationMessage ? (message.wines || []) : []
              const displayJourneys = isRecommendationMessage ? (message.journeys || []) : []
              
              // Use message ID for actions (buttons, selections)
              const actionMessageId = message.id
              const rankingsMessageId =
                message.metadata?.rankings_message_id ||
                message.message_id ||
                message.id

              return (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className={message.role === 'user' ? 'flex justify-end' : 'flex justify-start'}
                >
                {message.role === 'assistant' ? (
                  <div className="flex gap-2 md:gap-3 max-w-[90%] md:max-w-[85%] w-full">
                    <div className="w-8 h-8 md:w-10 md:h-10 bg-gradient-to-br from-gold-400 to-gold-600 rounded-full flex items-center justify-center flex-shrink-0 shadow-md">
                      <Wine className="w-4 h-4 md:w-5 md:h-5 text-burgundy-900" />
                    </div>
                    <div className="space-y-2 md:space-y-3 flex-1 min-w-0">
                      {/* Render message content - always show if exists or if we have wines/journeys */}
                      {(message.content && message.content.trim()) || (displayWines && displayWines.length > 0) || (displayJourneys && displayJourneys.length > 0) ? (
                        message.content && message.content.trim() ? (
                      <div className="bg-white rounded-xl md:rounded-2xl rounded-tl-sm px-3 md:px-4 py-2 md:py-3 shadow-sm border border-burgundy-100 overflow-x-hidden">
                        {/* Render markdown formatted message */}
                        <div className="text-burgundy-800 leading-relaxed prose prose-burgundy prose-sm max-w-none break-words overflow-wrap-anywhere">
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
                              {t('customerChat:chat.fallbackRecommendation')}
                            </p>
                          </div>
                        )
                      ) : null}
                      
                      {/* Wine suggestions - SINGLE mode (wines array) */}
                      {displayMode !== 'journey' && displayWines && displayWines.length > 0 && (
                        <motion.div 
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.3 }}
                          className="space-y-3"
                        >
                          <p className="text-xs text-burgundy-500 font-medium uppercase tracking-wide flex items-center gap-1">
                            <Sparkles className="w-3 h-3" />
                            {t('customerChat:chat.recommendations')}
                          </p>
                          
                          {/* All recommended wines - show all as selectable cards (max 3) */}
                          {displayWines.length > 0 && (
                            <div className="space-y-2 w-full overflow-x-hidden">
                              {(displayWines || []).slice(0, 3).map((wine, idx) => (
                                <div key={wine.id || idx} className="w-full">
                                  <WineCard 
                                    wine={wine} 
                                    isMainRecommendation={wine.best === true || (wine.best === undefined && idx === 0)}
                                    selected={selectedWineByMessage[actionMessageId] === wine.id || 
                                             (selectedWineByMessage[actionMessageId] === undefined && (wine.best === true || (wine.best === undefined && idx === 0)) && wine.id)}
                                    onClick={() => setSelectedWineByMessage(prev => ({
                                      ...prev,
                                      [actionMessageId]: wine.id
                                    }))}
                                  />
                                </div>
                              ))}
                            </div>
                          )}
                          
                          {/* Action buttons - only show if not already handled */}
                          {!messagesWithActionsHandled.has(actionMessageId) && (
                            <motion.div
                              initial={{ opacity: 0, y: 5 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: 0.5 }}
                              className="flex flex-col sm:flex-row gap-2 md:gap-3 pt-2 w-full"
                            >
                              <button
                                onClick={() => {
                                  const selectedWineId = selectedWineByMessage[actionMessageId] || displayWines[0]?.id
                                  if (selectedWineId) {
                                    handleConfirmSingleWine(actionMessageId, selectedWineId, displayWines)
                                  }
                                }}
                                disabled={isLoading || (!selectedWineByMessage[actionMessageId] && !displayWines[0]?.id)}
                                className="flex-1 flex items-center justify-center gap-2 px-3 md:px-4 py-2.5 md:py-3 bg-green-600 text-white rounded-lg md:rounded-xl text-sm md:text-base font-semibold hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                              >
                                <CheckCircle2 className="w-4 h-4 md:w-5 md:h-5 flex-shrink-0" />
                                <span className="truncate">{t('customerChat:chat.confirmWine')}</span>
                              </button>
                              <button
                                onClick={async () => {
                                  setModalMessageId(actionMessageId)
                                  setLoadingRankings(true)
                                  setShowAllWinesModal(true)

                                  // Fetch rankings from API using message_id from server
                                  try {
                                    if (rankingsMessageId) {
                                      const rankings = await fetchWineRankings(rankingsMessageId)
                                      if (rankings && rankings.length > 0) {
                                        setModalWines(rankings)
                                      } else {
                                        // Fallback to all_rankings from message
                                        const messageRankings = message.all_rankings || displayWines || []
                                        setModalWines(messageRankings)
                                      }
                                    } else {
                                      // No message_id available, use fallback
                                      const messageRankings = message.all_rankings || displayWines || []
                                      setModalWines(messageRankings)
                                    }
                                  } catch (err) {
                                    console.error('Error fetching rankings:', err)
                                    // Fallback to all_rankings from message
                                    const messageRankings = message.all_rankings || displayWines || []
                                    setModalWines(messageRankings)
                                  } finally {
                                    setLoadingRankings(false)
                                  }
                                }}
                                disabled={isLoading}
                                className="flex-1 flex items-center justify-center gap-2 px-3 md:px-4 py-2.5 md:py-3 bg-gold-500 text-burgundy-900 rounded-lg md:rounded-xl text-sm md:text-base font-semibold hover:bg-gold-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                              >
                                <Star className="w-4 h-4 md:w-5 md:h-5 flex-shrink-0" />
                                <span className="truncate">{t('customerChat:chat.viewAllWines')}</span>
                              </button>
                            </motion.div>
                          )}
                        </motion.div>
                      )}
                      
                      {/* Journey suggestions - JOURNEY mode */}
                      {displayMode === 'journey' && displayJourneys && displayJourneys.length > 0 && (
                        <motion.div 
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.3 }}
                          className="space-y-4"
                        >
                          <p className="text-xs text-burgundy-500 font-medium uppercase tracking-wide flex items-center gap-1">
                            <Sparkles className="w-3 h-3" />
                            {t('customerChat:chat.journeyRecommendations')}
                          </p>
                          
                          {displayJourneys.map((journey, journeyIdx) => (
                            <div 
                              key={journey.id || journeyIdx}
                              className={`p-4 rounded-xl border-2 transition-all ${
                                selectedJourneyByMessage[actionMessageId] === journey.id
                                  ? 'border-gold-500 bg-gold-50/30 shadow-md'
                                  : 'border-burgundy-100 bg-white'
                              }`}
                            >
                              <div className="flex items-start justify-between mb-3 gap-3">
                                <div className="flex-1">
                                  <h4 className="font-display font-semibold text-burgundy-900 text-base md:text-lg break-words">
                                    {journey.name || t('customerChat:chat.journeyName', { number: journeyIdx + 1 })}
                                  </h4>
                                </div>
                                <div className="flex gap-2 flex-shrink-0">
                                  {(journey.reason || journey.description) && (
                                    <button
                                      onClick={() => setSelectedJourneyDetails(prev => ({
                                        ...prev,
                                        [actionMessageId]: journey.id
                                      }))}
                                      className="px-3 py-2 rounded-lg font-medium text-sm transition-colors bg-burgundy-100 text-burgundy-700 hover:bg-burgundy-200"
                                    >
                                      {t('customerChat:chat.journeyDetails')}
                                    </button>
                                  )}
                                  <button
                                    onClick={() => setSelectedJourneyByMessage(prev => ({
                                      ...prev,
                                      [actionMessageId]: journey.id
                                    }))}
                                    className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                                      selectedJourneyByMessage[actionMessageId] === journey.id
                                        ? 'bg-gold-500 text-burgundy-900'
                                        : 'bg-burgundy-700 text-cream-50 hover:bg-burgundy-600'
                                    }`}
                                  >
                                    {selectedJourneyByMessage[actionMessageId] === journey.id ? t('customerChat:chat.journeySelected') : t('customerChat:chat.selectJourney')}
                                  </button>
                                </div>
                              </div>
                              
                              
                              <div className="space-y-2">
                                {journey.wines && journey.wines.map((wine, wineIdx) => (
                                  <WineCard key={wine.id || wineIdx} wine={wine} />
                                ))}
                              </div>
                              
                              {/* Journey Details Modal */}
                              <JourneyDetailsModal
                                journey={journey}
                                isOpen={selectedJourneyDetails[actionMessageId] === journey.id}
                                onClose={() => setSelectedJourneyDetails(prev => ({
                                  ...prev,
                                  [actionMessageId]: null
                                }))}
                              />
                            </div>
                          ))}
                          
                          {/* Action buttons - only show if not already handled */}
                          {!messagesWithActionsHandled.has(actionMessageId) && (
                            <motion.div
                              initial={{ opacity: 0, y: 5 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: 0.5 }}
                              className="flex gap-3 pt-2"
                            >
                              <button
                                onClick={() => {
                                  const selectedJourneyId = selectedJourneyByMessage[actionMessageId]
                                  if (selectedJourneyId) {
                                    handleConfirmJourney(actionMessageId, selectedJourneyId, displayJourneys)
                                  }
                                }}
                                disabled={isLoading || !selectedJourneyByMessage[actionMessageId]}
                                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                              >
                                <CheckCircle2 className="w-5 h-5" />
                                {t('customerChat:chat.confirmJourney')}
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
            )
          })}
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
                <p className="text-red-800 font-medium mb-1">{t('customerChat:chat.connectionError')}</p>
                <p className="text-red-600 text-sm">{error}</p>
                <button
                  onClick={() => sendMessage(inputValue || t('common:buttons.retry'))}
                  className="mt-2 text-sm text-red-700 underline hover:text-red-900"
                >
                  {t('customerChat:chat.retryError')}
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
                    {t('customerChat:feedback.title')}
                  </h3>
                  <p className="text-sm text-cream-100/70">
                    {t('customerChat:feedback.subtitle')}
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
                    placeholder={t('customerChat:feedback.commentPlaceholder')}
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
                    {t('customerChat:feedback.skipButton')}
                  </button>
                  <button
                    onClick={handleSubmitFeedback}
                    disabled={rating === 0 || submittingFeedback}
                    className="flex-1 px-4 py-3 bg-gold-500 text-burgundy-900 rounded-xl font-semibold hover:bg-gold-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {submittingFeedback ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        {t('customerChat:feedback.submitting')}
                      </>
                    ) : (
                      <>
                        <Check className="w-4 h-4" />
                        {t('customerChat:feedback.submitButton')}
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
              // Modal remains open so user can see selection and select another wine if needed
            }
          }}
          selectedWineId={modalMessageId ? selectedWineByMessage[modalMessageId] : null}
        />
      )}

      {/* Proceed CTA */}
      {flowStep === 'chat' && showProceedButton && (
        <div className="border-t border-burgundy-100 bg-white px-4 pt-4">
          <div className="max-w-2xl mx-auto">
            {precomputeStatus === 'loading' ? (
              <div className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-100 text-gray-600 rounded-xl font-medium">
                <RefreshCw className="w-4 h-4 animate-spin" />
                {t('customerChat:chat.preparingOptions')}
              </div>
            ) : precomputeStatus === 'error' ? (
              <button
                onClick={() => {
                  setPrecomputeStatus(null) // Trigger retry
                }}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-orange-500 text-white rounded-xl font-semibold hover:bg-orange-600 transition-colors shadow-sm"
              >
                <RefreshCw className="w-4 h-4" />
                {t('customerChat:chat.retryLoading')}
              </button>
            ) : (
              <button
                onClick={() => handleProceedSuggestions()}
                disabled={proceedLoading}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              >
                {proceedLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    {t('customerChat:chat.proceedLoading')}
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    {t('customerChat:chat.proceedButton')}
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Clarification Hint - Show when in clarification mode */}
      {showClarificationHint && (
        <div className="border-t border-burgundy-100 bg-white px-4 py-3">
          <div className="max-w-2xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="px-4 py-3 bg-gold-50 border-l-4 border-gold-500 rounded-lg"
            >
              <p className="text-burgundy-900 font-medium flex items-center gap-2">
                <ArrowUp className="w-5 h-5 text-gold-600" />
                {t('customerChat:chat.clarificationHint')}
              </p>
            </motion.div>
          </div>
        </div>
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
              placeholder={t('customerChat:chat.inputPlaceholder')}
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

