import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Wine, Sparkles, Trash2, RefreshCw } from 'lucide-react'
import { useChat } from '../hooks/useChat'
import { LoadingDots } from '../components/ui/LoadingSpinner'
import WineCard from '../components/chat/WineCard'

function DashboardChat() {
  const [inputValue, setInputValue] = useState('')
  const inputRef = useRef(null)
  const { 
    messages, 
    isLoading, 
    error, 
    sendMessage, 
    clearMessages,
    messagesEndRef 
  } = useChat(null, 'b2b')

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      // The welcome message will be set by the hook
    }
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (inputValue.trim() && !isLoading) {
      sendMessage(inputValue)
      setInputValue('')
    }
  }

  const quickSuggestions = [
    'Quali vini rossi consigli per un menu a base di carne?',
    'Suggeriscimi vini con un buon rapporto qualità-prezzo',
    'Ho bisogno di bollicine per aperitivi, cosa consigli?',
    'Quali vini biologici sono di tendenza?',
    'Aiutami a rinnovare la sezione bianchi'
  ]

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-3xl font-bold text-burgundy-900 flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-gold-500" />
            Assistente AI
          </h1>
          <p className="text-burgundy-600 mt-1">
            Chiedi consigli per la tua carta vini
          </p>
        </div>
        <button
          onClick={clearMessages}
          className="btn-outline flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Nuova Chat
        </button>
      </div>

      {/* Chat Container */}
      <div className="flex-1 flex flex-col card overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-20 h-20 bg-gold-100 rounded-2xl flex items-center justify-center mb-6">
                <Sparkles className="w-10 h-10 text-gold-600" />
              </div>
              <h2 className="font-display text-xl font-semibold text-burgundy-900 mb-2">
                Come posso aiutarti?
              </h2>
              <p className="text-burgundy-600 mb-8 max-w-md">
                Sono qui per aiutarti a selezionare i vini perfetti per la tua carta. 
                Chiedimi consigli su tipologie, abbinamenti, trend e molto altro.
              </p>
              <div className="flex flex-wrap justify-center gap-2 max-w-2xl">
                {quickSuggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInputValue(suggestion)
                      inputRef.current?.focus()
                    }}
                    className="px-4 py-2 bg-cream-50 border border-burgundy-200 rounded-lg text-sm text-burgundy-700 hover:border-gold-400 hover:bg-gold-50 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              <AnimatePresence mode="popLayout">
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className={message.role === 'user' ? 'flex justify-end' : 'flex justify-start'}
                  >
                    {message.role === 'assistant' ? (
                      <div className="flex gap-3 max-w-[85%]">
                        <div className="w-10 h-10 bg-gold-500 rounded-xl flex items-center justify-center flex-shrink-0">
                          <Sparkles className="w-5 h-5 text-burgundy-900" />
                        </div>
                        <div className="space-y-3">
                          <div className="chat-bubble-ai">
                            <p className="whitespace-pre-wrap">{message.content}</p>
                          </div>
                          
                          {/* Wine suggestions */}
                          {message.wines && message.wines.length > 0 && (
                            <div className="grid gap-3">
                              {message.wines.map((wine, idx) => (
                                <WineCard key={idx} wine={wine} />
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="chat-bubble-user">
                        <p>{message.content}</p>
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
                  <div className="w-10 h-10 bg-gold-500 rounded-xl flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-burgundy-900" />
                  </div>
                  <div className="chat-bubble-ai">
                    <LoadingDots />
                  </div>
                </motion.div>
              )}

              {/* Error */}
              {error && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center py-4"
                >
                  <p className="text-red-600 text-sm">{error}</p>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-burgundy-100 p-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Scrivi un messaggio..."
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
          </form>
        </div>
      </div>
    </div>
  )
}

export default DashboardChat

