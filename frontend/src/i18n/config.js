import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

// Import translation files
import commonIT from './locales/it/common.json'
import customerChatIT from './locales/it/customerChat.json'
import errorsIT from './locales/it/errors.json'

import commonEN from './locales/en/common.json'
import customerChatEN from './locales/en/customerChat.json'
import errorsEN from './locales/en/errors.json'

const resources = {
  it: {
    common: commonIT,
    customerChat: customerChatIT,
    errors: errorsIT
  },
  en: {
    common: commonEN,
    customerChat: customerChatEN,
    errors: errorsEN
  }
}

i18n
  // Detect user language
  .use(LanguageDetector)
  // Pass the i18n instance to react-i18next
  .use(initReactI18next)
  // Init i18next
  .init({
    resources,
    fallbackLng: 'it', // Default to Italian
    defaultNS: 'common',
    ns: ['common', 'customerChat', 'errors'],

    detection: {
      // Order of language detection
      order: ['localStorage', 'navigator'],
      // Keys to look for in localStorage
      lookupLocalStorage: 'language-storage',
      // Cache user language
      caches: ['localStorage'],
    },

    interpolation: {
      escapeValue: false // React already escapes values
    },

    react: {
      useSuspense: false // Disable suspense for now
    }
  })

export default i18n
