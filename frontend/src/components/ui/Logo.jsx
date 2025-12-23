import { motion } from 'framer-motion'
import { useState } from 'react'

/**
 * Logo component for LIBER
 * Replaces the wine glass icon throughout the application
 */
function Logo({ className = '', size = 'md', animate = false }) {
  const [imgError, setImgError] = useState(false)
  
  // Size mapping to actual pixel values (increased sizes for better visibility)
  const sizeMap = {
    xs: { width: 24, height: 24 },      // was 16
    sm: { width: 36, height: 36 },      // was 24
    md: { width: 48, height: 48 },      // was 32
    lg: { width: 72, height: 72 },      // was 48
    xl: { width: 96, height: 96 }       // was 64
  }
  
  const sizeClasses = {
    xs: 'w-6 h-6',      // was w-4 h-4
    sm: 'w-9 h-9',      // was w-6 h-6
    md: 'w-12 h-12',    // was w-8 h-8
    lg: 'w-[72px] h-[72px]',    // was w-12 h-12
    xl: 'w-24 h-24'     // was w-16 h-16
  }
  
  const sizeClass = sizeClasses[size] || sizeClasses.md
  const dimensions = sizeMap[size] || sizeMap.md
  
  const content = imgError ? (
    <span className="font-display font-bold text-burgundy-900">LIBER</span>
  ) : (
    <img 
      src="/logo.svg" 
      alt="LIBER" 
      className={className}
      style={{ 
        display: 'block',
        width: `${dimensions.width}px`,
        height: `${dimensions.height}px`,
        objectFit: 'contain',
        objectPosition: 'center',
        flexShrink: 0
      }}
      onError={() => {
        console.warn('Logo SVG failed to load, using text fallback')
        setImgError(true)
      }}
      onLoad={() => {
        console.log('Logo SVG loaded successfully')
      }}
    />
  )
  
  const wrapper = (
    <div 
      className={`${sizeClass} flex items-center justify-center flex-shrink-0 ${className}`}
      style={{
        minWidth: `${dimensions.width}px`,
        minHeight: `${dimensions.height}px`
      }}
    >
      {content}
    </div>
  )
  
  if (animate) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        {wrapper}
      </motion.div>
    )
  }
  
  return wrapper
}

export default Logo

