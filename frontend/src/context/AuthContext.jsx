import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [venue, setVenue] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    // Check for existing session on mount
    const token = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')
    const storedVenue = localStorage.getItem('venue')
    
    console.log('[AuthContext] Checking existing session...')
    console.log('[AuthContext] Token exists:', !!token)
    console.log('[AuthContext] Stored user exists:', !!storedUser)
    console.log('[AuthContext] Stored venue exists:', !!storedVenue)
    
    if (token && storedUser) {
      const parsedUser = JSON.parse(storedUser)
      setUser(parsedUser)
      console.log('[AuthContext] User loaded from localStorage:', parsedUser)
      
      if (storedVenue) {
        const parsedVenue = JSON.parse(storedVenue)
        setVenue(parsedVenue)
        console.log('[AuthContext] Venue loaded from localStorage:', parsedVenue)
        console.log('[AuthContext] Venue is_onboarded:', parsedVenue?.is_onboarded)
      } else {
        console.warn('[AuthContext] No venue in localStorage!')
      }
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    try {
      console.log('[AuthContext] Login attempt for:', email)
      const response = await authService.login(email, password)
      const { access_token, user: userData, venue: venueData } = response.data
      
      console.log('[AuthContext] Login response received')
      console.log('[AuthContext] User data:', userData)
      console.log('[AuthContext] Venue data:', venueData)
      console.log('[AuthContext] is_onboarded:', venueData?.is_onboarded)
      
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))
      if (venueData) {
        localStorage.setItem('venue', JSON.stringify(venueData))
        setVenue(venueData)
        console.log('[AuthContext] Venue saved to localStorage and state')
      } else {
        console.warn('[AuthContext] No venue data received from login!')
      }
      
      setUser(userData)
      
      // Redirect based on onboarding status
      if (venueData?.is_onboarded) {
        console.log('[AuthContext] Venue is onboarded, navigating to dashboard')
        navigate('/dashboard')
      } else {
        console.log('[AuthContext] Venue NOT onboarded, navigating to onboarding')
        navigate('/onboarding')
      }
      
      return { success: true }
    } catch (error) {
      console.error('[AuthContext] Login error:', error)
      return { 
        success: false, 
        error: error.response?.data?.message || 'Errore durante il login' 
      }
    }
  }

  const register = async (data) => {
    try {
      console.log('[AuthContext] Register attempt with data:', { ...data, password: '***' })
      const response = await authService.register(data)
      const { access_token, user: userData, venue: venueData } = response.data
      
      console.log('[AuthContext] Register response received')
      console.log('[AuthContext] User data:', userData)
      console.log('[AuthContext] Venue data:', venueData)
      console.log('[AuthContext] Venue ID:', venueData?.id)
      console.log('[AuthContext] Venue is_onboarded:', venueData?.is_onboarded)
      
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))
      if (venueData) {
        localStorage.setItem('venue', JSON.stringify(venueData))
        setVenue(venueData)
        console.log('[AuthContext] Venue saved to localStorage and state')
      } else {
        console.error('[AuthContext] NO VENUE DATA from registration!')
      }
      
      setUser(userData)
      console.log('[AuthContext] Navigating to onboarding...')
      navigate('/onboarding')
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.message || 'Errore durante la registrazione' 
      }
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('venue')
    setUser(null)
    setVenue(null)
    navigate('/login')
  }

  const updateVenue = (venueData) => {
    console.log('[AuthContext] updateVenue called with:', venueData)
    console.log('[AuthContext] is_onboarded value:', venueData?.is_onboarded)
    localStorage.setItem('venue', JSON.stringify(venueData))
    setVenue(venueData)
    console.log('[AuthContext] Venue updated in localStorage and state')
  }

  const value = {
    user,
    venue,
    loading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    updateVenue
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

