import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLanguageStore } from '../../stores/languageStore'
import { Globe } from 'lucide-react'

/**
 * Language switcher component with flag buttons
 * Allows users to switch between Italian and English
 * Can be disabled to prevent language changes during active sessions
 */
function LanguageSwitcher({ disabled = false }) {
  const { i18n } = useTranslation()
  const { language, setLanguage } = useLanguageStore()
  const [isOpen, setIsOpen] = useState(false)

  const handleLanguageChange = (lang) => {
    if (disabled) return

    // Update i18next
    i18n.changeLanguage(lang)
    // Update Zustand store (which persists to localStorage)
    setLanguage(lang)
    setIsOpen(false)
  }

  const languages = [
    { code: 'it', label: 'Italiano', flag: '🇮🇹' },
    { code: 'en', label: 'English', flag: '🇬🇧' }
  ]

  const currentLanguage = languages.find(lang => lang.code === language)

  return (
    <div className="relative">
      <button
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg
          border border-gray-300 bg-white
          hover:bg-gray-50 transition-colors
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        title={disabled ? "Language cannot be changed during an active session" : "Change language"}
      >
        <Globe className="w-4 h-4 text-gray-600" />
        <span className="text-2xl">{currentLanguage?.flag}</span>
        <span className="text-sm font-medium text-gray-700">{currentLanguage?.code.toUpperCase()}</span>
      </button>

      {isOpen && !disabled && (
        <>
          {/* Backdrop to close dropdown when clicking outside */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown menu */}
          <div className="absolute right-0 mt-2 w-48 rounded-lg border border-gray-200 bg-white shadow-lg z-20 overflow-hidden">
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLanguageChange(lang.code)}
                className={`
                  w-full flex items-center gap-3 px-4 py-3
                  hover:bg-gray-50 transition-colors text-left
                  ${language === lang.code ? 'bg-purple-50 border-l-4 border-purple-600' : ''}
                `}
              >
                <span className="text-2xl">{lang.flag}</span>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">{lang.label}</div>
                  <div className="text-xs text-gray-500">{lang.code.toUpperCase()}</div>
                </div>
                {language === lang.code && (
                  <div className="w-2 h-2 rounded-full bg-purple-600" />
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default LanguageSwitcher
