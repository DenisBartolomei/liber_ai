import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

function LoadingSpinner({ size = 'md', className = '' }) {
  const sizes = {
    sm: 'w-5 h-5',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  }

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <motion.div
        className={`${sizes[size]} border-3 border-burgundy-200 border-t-burgundy-900 rounded-full`}
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        style={{ borderWidth: '3px' }}
      />
    </div>
  )
}

export function LoadingDots() {
  return (
    <div className="flex items-center space-x-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-2 h-2 bg-burgundy-400 rounded-full"
          animate={{ y: [0, -6, 0] }}
          transition={{
            duration: 0.6,
            repeat: Infinity,
            delay: i * 0.15
          }}
        />
      ))}
    </div>
  )
}

export function ThinkingMessages() {
  const messages = [
    'Elaboro le preferenze',
    'Analizzo la carta dei vini',
    'Scelgo vini appropriati'
  ]

  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % messages.length)
    }, 2000) // Cambia messaggio ogni 2 secondi

    return () => clearInterval(interval)
  }, [messages.length])

  return (
    <div className="flex items-center gap-2">
      <AnimatePresence mode="wait">
        <motion.span
          key={currentIndex}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
          className="text-sm text-burgundy-700"
        >
          {messages[currentIndex]}
        </motion.span>
      </AnimatePresence>
      <motion.div
        className="flex items-center space-x-1 ml-1"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-1.5 h-1.5 bg-burgundy-400 rounded-full"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{
              duration: 1.2,
              repeat: Infinity,
              delay: i * 0.2
            }}
          />
        ))}
      </motion.div>
    </div>
  )
}

export default LoadingSpinner

