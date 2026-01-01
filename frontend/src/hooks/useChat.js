import { useState, useCallback, useRef, useEffect } from 'react'
import { chatService } from '../services/api'

export function useChat(venueSlug = null, mode = 'b2c') {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sessionToken, setSessionToken] = useState(null)
  const [context, setContext] = useState(null) // Customer context (dishes, guest_count)
  const messagesEndRef = useRef(null)
  const isInitializingRef = useRef(false) // Prevent multiple simultaneous session creation calls

  // Initialize session for B2C mode
  const initializeSession = useCallback(async () => {
    // Prevenire chiamate multiple simultanee
    if (isInitializingRef.current) {
      return
    }
    
    isInitializingRef.current = true
    try {
      const response = await chatService.createSession(venueSlug)
      setSessionToken(response.data.session_token)
    } catch (err) {
      console.error('Failed to create session:', err)
      // Create local session token for fallback
      setSessionToken(`local-${Date.now()}`)
    } finally {
      isInitializingRef.current = false
    }
  }, [venueSlug])

  // Initialize session for B2C mode
  useEffect(() => {
    if (mode === 'b2c' && venueSlug && !sessionToken) {
      initializeSession()
    }
  }, [venueSlug, mode, sessionToken, initializeSession])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Set initial context from setup flow
  const setInitialContext = useCallback((newContext) => {
    setContext(newContext)
  }, [])

  const sendMessage = useCallback(async (content, initialContext = null, options = {}) => {
    if (!content.trim()) return

    // Use provided context or stored context
    const messageContext = initialContext || context
    
    // Check if this is the first message (hidden from display)
    const isInitialMessage = options.hidden || false

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
      hidden: isInitialMessage // Flag to hide this message in the UI
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    try {
      let response
      
      if (mode === 'b2c') {
        response = await chatService.sendMessage(sessionToken, content, messageContext)
      } else {
        throw new Error('Modalità non supportata. Solo B2C è disponibile.')
      }

      // Ensure message content is always a string
      const messageContent = response.data.message || response.data.content || ''
      
      const assistantMessage = {
        id: response.data.message_id?.toString() || (Date.now() + 1).toString(), // Use server message_id if available
        message_id: response.data.message_id, // Store server message_id for API calls
        role: 'assistant',
        content: messageContent,
        suggestions: response.data.suggestions || [],
        wines: response.data.wines || [],
        all_rankings: response.data.all_rankings || [], // Tutti i vini rankati per il modal "Valuta tutti"
        journeys: response.data.journeys || [],
        mode: response.data.mode || 'single',
        metadata: response.data.metadata || {},
        timestamp: new Date().toISOString()
      }
      
      // Log for debugging
      if (!messageContent) {
        console.warn('Received empty message from API:', response.data)
      }

      setMessages(prev => [...prev, assistantMessage])
      setError(null)
      
    } catch (err) {
      console.error('Chat error:', err)
      
      // Extract error message
      let errorMessage = 'Errore di connessione. Verifica la tua connessione internet e riprova.'
      
      if (err.response?.data?.message) {
        errorMessage = err.response.data.message
      } else if (err.response?.status === 401) {
        errorMessage = 'Sessione scaduta. Ricarica la pagina.'
      } else if (err.response?.status === 500) {
        errorMessage = 'Errore del server. Il servizio AI potrebbe non essere configurato correttamente.'
      } else if (err.response?.status === 503) {
        errorMessage = 'Servizio temporaneamente non disponibile. Riprova tra qualche secondo.'
      } else if (err.message) {
        errorMessage = err.message
      }
      
      // Add error as assistant message so user sees what happened
      const errorAssistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `⚠️ ${errorMessage}`,
        isError: true,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorAssistantMessage])
      setError(errorMessage)
      
    } finally {
      setIsLoading(false)
    }
  }, [sessionToken, mode, context])

  const clearMessages = useCallback(() => {
    setMessages([])
    setSessionToken(null)
    setContext(null)
    setError(null)
    isInitializingRef.current = false // Reset initialization flag
    if (mode === 'b2c' && venueSlug) {
      initializeSession()
    }
  }, [venueSlug, mode, initializeSession])

  // Retry last failed message
  const retryLastMessage = useCallback((content) => {
    setError(null)
    sendMessage(content, context)
  }, [sendMessage, context])

  // Add a direct assistant message without calling AI (for confirmation templates)
  const addAssistantMessage = useCallback((content) => {
    const assistantMessage = {
      id: Date.now().toString(),
      role: 'assistant',
      content: content,
      timestamp: new Date().toISOString(),
      isConfirmation: true // Flag to indicate this is a confirmation message
    }
    setMessages(prev => [...prev, assistantMessage])
  }, [])

  // Fetch wine rankings for a message from the database
  const fetchWineRankings = useCallback(async (messageId) => {
    try {
      const response = await chatService.getMessageRankings(messageId)
      return response.data.wines || []
    } catch (err) {
      console.error('Error fetching wine rankings:', err)
      // Return empty array on error - fallback will be used
      return []
    }
  }, [])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    retryLastMessage,
    messagesEndRef,
    sessionToken,
    setInitialContext,
    context,
    addAssistantMessage,
    fetchWineRankings
  }
}

export default useChat
