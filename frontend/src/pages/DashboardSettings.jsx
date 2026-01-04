import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Settings, 
  QrCode, 
  Download, 
  Copy, 
  Check, 
  Building2,
  Save,
  RefreshCw,
  Loader2,
  Plus,
  Trash2,
  Sparkles,
  ChefHat,
  Wine,
  X,
  Edit3
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { venueService, menuService, productService } from '../services/api'
import toast from 'react-hot-toast'

const categoryLabels = {
  'antipasto': 'Antipasti',
  'primo': 'Primi Piatti',
  'secondo': 'Secondi Piatti',
  'contorno': 'Contorni',
  'dolce': 'Dolci',
  'altro': 'Altro'
}

function DashboardSettings() {
  console.log('[DashboardSettings] Component rendering...')
  
  const { venue, updateVenue } = useAuth()
  
  console.log('[DashboardSettings] Venue from context:', venue)
  console.log('[DashboardSettings] Venue ID:', venue?.id)
  console.log('[DashboardSettings] Venue name:', venue?.name)
  
  const [copied, setCopied] = useState(false)
  const [saving, setSaving] = useState(false)
  const [loadingQR, setLoadingQR] = useState(false)
  const [qrCodeImage, setQrCodeImage] = useState(null)
  const [formData, setFormData] = useState({
    name: venue?.name || '',
    description: venue?.description || ''
  })
  
  // Menu management state
  const [menuItems, setMenuItems] = useState([])
  const [loadingMenu, setLoadingMenu] = useState(false)
  const [showMenuUpload, setShowMenuUpload] = useState(false)
  const [menuText, setMenuText] = useState('')
  const [parsingMenu, setParsingMenu] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  
  // Manual dish entry state (same as onboarding)
  const [newDishName, setNewDishName] = useState('')
  const [newDishCategory, setNewDishCategory] = useState('primo')
  const [newDishMainIngredient, setNewDishMainIngredient] = useState('')
  const [newDishCookingMethod, setNewDishCookingMethod] = useState('')
  
  // Featured wines state
  const [products, setProducts] = useState([])
  const [loadingProducts, setLoadingProducts] = useState(false)
  const [selectedFeaturedWines, setSelectedFeaturedWines] = useState([])

  // Customer URL with real slug
  const customerUrl = venue?.slug 
    ? `${window.location.origin}/v/${venue.slug}`
    : null

  // Sync formData when venue changes
  useEffect(() => {
    if (venue) {
      setFormData({
        name: venue.name || '',
        description: venue.description || ''
      })
    }
  }, [venue])

  // Fetch data on mount
  useEffect(() => {
    if (venue?.id) {
      fetchQRCode()
      fetchMenu()
      fetchProducts()
    }
  }, [venue?.id])
  
  // Load featured wines from venue
  useEffect(() => {
    if (venue?.featured_wines) {
      setSelectedFeaturedWines(venue.featured_wines)
    }
  }, [venue?.featured_wines])

  const fetchQRCode = async () => {
    if (!venue?.id) return
    
    setLoadingQR(true)
    try {
      const response = await venueService.getQRCode(venue.id)
      setQrCodeImage(response.data.qr_code_url)
    } catch (error) {
      console.error('Error fetching QR code:', error)
    } finally {
      setLoadingQR(false)
    }
  }
  
  const fetchMenu = async () => {
    if (!venue?.id) {
      console.log('[DashboardSettings] fetchMenu: No venue ID')
      return
    }
    
    console.log('[DashboardSettings] fetchMenu: Fetching menu for venue', venue.id)
    setLoadingMenu(true)
    try {
      const response = await menuService.getMenu(venue.id)
      console.log('[DashboardSettings] fetchMenu: Full response', response)
      console.log('[DashboardSettings] fetchMenu: Response data', response.data)
      
      // API returns { items: [], grouped: {}, categories: [] }
      if (!response || !response.data) {
        console.warn('[DashboardSettings] fetchMenu: Invalid response structure')
        setMenuItems([])
        return
      }
      
      const items = Array.isArray(response.data.items) ? response.data.items : []
      console.log('[DashboardSettings] fetchMenu: Setting menu items', items.length, items)
      setMenuItems(items)
      
      if (items.length === 0) {
        console.log('[DashboardSettings] fetchMenu: No menu items found (this is OK if menu is empty)')
      }
    } catch (error) {
      console.error('[DashboardSettings] Error fetching menu:', error)
      console.error('[DashboardSettings] Error response:', error.response)
      console.error('[DashboardSettings] Error status:', error.response?.status)
      console.error('[DashboardSettings] Error data:', error.response?.data)
      console.error('[DashboardSettings] Error message:', error.message)
      
      // Show user-friendly error
      if (error.response?.status === 404) {
        console.warn('[DashboardSettings] Menu endpoint not found - venue might not exist')
      } else if (error.response?.status === 403) {
        console.warn('[DashboardSettings] Access forbidden')
      } else {
        console.error('[DashboardSettings] Unexpected error fetching menu')
      }
      
      setMenuItems([]) // Ensure it's always an array
    } finally {
      setLoadingMenu(false)
    }
  }

  const handleRegenerateQR = async () => {
    if (!venue?.id) return
    
    setLoadingQR(true)
    try {
      const response = await venueService.regenerateQRCode(venue.id)
      setQrCodeImage(response.data.qr_code_url)
      toast.success('QR Code rigenerato!')
    } catch (error) {
      toast.error('Errore durante la rigenerazione del QR code')
    } finally {
      setLoadingQR(false)
    }
  }

  const handleCopyLink = () => {
    if (!customerUrl) {
      toast.error('Link non disponibile')
      return
    }
    navigator.clipboard.writeText(customerUrl)
    setCopied(true)
    toast.success('Link copiato!')
    setTimeout(() => setCopied(false), 2000)
  }

  const fetchProducts = async () => {
    if (!venue?.id) return
    
    setLoadingProducts(true)
    try {
      const response = await productService.getProducts(venue.id)
      const productsData = Array.isArray(response.data) ? response.data : (response.data?.products || [])
      setProducts(productsData.filter(p => p.is_available !== false))
    } catch (error) {
      console.error('Error fetching products:', error)
      setProducts([])
    } finally {
      setLoadingProducts(false)
    }
  }
  
  const handleToggleFeaturedWine = (wineId) => {
    setSelectedFeaturedWines(prev => {
      if (prev.includes(wineId)) {
        // Remove wine
        return prev.filter(id => id !== wineId)
      } else {
        // Add wine (max 2)
        if (prev.length >= 2) {
          toast.error('Puoi selezionare massimo 2 vini in evidenza')
          return prev
        }
        return [...prev, wineId]
      }
    })
  }
  
  const handleSave = async () => {
    if (!venue?.id) {
      toast.error('Errore: venue non trovato')
      return
    }
    
    setSaving(true)
    try {
      const updateData = {
        ...formData,
        featured_wines: selectedFeaturedWines
      }
      const response = await venueService.updateVenue(venue.id, updateData)
      updateVenue(response.data.venue)
      toast.success('Impostazioni salvate!')
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Errore durante il salvataggio'
      toast.error(errorMsg)
    } finally {
      setSaving(false)
    }
  }

  const handleDownloadQR = () => {
    if (!qrCodeImage) {
      toast.error('QR Code non disponibile')
      return
    }
    
    const link = document.createElement('a')
    if (qrCodeImage.startsWith('data:')) {
      link.href = qrCodeImage
    } else {
      const apiBase = import.meta.env.VITE_API_URL || ''
      link.href = apiBase.replace('/api', '') + qrCodeImage
    }
    link.download = `qr-code-${venue?.slug || 'venue'}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    toast.success('QR Code scaricato!')
  }
  
  // Menu management handlers
  const handleParseMenu = async () => {
    if (!menuText.trim()) {
      toast.error('Inserisci il testo del menù')
      return
    }
    
    setParsingMenu(true)
    try {
      const response = await menuService.parseMenu(venue.id, menuText)
      const newItems = response.data.items || []
      
      if (newItems.length > 0) {
        await menuService.bulkAdd(venue.id, newItems)
        await fetchMenu()
        toast.success(`${newItems.length} piatti importati!`)
      }
      
      setMenuText('')
      setShowMenuUpload(false)
    } catch (error) {
      toast.error('Errore durante il parsing del menù')
    } finally {
      setParsingMenu(false)
    }
  }
  
  const handleDeleteMenuItem = async (itemId) => {
    try {
      await menuService.deleteItem(venue.id, itemId)
      setMenuItems(menuItems.filter(i => i.id !== itemId))
      toast.success('Piatto eliminato')
    } catch (error) {
      toast.error('Errore durante l\'eliminazione')
    }
  }
  
  const handleClearMenu = async () => {
    if (!confirm('Sei sicuro di voler eliminare tutti i piatti?')) return
    
    try {
      await menuService.clearMenu(venue.id)
      setMenuItems([])
      toast.success('Menù cancellato')
    } catch (error) {
      toast.error('Errore durante l\'eliminazione')
    }
  }
  
  // Manual dish entry handlers (same as onboarding)
  const handleAddDish = async () => {
    if (!newDishName.trim()) {
      toast.error('Inserisci il nome del piatto')
      return
    }
    
    if (!venue?.id) {
      toast.error('Errore: venue non trovato')
      return
    }
    
    const newItem = {
      name: newDishName.trim(),
      category: newDishCategory,
      main_ingredient: newDishMainIngredient.trim() || null,
      cooking_method: newDishCookingMethod.trim() || null
    }
    
    try {
      await menuService.bulkAdd(venue.id, [newItem])
      await fetchMenu() // Refresh menu list
      setNewDishName('')
      setNewDishMainIngredient('')
      setNewDishCookingMethod('')
      toast.success('Piatto aggiunto!')
    } catch (error) {
      toast.error('Errore durante l\'aggiunta del piatto')
    }
  }
  
  const handleUpdateItem = (id, field, value) => {
    setMenuItems(menuItems.map(item => 
      item.id === id ? { ...item, [field]: value } : item
    ))
  }
  
  const handleSaveMenuItem = async (item) => {
    if (!venue?.id) return
    
    try {
      await menuService.updateItem(venue.id, item.id, {
        name: item.name,
        category: item.category,
        main_ingredient: item.main_ingredient,
        cooking_method: item.cooking_method
      })
      await fetchMenu()
      setEditingItem(null)
      toast.success('Piatto aggiornato!')
    } catch (error) {
      toast.error('Errore durante l\'aggiornamento')
    }
  }

  // Group menu items by category
  const groupedItems = menuItems.reduce((acc, item) => {
    const cat = item.category || 'altro'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(item)
    return acc
  }, {})

  // Early return if venue is not loaded yet
  if (!venue) {
    console.log('[DashboardSettings] Venue is null/undefined, showing loader')
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-burgundy-400 animate-spin mx-auto mb-4" />
          <p className="text-burgundy-600">Caricamento impostazioni...</p>
          <p className="text-burgundy-400 text-sm mt-2">
            Se il caricamento non termina, prova a effettuare nuovamente il login.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="font-display text-3xl font-bold text-burgundy-900 flex items-center gap-3">
          <Settings className="w-8 h-8 text-gold-500" />
          Impostazioni
        </h1>
        <p className="text-burgundy-600 mt-1">
          Configura il tuo locale e il sommelier AI
        </p>
      </div>

      {/* QR Code Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card"
      >
        <div className="flex items-start gap-3 mb-6">
          <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
            <QrCode className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h2 className="font-display text-lg font-semibold text-burgundy-900">
              QR Code
            </h2>
            <p className="text-sm text-burgundy-600">
              Stampa e posiziona sui tavoli per far accedere i clienti al sommelier
            </p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-6">
          <div className="w-48 h-48 bg-white border-2 border-burgundy-200 rounded-2xl flex items-center justify-center flex-shrink-0 overflow-hidden">
            {loadingQR ? (
              <Loader2 className="w-8 h-8 text-burgundy-400 animate-spin" />
            ) : qrCodeImage ? (
              <img 
                src={qrCodeImage.startsWith('data:') || qrCodeImage.startsWith('http') 
                  ? qrCodeImage 
                  : `${(import.meta.env.VITE_API_URL || '').replace('/api', '')}${qrCodeImage}`
                }
                alt="QR Code"
                className="w-full h-full object-contain p-2"
              />
            ) : (
              <div className="text-center">
                <QrCode className="w-20 h-20 text-burgundy-300 mx-auto mb-2" />
                <p className="text-xs text-burgundy-400">QR non generato</p>
              </div>
            )}
          </div>

          <div className="flex-1 space-y-4">
            <div>
              <label className="block text-sm font-medium text-burgundy-700 mb-2">
                Link per i clienti
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customerUrl || 'Slug non disponibile'}
                  readOnly
                  className="input-field flex-1 bg-cream-50"
                />
                <button
                  onClick={handleCopyLink}
                  className="btn-outline px-4"
                  disabled={!customerUrl}
                >
                  {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <button 
                onClick={handleDownloadQR} 
                className="btn-primary flex items-center gap-2"
                disabled={!qrCodeImage || loadingQR}
              >
                <Download className="w-4 h-4" />
                Scarica QR Code
              </button>
              <button 
                onClick={handleRegenerateQR}
                className="btn-outline flex items-center gap-2"
                disabled={loadingQR}
              >
                <RefreshCw className={`w-4 h-4 ${loadingQR ? 'animate-spin' : ''}`} />
                Rigenera
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Menu Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card"
      >
        <div className="flex items-start justify-between gap-3 mb-6">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-gold-100 rounded-xl flex items-center justify-center">
              <ChefHat className="w-5 h-5 text-gold-600" />
            </div>
            <div>
              <h2 className="font-display text-lg font-semibold text-burgundy-900">
                Menù Piatti
              </h2>
              <p className="text-sm text-burgundy-600">
                {menuItems.length} piatti in menù
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowMenuUpload(!showMenuUpload)}
              className="btn-outline flex items-center gap-2 text-sm"
            >
              <Plus className="w-4 h-4" />
              Aggiungi piatti
            </button>
            {menuItems.length > 0 && (
              <button
                onClick={handleClearMenu}
                className="btn-outline text-red-600 border-red-200 hover:bg-red-50 text-sm"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Menu Add Form - Same as onboarding */}
        {showMenuUpload && (
          <div className="mb-6 space-y-4">
            {/* Manual Entry Form */}
            <div className="bg-white rounded-xl border border-burgundy-200 p-6">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-gold-100 rounded-xl flex items-center justify-center">
                  <ChefHat className="w-6 h-6 text-gold-600" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-burgundy-900 mb-1">
                    Aggiungi i tuoi piatti
                  </h3>
                  <p className="text-sm text-burgundy-600">
                    Inserisci i piatti del menù uno alla volta. Serviranno per suggerire abbinamenti perfetti.
                  </p>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newDishName}
                    onChange={(e) => setNewDishName(e.target.value)}
                    placeholder="Nome del piatto *"
                    className="flex-1 px-4 py-2 border border-burgundy-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gold-400"
                    required
                  />
                  <select
                    value={newDishCategory}
                    onChange={(e) => setNewDishCategory(e.target.value)}
                    className="px-3 py-2 border border-burgundy-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gold-400"
                  >
                    {Object.entries(categoryLabels).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    value={newDishMainIngredient}
                    onChange={(e) => setNewDishMainIngredient(e.target.value)}
                    placeholder="Ingrediente principale (es. Manzo, Pesce, Pasta)"
                    className="px-4 py-2 border border-burgundy-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gold-400"
                  />
                  <input
                    type="text"
                    value={newDishCookingMethod}
                    onChange={(e) => setNewDishCookingMethod(e.target.value)}
                    placeholder="Metodo di cottura (es. Griglia, Al forno, Crudo)"
                    className="px-4 py-2 border border-burgundy-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gold-400"
                  />
                </div>
                <button
                  onClick={handleAddDish}
                  disabled={!newDishName.trim()}
                  className="w-full px-4 py-2 bg-gold-500 text-white rounded-lg hover:bg-gold-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Plus className="w-5 h-5" />
                  Aggiungi Piatto
                </button>
              </div>
            </div>

            {/* AI Parsing Option */}
            <div className="bg-gold-50 rounded-xl border border-gold-200 p-4">
              <h3 className="font-semibold text-burgundy-900 mb-3">Oppure carica menù con AI</h3>
              <textarea
                value={menuText}
                onChange={(e) => setMenuText(e.target.value)}
                placeholder={`Incolla qui il tuo menù...

Esempio:
ANTIPASTI
Bruschetta al pomodoro - €8
Carpaccio di manzo - €14

PRIMI PIATTI
Spaghetti alle vongole - €16
Risotto ai funghi - €18`}
                className="w-full h-40 p-3 border border-gold-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-gold-400 text-sm"
              />
              <div className="flex gap-2 mt-3">
                <button
                  onClick={handleParseMenu}
                  disabled={!menuText.trim() || parsingMenu}
                  className="btn-primary flex items-center gap-2"
                >
                  {parsingMenu ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                  {parsingMenu ? 'Elaborazione...' : 'Estrai con AI'}
                </button>
                <button
                  onClick={() => { setShowMenuUpload(false); setMenuText('') }}
                  className="btn-outline"
                >
                  Annulla
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Menu List */}
        {loadingMenu ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 text-gold-400 animate-spin" />
          </div>
        ) : menuItems.length === 0 ? (
          <div className="text-center py-8 text-burgundy-500">
            <ChefHat className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>Nessun piatto in menù</p>
            <p className="text-sm">Clicca "Aggiungi piatti" per iniziare</p>
          </div>
        ) : (
          <div className="space-y-4 max-h-[40vh] overflow-y-auto pr-2">
            {Object.entries(categoryLabels).map(([catKey, catLabel]) => {
              const catItems = groupedItems[catKey]
              if (!catItems || catItems.length === 0) return null
              
              return (
                <div key={catKey}>
                  <h3 className="font-medium text-burgundy-800 mb-2 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-gold-500"></span>
                    {catLabel} ({catItems.length})
                  </h3>
                  <div className="space-y-1">
                    {catItems.map(item => (
                      <div 
                        key={item.id}
                        className="bg-white rounded-lg border border-burgundy-100 p-2"
                      >
                        {editingItem === item.id ? (
                          <div className="space-y-2">
                            <div className="flex gap-2">
                              <input
                                type="text"
                                value={item.name}
                                onChange={(e) => handleUpdateItem(item.id, 'name', e.target.value)}
                                className="flex-1 px-2 py-1 border border-burgundy-200 rounded text-sm"
                                placeholder="Nome piatto"
                                autoFocus
                              />
                              <select
                                value={item.category}
                                onChange={(e) => handleUpdateItem(item.id, 'category', e.target.value)}
                                className="px-2 py-1 border border-burgundy-200 rounded text-sm"
                              >
                                {Object.entries(categoryLabels).map(([k, v]) => (
                                  <option key={k} value={k}>{v}</option>
                                ))}
                              </select>
                              <button
                                onClick={() => handleSaveMenuItem(item)}
                                className="p-1 text-green-600 hover:bg-green-50 rounded"
                              >
                                <Save className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => setEditingItem(null)}
                                className="p-1 text-burgundy-400 hover:bg-burgundy-50 rounded"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                              <input
                                type="text"
                                value={item.main_ingredient || ''}
                                onChange={(e) => handleUpdateItem(item.id, 'main_ingredient', e.target.value)}
                                className="px-2 py-1 border border-burgundy-200 rounded text-sm"
                                placeholder="Ingrediente principale"
                              />
                              <input
                                type="text"
                                value={item.cooking_method || ''}
                                onChange={(e) => handleUpdateItem(item.id, 'cooking_method', e.target.value)}
                                className="px-2 py-1 border border-burgundy-200 rounded text-sm"
                                placeholder="Metodo di cottura"
                              />
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <div className="flex-1">
                              <span className="text-burgundy-900 text-sm font-medium block">{item.name}</span>
                              {(item.main_ingredient || item.cooking_method) && (
                                <div className="flex gap-2 mt-1">
                                  {item.main_ingredient && (
                                    <span className="text-xs text-burgundy-500">Ingrediente: {item.main_ingredient}</span>
                                  )}
                                  {item.cooking_method && (
                                    <span className="text-xs text-burgundy-500">Cottura: {item.cooking_method}</span>
                                  )}
                                </div>
                              )}
                            </div>
                            {item.price && (
                              <span className="text-gold-600 font-medium text-sm">€{item.price}</span>
                            )}
                            <button
                              onClick={() => setEditingItem(item.id)}
                              className="p-1 text-burgundy-400 hover:text-burgundy-600 rounded"
                            >
                              <Edit3 className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => handleDeleteMenuItem(item.id)}
                              className="p-1 text-red-400 hover:text-red-600 rounded"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </motion.div>

      {/* Venue Info Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="card"
      >
        <div className="flex items-start gap-3 mb-6">
          <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
            <Building2 className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h2 className="font-display text-lg font-semibold text-burgundy-900">
              Informazioni Locale
            </h2>
            <p className="text-sm text-burgundy-600">
              Dati del tuo ristorante
            </p>
          </div>
        </div>

        <div className="grid gap-4">
          <div>
            <label className="block text-sm font-medium text-burgundy-700 mb-2">
              Nome del Ristorante
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-burgundy-700 mb-2">
              Descrizione
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="input-field"
              rows={3}
            />
          </div>
        </div>
      </motion.div>

      {/* Featured Wines Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.18 }}
        className="card"
      >
        <div className="flex items-start gap-3 mb-6">
          <div className="w-10 h-10 bg-gold-100 rounded-xl flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-gold-600" />
          </div>
          <div className="flex-1">
            <h2 className="font-display text-lg font-semibold text-burgundy-900">
              Vini in Evidenza
            </h2>
            <p className="text-sm text-burgundy-600">
              Seleziona massimo 2 vini dalla tua carta che il sommelier proporrà prioritariamente quando appropriati
            </p>
            <p className="text-xs text-burgundy-500 mt-1">
              {selectedFeaturedWines.length}/2 selezionati
            </p>
          </div>
        </div>

        {loadingProducts ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 text-burgundy-400 animate-spin" />
            <span className="ml-2 text-burgundy-600">Caricamento vini...</span>
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-8 bg-cream-50 rounded-xl">
            <Wine className="w-12 h-12 text-burgundy-300 mx-auto mb-3" />
            <p className="text-burgundy-600 mb-2">Nessun vino disponibile</p>
            <p className="text-sm text-burgundy-500">
              Aggiungi vini alla carta nella sezione "Prodotti"
            </p>
          </div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
            {products.map((wine) => {
              const isSelected = selectedFeaturedWines.includes(wine.id)
              const isDisabled = !isSelected && selectedFeaturedWines.length >= 2
              
              return (
                <label
                  key={wine.id}
                  className={`flex items-center gap-4 p-4 rounded-xl border-2 cursor-pointer transition-all ${
                    isSelected
                      ? 'border-gold-500 bg-gold-50'
                      : isDisabled
                      ? 'border-burgundy-100 bg-cream-50 opacity-50 cursor-not-allowed'
                      : 'border-burgundy-100 bg-white hover:border-gold-300 hover:bg-gold-50/30'
                  }`}
                >
                  <div className="flex items-center gap-3 flex-1">
                    <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 ${
                      isSelected
                        ? 'border-gold-600 bg-gold-600'
                        : 'border-burgundy-300'
                    }`}>
                      {isSelected && <Check className="w-3 h-3 text-white" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-burgundy-900">
                          {wine.name}
                        </h3>
                        {wine.type && (
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            wine.type === 'red' ? 'bg-red-100 text-red-700' :
                            wine.type === 'white' ? 'bg-amber-100 text-amber-700' :
                            wine.type === 'rose' ? 'bg-pink-100 text-pink-700' :
                            wine.type === 'sparkling' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {wine.type === 'red' ? 'Rosso' :
                             wine.type === 'white' ? 'Bianco' :
                             wine.type === 'rose' ? 'Rosato' :
                             wine.type === 'sparkling' ? 'Bollicine' : wine.type}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-sm text-burgundy-600">
                        {wine.region && <span>{wine.region}</span>}
                        {wine.price && (
                          <span className="font-semibold text-burgundy-900">
                            €{parseFloat(wine.price).toFixed(2)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => handleToggleFeaturedWine(wine.id)}
                    disabled={isDisabled}
                    className="sr-only"
                  />
                </label>
              )
            })}
          </div>
        )}

        {selectedFeaturedWines.length > 0 && (
          <div className="mt-4 p-3 bg-gold-50 rounded-xl border border-gold-200">
            <p className="text-sm font-medium text-burgundy-900 mb-2">
              Vini selezionati:
            </p>
            <div className="flex flex-wrap gap-2">
              {selectedFeaturedWines.map(wineId => {
                const wine = products.find(p => p.id === wineId)
                return wine ? (
                  <span
                    key={wineId}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-gold-500 text-burgundy-900 rounded-full text-sm font-medium"
                  >
                    {wine.name}
                    <button
                      onClick={() => handleToggleFeaturedWine(wineId)}
                      className="ml-1 hover:bg-burgundy-900/20 rounded-full p-0.5"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ) : null
              })}
            </div>
          </div>
        )}
      </motion.div>

      {/* Save Button */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="flex justify-end"
      >
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn-primary flex items-center gap-2"
        >
          <Save className="w-5 h-5" />
          {saving ? 'Salvataggio...' : 'Salva Modifiche'}
        </button>
      </motion.div>
    </div>
  )
}

export default DashboardSettings
