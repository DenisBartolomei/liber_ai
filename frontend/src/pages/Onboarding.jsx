import { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ChefHat, 
  Users, 
  ArrowRight, 
  ArrowLeft,
  Check,
  Upload,
  Trash2,
  Edit3,
  Plus,
  Save,
  Wine
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { venueService, menuService, productService } from '../services/api'
import toast from 'react-hot-toast'
import Logo from '../components/ui/Logo'
import CsvWineUpload from '../components/onboarding/CsvWineUpload'

const steps = [
  {
    id: 'menu',
    title: 'Menù del Ristorante',
    description: 'Inserisci i piatti del tuo menù',
    icon: ChefHat
  },
  {
    id: 'wines',
    title: 'Carta dei Vini',
    description: 'Carica un file CSV con la lista dei vini',
    icon: Wine
  },
  {
    id: 'target',
    title: 'Clientela',
    description: 'Qual è il target principale del tuo locale?',
    icon: Users
  },
  {
    id: 'style',
    title: 'Stile del Sommelier',
    description: 'Come vuoi che il sommelier AI si presenti?',
    icon: null // Will use Logo component instead
  }
]

const targetOptions = [
  { value: 'business', label: 'Business/Professionisti', icon: '💼' },
  { value: 'couples', label: 'Coppie Romantiche', icon: '💑' },
  { value: 'families', label: 'Famiglie', icon: '👨‍👩‍👧‍👦' },
  { value: 'tourists', label: 'Turisti', icon: '🌎' },
  { value: 'young', label: 'Giovani/Trendy', icon: '🎉' },
  { value: 'connoisseurs', label: 'Intenditori', icon: '🍷' }
]

const styleOptions = [
  { value: 'professional', label: 'Professionale ed Elegante', description: 'Consigli formali e dettagliati' },
  { value: 'friendly', label: 'Amichevole e Informale', description: 'Tono colloquiale e accessibile' },
  { value: 'expert', label: 'Esperto e Tecnico', description: 'Per intenditori e appassionati' },
  { value: 'playful', label: 'Divertente e Creativo', description: 'Leggero con tocco di originalità' }
]

const categoryLabels = {
  'antipasto': 'Antipasti',
  'primo': 'Primi Piatti',
  'secondo': 'Secondi Piatti',
  'contorno': 'Contorni',
  'dolce': 'Dolci',
  'altro': 'Altro'
}

const wineTypeLabels = {
  'red': 'Vini Rossi',
  'white': 'Vini Bianchi',
  'rose': 'Vini Rosati',
  'sparkling': 'Spumanti e Champagne',
  'dessert': 'Vini Dolci',
  'fortified': 'Vini Fortificati'
}

function Onboarding() {
  const [currentStep, setCurrentStep] = useState(0)
  const [formData, setFormData] = useState({
    target_audience: [],
    sommelier_style: ''
  })
  
  // Menu state - simplified to just manual entry
  const [parsedItems, setParsedItems] = useState([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  const [newDishName, setNewDishName] = useState('')
  const [newDishCategory, setNewDishCategory] = useState('primo')
  const [newDishMainIngredient, setNewDishMainIngredient] = useState('')
  const [newDishCookingMethod, setNewDishCookingMethod] = useState('')
  
  // Wine state - CSV upload only
  const [parsedWines, setParsedWines] = useState([])
  const [editingWine, setEditingWine] = useState(null)
  
  const { venue, updateVenue } = useAuth()
  const navigate = useNavigate()
  
  console.log('[Onboarding] Component rendering...')
  console.log('[Onboarding] Venue from context:', venue)
  console.log('[Onboarding] Venue ID:', venue?.id)
  console.log('[Onboarding] Venue is_onboarded:', venue?.is_onboarded)

  // Add dish manually
  const handleAddDish = () => {
    if (!newDishName.trim()) {
      toast.error('Inserisci il nome del piatto')
      return
    }
    
    const newItem = {
      id: `menu-${Date.now()}`,
      name: newDishName.trim(),
      category: newDishCategory,
      main_ingredient: newDishMainIngredient.trim() || null,
      cooking_method: newDishCookingMethod.trim() || null
    }
    setParsedItems([...parsedItems, newItem])
    setNewDishName('')
    setNewDishMainIngredient('')
    setNewDishCookingMethod('')
    toast.success('Piatto aggiunto!')
  }
  

  const handleAddItem = () => {
    setEditingItem(`new-${Date.now()}`)
  }
  
  const handleAddWine = () => {
    const newWine = {
      id: `wine-${Date.now()}`,
      name: '',
      type: 'red',
      region: '',
      price: null,
      isNew: true
    }
    setParsedWines([...parsedWines, newWine])
    setEditingWine(newWine.id)
  }

  const handleUpdateItem = (id, field, value) => {
    setParsedItems(parsedItems.map(item => 
      item.id === id ? { ...item, [field]: value } : item
    ))
  }
  
  const handleUpdateWine = (id, field, value) => {
    setParsedWines(parsedWines.map(wine => 
      wine.id === id ? { ...wine, [field]: value } : wine
    ))
  }

  const handleDeleteItem = (id) => {
    setParsedItems(parsedItems.filter(item => item.id !== id))
  }
  
  const handleDeleteWine = (id) => {
    setParsedWines(parsedWines.filter(wine => wine.id !== id))
  }

  const handleTargetSelect = (value) => {
    setFormData(prev => ({
      ...prev,
      target_audience: prev.target_audience.includes(value)
        ? prev.target_audience.filter(v => v !== value)
        : [...prev.target_audience, value]
    }))
  }

  const handleStyleSelect = (value) => {
    setFormData(prev => ({ ...prev, sommelier_style: value }))
  }

  const canProceed = () => {
    switch (currentStep) {
      case 0: // Menu
        return parsedItems.length > 0
      case 1: // Wines
        return parsedWines.length > 0
      case 2: // Target
        return formData.target_audience.length > 0
      case 3: // Style
        return formData.sommelier_style !== ''
      default:
        return false
    }
  }

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1)
    } else {
      handleSubmit()
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1)
    }
  }

  const handleSubmit = async () => {
    console.log('[Onboarding] handleSubmit called')
    console.log('[Onboarding] Current venue:', venue)
    console.log('[Onboarding] Venue ID for API calls:', venue?.id)
    
    if (!venue?.id) {
      console.error('[Onboarding] ERROR: No venue ID available!')
      toast.error('Errore: ID locale non disponibile. Effettua nuovamente il login.')
      return
    }
    
    setIsSubmitting(true)
    try {
      // Save menu items
      const validItems = parsedItems.filter(item => item.name?.trim())
      if (validItems.length > 0) {
        console.log('Saving menu items:', validItems.length)
        await menuService.bulkAdd(venue.id, validItems)
        console.log('Menu items saved successfully')
      }
      
      // Save wines with normalized data (only if not already saved from CSV)
      const winesToSave = parsedWines
      const validWines = winesToSave.filter(wine => wine.name?.trim())
      
      // Separate wines already saved from CSV (have 'saved' flag or 'id') from new ones
      const alreadySavedWines = validWines.filter(wine => wine.saved || wine.id)
      const newWines = validWines.filter(wine => !wine.saved && !wine.id)
      
      if (newWines.length > 0) {
        try {
          // Normalize wine data - ensure all required fields are present
          const normalizedWines = newWines.map(wine => ({
            name: wine.name.trim(),
            type: wine.type || 'red',
            region: wine.region || null,
            country: wine.country || 'Italia',
            grape_variety: wine.grape_variety || null,
            vintage: wine.vintage || null,
            producer: wine.producer || null,
            price: wine.price || 0,
            description: wine.description || null,
            tasting_notes: wine.tasting_notes || null,
            food_pairings: wine.food_pairings || null,
            image_url: wine.image_url || null,
            color: wine.color || null,
            aromas: wine.aromas || null,
            body: wine.body || null,
            acidity_level: wine.acidity_level || null,
            tannin_level: wine.tannin_level || null,
            is_available: true
          }))
          
          console.log('Saving new wines (not from CSV):', normalizedWines.length, normalizedWines)
          const importResponse = await productService.bulkImport(venue.id, normalizedWines)
          console.log('Wine import response:', importResponse.data)
          
          // Upload label images if any wines have image_file (both saved and new)
          const winesWithImages = validWines.filter(w => w.image_file)
          if (winesWithImages.length > 0) {
            // Get saved products to match by name and upload images
            const savedProducts = await productService.getProducts(venue.id)
            for (const wineWithImage of winesWithImages) {
              const savedProduct = savedProducts.data.find(p => 
                p.name === wineWithImage.name && p.type === wineWithImage.type
              )
              if (savedProduct && savedProduct.id) {
                try {
                  await productService.uploadLabelImage(savedProduct.id, wineWithImage.image_file)
                  console.log(`Image uploaded for wine ${savedProduct.id}`)
                } catch (e) {
                  console.warn(`Failed to upload image for wine ${savedProduct.id}:`, e)
                }
              }
            }
          }
          
        } catch (wineError) {
          console.error('Error saving wines:', wineError)
          toast.error(`Errore nel salvataggio vini: ${wineError.response?.data?.message || wineError.message}`)
          // Continue with onboarding even if wines fail
        }
      } else if (alreadySavedWines.length > 0) {
        console.log(`${alreadySavedWines.length} wines already saved from CSV, skipping bulk import`)
      }
      
      // Sync to Qdrant (for all wines, both from CSV and manually added)
      if (validWines.length > 0) {
        try {
          await productService.syncVectorDB(venue.id)
          console.log('Wines synced to vector DB')
        } catch (e) {
          console.warn('Vector sync error:', e)
        }
      }

      // Update venue settings - CRITICAL: This must succeed
      console.log('Updating venue with is_onboarded=true:', { ...formData, is_onboarded: true })
      const response = await venueService.updateVenue(venue.id, {
        ...formData,
        is_onboarded: true
      })
      console.log('Venue update response:', response.data)
      
      if (!response.data || !response.data.venue) {
        throw new Error('Risposta dal server non valida')
      }
      
      // Update both localStorage and state with the server response
      console.log('[Onboarding] Calling updateVenue with:', response.data.venue)
      updateVenue(response.data.venue)
      console.log('[Onboarding] updateVenue called successfully')
      toast.success('Configurazione completata!')
      console.log('[Onboarding] Navigating to dashboard...')
      navigate('/dashboard')
    } catch (error) {
      console.error('Onboarding error:', error)
      const errorMessage = error.response?.data?.message || error.message || 'Errore durante il salvataggio'
      toast.error(`Errore durante il salvataggio: ${errorMessage}`)
      // DO NOT proceed if save failed - user must retry
      // This ensures data is actually saved to database
      setIsSubmitting(false)
      // Don't navigate - let user see the error and retry
    }
  }

  // Group items by category
  const groupedItems = parsedItems.reduce((acc, item) => {
    const cat = item.category || 'altro'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(item)
    return acc
  }, {})
  
  // Group wines by type
  const groupedWines = parsedWines.reduce((acc, wine) => {
    const type = wine.type || 'red'
    if (!acc[type]) acc[type] = []
    acc[type].push(wine)
    return acc
  }, {})

  return (
    <div className="min-h-screen bg-cream-50 flex">
      {/* Left sidebar */}
      <div className="hidden lg:flex lg:w-1/3 bg-burgundy-900 text-cream-50 p-8 flex-col">
        <div className="flex items-center gap-2 mb-12">
          <Logo size="md" className="rounded-xl" />
          <span className="font-display text-2xl font-bold">LIBER</span>
        </div>

        <div className="flex-1">
          <h2 className="font-display text-3xl font-bold mb-4">
            Configura il tuo Sommelier AI
          </h2>
          <p className="text-cream-100/80 mb-12">
            Aiutaci a personalizzare l'esperienza per il tuo ristorante e i tuoi clienti.
          </p>

          {/* Progress steps */}
          <div className="space-y-6">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${
                  index < currentStep 
                    ? 'bg-gold-500 text-burgundy-900' 
                    : index === currentStep 
                      ? 'bg-burgundy-700 text-cream-50' 
                      : 'bg-burgundy-800 text-burgundy-500'
                }`}>
                  {index < currentStep ? (
                    <Check className="w-5 h-5" />
                  ) : step.icon ? (
                    <step.icon className="w-5 h-5" />
                  ) : (
                    <Logo size="sm" />
                  )}
                </div>
                <div>
                  <p className={`font-medium ${
                    index <= currentStep ? 'text-cream-50' : 'text-burgundy-500'
                  }`}>
                    {step.title}
                  </p>
                  <p className="text-sm text-cream-100/60">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 p-8 overflow-y-auto">
        <div className="w-full max-w-3xl mx-auto">
          {/* Mobile header */}
          <div className="lg:hidden mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Logo size="md" />
              <span className="font-display text-xl font-bold text-burgundy-900">LIBER</span>
            </div>
            <div className="flex gap-2 mb-4">
              {steps.map((_, index) => (
                <div 
                  key={index}
                  className={`h-1.5 flex-1 rounded-full ${
                    index <= currentStep ? 'bg-burgundy-900' : 'bg-burgundy-200'
                  }`}
                />
              ))}
            </div>
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <h1 className="font-display text-3xl font-bold text-burgundy-900 mb-2">
                {steps[currentStep].title}
              </h1>
              <p className="text-burgundy-600 mb-8">
                {steps[currentStep].description}
              </p>

              {/* Step 1: Menu - Simple Manual Entry */}
              {currentStep === 0 && (
                <div className="space-y-6">
                  {/* Add dish form */}
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

                  {/* List of added dishes */}
                  {parsedItems.length > 0 && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <p className="text-burgundy-600">
                          <span className="font-bold text-burgundy-900">{parsedItems.length}</span> piatti inseriti
                        </p>
                        <button
                          onClick={() => setParsedItems([])}
                          className="flex items-center gap-1 px-3 py-1.5 text-sm bg-red-50 text-red-600 rounded-lg hover:bg-red-100"
                        >
                          <Trash2 className="w-4 h-4" />
                          Svuota tutto
                        </button>
                      </div>

                      <div className="space-y-4 max-h-[40vh] overflow-y-auto pr-2">
                        {Object.entries(categoryLabels).map(([catKey, catLabel]) => {
                          const items = groupedItems[catKey]
                          if (!items || items.length === 0) return null
                          
                          return (
                            <div key={catKey}>
                              <h3 className="font-display font-bold text-burgundy-900 mb-2 flex items-center gap-2">
                                <span className="w-2 h-2 bg-gold-500 rounded-full"></span>
                                {catLabel}
                                <span className="text-sm font-normal text-burgundy-500">({items.length})</span>
                              </h3>
                              <div className="space-y-1">
                                {items.map(item => (
                                  <div 
                                    key={item.id}
                                    className="bg-white rounded-lg border border-burgundy-100 p-2 flex items-center gap-2"
                                  >
                                    {editingItem === item.id ? (
                                      <div className="flex-1 space-y-2">
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
                                            onClick={() => setEditingItem(null)}
                                            className="p-1 text-green-600 hover:bg-green-50 rounded"
                                          >
                                            <Save className="w-4 h-4" />
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
                                      <>
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
                                        <button
                                          onClick={() => setEditingItem(item.id)}
                                          className="p-1 text-burgundy-400 hover:text-burgundy-600 hover:bg-burgundy-50 rounded"
                                        >
                                          <Edit3 className="w-4 h-4" />
                                        </button>
                                        <button
                                          onClick={() => handleDeleteItem(item.id)}
                                          className="p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded"
                                        >
                                          <Trash2 className="w-4 h-4" />
                                        </button>
                                      </>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                  
                  {parsedItems.length === 0 && (
                    <div className="text-center py-8 text-burgundy-400">
                      <ChefHat className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>Nessun piatto ancora inserito</p>
                      <p className="text-sm">Inizia ad aggiungere i piatti del tuo menù</p>
                    </div>
                  )}
                </div>
              )}

              {/* Step 2: Wine List Upload - CSV Only */}
              {currentStep === 1 && (
                <div className="space-y-6">
                  {parsedWines.length === 0 ? (
                    <div className="bg-white rounded-xl border-2 border-dashed border-burgundy-200 p-6">
                      <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                          <Upload className="w-6 h-6 text-green-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-burgundy-900">
                            Carica file CSV
                          </h3>
                          <p className="text-sm text-burgundy-600">
                            Il CSV deve contenere: nome, tipo, prezzo (obbligatori) e opzionalmente regione, vitigno, anno, produttore
                          </p>
                        </div>
                      </div>
                      
                      <CsvWineUpload
                        venueId={venue?.id}
                        onWinesParsed={(wines) => {
                          setParsedWines(wines)
                        }}
                      />
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center justify-between mb-4">
                        <p className="text-burgundy-600">
                          <span className="font-bold text-burgundy-900">{parsedWines.length}</span> vini estratti
                        </p>
                        <div className="flex gap-2">
                          <button
                            onClick={handleAddWine}
                            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-burgundy-100 text-burgundy-700 rounded-lg hover:bg-burgundy-200"
                          >
                            <Plus className="w-4 h-4" />
                            Aggiungi
                          </button>
                          <button
                            onClick={() => { 
                              setParsedWines([])
                            }}
                            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-red-50 text-red-600 rounded-lg hover:bg-red-100"
                          >
                            <Trash2 className="w-4 h-4" />
                            Ricomincia
                          </button>
                        </div>
                      </div>


                      {/* Grouped wines */}
                      <div className="space-y-6 max-h-[50vh] overflow-y-auto pr-2">
                        {Object.entries(wineTypeLabels).map(([typeKey, typeLabel]) => {
                          const wines = groupedWines[typeKey]
                          if (!wines || wines.length === 0) return null
                          
                          return (
                            <div key={typeKey}>
                              <h3 className="font-display font-bold text-burgundy-900 mb-3 flex items-center gap-2">
                                <span className={`w-2 h-2 rounded-full ${
                                  typeKey === 'red' ? 'bg-red-500' :
                                  typeKey === 'white' ? 'bg-yellow-300' :
                                  typeKey === 'rose' ? 'bg-pink-400' :
                                  typeKey === 'sparkling' ? 'bg-amber-300' :
                                  'bg-burgundy-500'
                                }`}></span>
                                {typeLabel}
                                <span className="text-sm font-normal text-burgundy-500">({wines.length})</span>
                              </h3>
                              <div className="space-y-2">
                                {wines.map(wine => (
                                  <div 
                                    key={wine.id}
                                    className="bg-white rounded-lg border border-burgundy-100 p-3 flex items-center gap-3"
                                  >
                                    {editingWine === wine.id ? (
                                      <div className="flex-1 flex flex-wrap gap-2">
                                        <input
                                          type="text"
                                          value={wine.name}
                                          onChange={(e) => handleUpdateWine(wine.id, 'name', e.target.value)}
                                          className="flex-1 min-w-[200px] px-2 py-1 border border-burgundy-200 rounded text-sm"
                                          placeholder="Nome vino"
                                          autoFocus
                                        />
                                        <select
                                          value={wine.type}
                                          onChange={(e) => handleUpdateWine(wine.id, 'type', e.target.value)}
                                          className="px-2 py-1 border border-burgundy-200 rounded text-sm"
                                        >
                                          {Object.entries(wineTypeLabels).map(([k, v]) => (
                                            <option key={k} value={k}>{v}</option>
                                          ))}
                                        </select>
                                        <input
                                          type="text"
                                          value={wine.region || ''}
                                          onChange={(e) => handleUpdateWine(wine.id, 'region', e.target.value)}
                                          className="w-28 px-2 py-1 border border-burgundy-200 rounded text-sm"
                                          placeholder="Regione"
                                        />
                                        <input
                                          type="number"
                                          value={wine.price || ''}
                                          onChange={(e) => handleUpdateWine(wine.id, 'price', e.target.value ? parseFloat(e.target.value) : null)}
                                          className="w-20 px-2 py-1 border border-burgundy-200 rounded text-sm"
                                          placeholder="€"
                                        />
                                        <button
                                          onClick={() => setEditingWine(null)}
                                          className="p-1 text-green-600 hover:bg-green-50 rounded"
                                        >
                                          <Save className="w-4 h-4" />
                                        </button>
                                      </div>
                                    ) : (
                                      <>
                                        <div className="flex-1">
                                          <span className="text-burgundy-900 font-medium">{wine.name}</span>
                                          {wine.vintage && (
                                            <span className="text-sm text-burgundy-500 ml-2">{wine.vintage}</span>
                                          )}
                                          {wine.region && (
                                            <span className="text-sm text-burgundy-400 ml-2">• {wine.region}</span>
                                          )}
                                        </div>
                                        {wine.price && (
                                          <span className="text-sm text-gold-600 font-medium">€{wine.price}</span>
                                        )}
                                        <button
                                          onClick={() => setEditingWine(wine.id)}
                                          className="p-1 text-burgundy-400 hover:text-burgundy-600 hover:bg-burgundy-50 rounded"
                                        >
                                          <Edit3 className="w-4 h-4" />
                                        </button>
                                        <button
                                          onClick={() => handleDeleteWine(wine.id)}
                                          className="p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded"
                                        >
                                          <Trash2 className="w-4 h-4" />
                                        </button>
                                      </>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Step 3: Target Audience */}
              {currentStep === 2 && (
                <div className="space-y-3">
                  <p className="text-sm text-burgundy-500 mb-4">
                    Seleziona una o più opzioni
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    {targetOptions.map(option => (
                      <button
                        key={option.value}
                        onClick={() => handleTargetSelect(option.value)}
                        className={`p-4 rounded-xl border-2 text-left transition-all ${
                          formData.target_audience.includes(option.value)
                            ? 'border-gold-500 bg-gold-50'
                            : 'border-burgundy-200 hover:border-burgundy-400'
                        }`}
                      >
                        <span className="text-2xl mb-2 block">{option.icon}</span>
                        <span className="font-medium text-burgundy-900">{option.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Step 4: Sommelier Style */}
              {currentStep === 3 && (
                <div className="space-y-3">
                  {styleOptions.map(option => (
                    <button
                      key={option.value}
                      onClick={() => handleStyleSelect(option.value)}
                      className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                        formData.sommelier_style === option.value
                          ? 'border-gold-500 bg-gold-50'
                          : 'border-burgundy-200 hover:border-burgundy-400'
                      }`}
                    >
                      <span className="font-medium text-burgundy-900 block mb-1">
                        {option.label}
                      </span>
                      <span className="text-sm text-burgundy-600">
                        {option.description}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex justify-between mt-8">
            <button
              onClick={handleBack}
              disabled={currentStep === 0}
              className="flex items-center gap-2 text-burgundy-600 hover:text-burgundy-900 disabled:opacity-0"
            >
              <ArrowLeft className="w-5 h-5" />
              Indietro
            </button>
            <button
              onClick={handleNext}
              disabled={!canProceed() || isSubmitting}
              className="btn-primary flex items-center gap-2"
            >
              {currentStep === steps.length - 1 ? (
                isSubmitting ? (
                  'Salvataggio...'
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Completa
                  </>
                )
              ) : (
                <>
                  Continua
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Onboarding
