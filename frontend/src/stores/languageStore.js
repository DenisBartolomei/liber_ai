import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * Language store for managing user's language preference
 * Persists to localStorage for session memory
 */
export const useLanguageStore = create(
  persist(
    (set) => ({
      language: 'it', // Default to Italian
      setLanguage: (lang) => {
        // Validate language code
        if (lang !== 'it' && lang !== 'en') {
          console.warn(`Invalid language code: ${lang}. Falling back to 'it'`)
          return
        }
        set({ language: lang })
      }
    }),
    {
      name: 'language-storage', // Key in localStorage
      getStorage: () => localStorage
    }
  )
)
