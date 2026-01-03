import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

// Create axios instance with defaults
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // If data is FormData, remove Content-Type to let browser set it with boundary
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('venue')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Export api instance for direct use
export { api }

// Auth Service
export const authService = {
  login: (email, password) => 
    api.post('/auth/login', { email, password }),
  
  register: (data) => 
    api.post('/auth/register', data),
  
  refreshToken: () => 
    api.post('/auth/refresh'),
  
  getProfile: () => 
    api.get('/auth/profile')
}

// Venues Service
export const venueService = {
  getVenue: (slug) => 
    api.get(`/venues/${slug}`),
  
  updateVenue: (id, data) => 
    api.put(`/venues/${id}`, data),
  
  getQRCode: (id) => 
    api.get(`/venues/${id}/qrcode`),
  
  regenerateQRCode: (id) => 
    api.post(`/venues/${id}/qrcode/regenerate`)
}

// Products Service (Wine List)
export const productService = {
  getProducts: (venueId, params = {}) => 
    api.get(`/products/venue/${venueId}`, { params }),
  
  getProduct: (id) => 
    api.get(`/products/${id}`),
  
  createProduct: (data) => 
    api.post('/products', data),
  
  updateProduct: (id, data) => 
    api.put(`/products/${id}`, data),
  
  deleteProduct: (id) => 
    api.delete(`/products/${id}`),
  
  bulkImport: (venueId, products) => 
    api.post(`/products/venue/${venueId}/bulk`, { products }),
  
  syncVectorDB: (venueId) => 
    api.post(`/products/venue/${venueId}/sync-vectors`),
  
  // Wine list AI parsing from text
  parseWineList: (venueId, wineText) =>
    api.post(`/products/venue/${venueId}/parse`, { wine_text: wineText }),
  
  // Wine list AI parsing from images (base64)
  parseWineImages: (venueId, base64Images) =>
    api.post(`/products/venue/${venueId}/parse-images`, { images: base64Images }, { timeout: 120000 }),
  
  // Parse CSV wine list
  parseWineCsv: (venueId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/products/venue/${venueId}/parse-csv`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // Generate wine descriptions using AI
  generateWineDescriptions: (venueId, wines) =>
    api.post(`/products/venue/${venueId}/generate-descriptions`, { wines }),
  
  // Upload label image for a product
  uploadLabelImage: (productId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/products/${productId}/label-image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // Clear all products
  clearProducts: (venueId) =>
    api.delete(`/products/venue/${venueId}/clear`)
}

// Chat Service
export const chatService = {
  // B2C Customer chat
  createSession: (venueSlug) => 
    api.post('/chat/sessions', { venue_slug: venueSlug }),
  
  sendMessage: (sessionToken, message, context = null) => 
    api.post('/chat/messages', { 
      session_token: sessionToken, 
      message,
      context // { dishes, guest_count, budget, wine_count }
    }),
  
  confirmWines: (sessionToken, wineIds) =>
    api.post('/chat/confirm-wines', {
      session_token: sessionToken,
      wine_ids: wineIds
    }),
  
  submitFeedback: (sessionToken, rating, feedback) =>
    api.post('/chat/feedback', {
      session_token: sessionToken,
      rating: rating,
      feedback: feedback || ''
    }),
  
  getSessionHistory: (sessionToken) => 
    api.get(`/chat/sessions/${sessionToken}/history`),
  
  getMessageRankings: (messageId) =>
    api.get(`/chat/messages/${messageId}/rankings`)
}

// Analytics Service
export const analyticsService = {
  // FREE tier endpoints
  getOverview: (params = {}) => 
    api.get('/analytics/overview', { params }),
  
  getOperational: (params = {}) => 
    api.get('/analytics/operational', { params }),
  
  // PREMIUM tier endpoints
  getCustomerIntelligence: (params = {}) => 
    api.get('/analytics/customer-intelligence', { params }),
  
  getWinePerformance: (params = {}) => 
    api.get('/analytics/wine-performance', { params }),
  
  getRevenue: (params = {}) => 
    api.get('/analytics/revenue', { params }),
  
  getBenchmark: (params = {}) => 
    api.get('/analytics/benchmark', { params })
}

// Menu Service (Food menu for wine pairing)
export const menuService = {
  getMenu: (venueId, params = {}) =>
    api.get(`/menu/venue/${venueId}`, { params }),
  
  addItem: (venueId, item) =>
    api.post(`/menu/venue/${venueId}/items`, item),
  
  updateItem: (venueId, itemId, data) =>
    api.put(`/menu/venue/${venueId}/items/${itemId}`, data),
  
  deleteItem: (venueId, itemId) =>
    api.delete(`/menu/venue/${venueId}/items/${itemId}`),
  
  parseMenu: (venueId, menuText) =>
    api.post(`/menu/venue/${venueId}/parse`, { menu_text: menuText }),
  
  bulkAdd: (venueId, items) =>
    api.post(`/menu/venue/${venueId}/bulk`, { items }),
  
  clearMenu: (venueId) =>
    api.delete(`/menu/venue/${venueId}/clear`)
}

export default api

