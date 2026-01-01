import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Plus, 
  Search, 
  Filter, 
  Upload, 
  Wine, 
  Edit2, 
  Trash2,
  X,
  Save,
  FileText
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { productService } from '../services/api'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import toast from 'react-hot-toast'

function DashboardProducts() {
  const { venue } = useAuth()
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState('all')
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingProduct, setEditingProduct] = useState(null)
  const [descriptionPopup, setDescriptionPopup] = useState(null)

  useEffect(() => {
    if (venue?.id) {
      loadProducts()
    }
  }, [venue?.id])

  const loadProducts = async () => {
    if (!venue?.id) {
      console.warn('[DashboardProducts] No venue ID, cannot load products')
      setProducts([])
      setLoading(false)
      return
    }
    
    console.log('[DashboardProducts] Loading products for venue', venue.id)
    setLoading(true)
    try {
      const response = await productService.getProducts(venue.id)
      console.log('[DashboardProducts] Products response:', response.data)
      
      // API returns array directly or wrapped in data
      const productsData = Array.isArray(response.data) ? response.data : (response.data?.products || [])
      console.log('[DashboardProducts] Setting products:', productsData.length, productsData)
      setProducts(productsData)
      
      if (productsData.length === 0) {
        console.log('[DashboardProducts] No products found (this is OK if catalog is empty)')
      }
    } catch (error) {
      console.error('[DashboardProducts] Error loading products:', error)
      console.error('[DashboardProducts] Error response:', error.response)
      console.error('[DashboardProducts] Error status:', error.response?.status)
      console.error('[DashboardProducts] Error data:', error.response?.data)
      
      // Show error to user
      const errorMsg = error.response?.data?.message || 'Errore durante il caricamento dei prodotti'
      toast.error(errorMsg)
      
      // Set empty array instead of demo data
      setProducts([])
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Sei sicuro di voler eliminare questo prodotto?')) return
    
    try {
      await productService.deleteProduct(id)
      setProducts(prev => prev.filter(p => p.id !== id))
      toast.success('Prodotto eliminato')
    } catch (error) {
      toast.error('Errore durante l\'eliminazione')
    }
  }

  const wineTypes = [
    { value: 'all', label: 'Tutti' },
    { value: 'red', label: 'Rossi' },
    { value: 'white', label: 'Bianchi' },
    { value: 'rose', label: 'Rosati' },
    { value: 'sparkling', label: 'Bollicine' }
  ]

  const filteredProducts = products.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         product.region?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = selectedType === 'all' || product.type === selectedType
    return matchesSearch && matchesType
  })

  const getTypeColor = (type) => {
    switch (type) {
      case 'red': return 'bg-burgundy-100 text-burgundy-800'
      case 'white': return 'bg-amber-100 text-amber-800'
      case 'rose': return 'bg-pink-100 text-pink-800'
      case 'sparkling': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeLabel = (type) => {
    switch (type) {
      case 'red': return 'Rosso'
      case 'white': return 'Bianco'
      case 'rose': return 'Rosato'
      case 'sparkling': return 'Spumante'
      default: return type
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-burgundy-900">
            Carta Vini
          </h1>
          <p className="text-burgundy-600">
            Gestisci i prodotti della tua carta
          </p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => setShowAddModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Aggiungi Vino
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-burgundy-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Cerca per nome o regione..."
              className="input-field pl-12"
            />
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {wineTypes.map(type => (
              <button
                key={type.value}
                onClick={() => setSelectedType(type.value)}
                className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                  selectedType === type.value
                    ? 'bg-burgundy-900 text-cream-50'
                    : 'bg-burgundy-100 text-burgundy-700 hover:bg-burgundy-200'
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Products Table */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-burgundy-100">
                  <th className="text-left py-4 px-4 font-semibold text-burgundy-900">Nome</th>
                  <th className="text-left py-4 px-4 font-semibold text-burgundy-900">Tipo</th>
                  <th className="text-left py-4 px-4 font-semibold text-burgundy-900">Regione</th>
                  <th className="text-left py-4 px-4 font-semibold text-burgundy-900">Vitigno</th>
                  <th className="text-left py-4 px-4 font-semibold text-burgundy-900">Anno</th>
                  <th className="text-left py-4 px-4 font-semibold text-burgundy-900">Prezzo</th>
                  <th className="text-left py-4 px-4 font-semibold text-burgundy-900">Descrizione</th>
                  <th className="text-right py-4 px-4 font-semibold text-burgundy-900">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.map((product, index) => (
                  <motion.tr
                    key={product.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: index * 0.05 }}
                    className="border-b border-burgundy-50 hover:bg-cream-50"
                  >
                    <td className="py-4 px-4">
                      <span className="font-medium text-burgundy-900">{product.name}</span>
                    </td>
                    <td className="py-4 px-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(product.type)}`}>
                        {getTypeLabel(product.type)}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-burgundy-700">{product.region}</td>
                    <td className="py-4 px-4 text-burgundy-700">{product.grape_variety}</td>
                    <td className="py-4 px-4 text-burgundy-700">{product.vintage}</td>
                    <td className="py-4 px-4 text-burgundy-900 font-medium">€{product.price}</td>
                    <td className="py-4 px-4">
                      {product.description ? (
                        <button
                          onClick={() => setDescriptionPopup(product)}
                          className="p-2 text-burgundy-600 hover:text-burgundy-900 hover:bg-burgundy-100 rounded-lg transition-colors"
                          title="Visualizza descrizione"
                        >
                          <FileText className="w-4 h-4" />
                        </button>
                      ) : (
                        <span className="text-burgundy-300 text-sm">-</span>
                      )}
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => setEditingProduct(product)}
                          className="p-2 text-burgundy-600 hover:text-burgundy-900 hover:bg-burgundy-100 rounded-lg"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleDelete(product.id)}
                          className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredProducts.length === 0 && (
            <div className="text-center py-12">
              <Wine className="w-12 h-12 text-burgundy-300 mx-auto mb-4" />
              <p className="text-burgundy-600">Nessun prodotto trovato</p>
            </div>
          )}
        </div>
      )}

      {/* Description Popup */}
      <AnimatePresence>
        {descriptionPopup && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-burgundy-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setDescriptionPopup(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-burgundy-100 flex items-center justify-between">
                <h2 className="font-display text-xl font-bold text-burgundy-900">
                  Descrizione - {descriptionPopup.name}
                </h2>
                <button 
                  onClick={() => setDescriptionPopup(null)} 
                  className="p-2 hover:bg-burgundy-100 rounded-lg"
                >
                  <X className="w-5 h-5 text-burgundy-600" />
                </button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                <p className="text-burgundy-700 whitespace-pre-wrap leading-relaxed">
                  {descriptionPopup.description}
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Add/Edit Modal */}
      <AnimatePresence>
        {(showAddModal || editingProduct) && (
          <ProductModal
            product={editingProduct}
            onClose={() => {
              setShowAddModal(false)
              setEditingProduct(null)
            }}
            onSave={async (product) => {
              try {
                if (editingProduct) {
                  // Update existing product
                  const response = await productService.updateProduct(product.id, product)
                  // API returns { message, product }
                  const updatedProduct = response.data?.product || response.data
                  setProducts(prev => prev.map(p => p.id === product.id ? updatedProduct : p))
                  toast.success('Prodotto aggiornato!')
                } else {
                  // Create new product
                  const response = await productService.createProduct({
                    ...product,
                    venue_id: venue.id
                  })
                  // API returns { message, product }
                  const newProduct = response.data?.product || response.data
                  setProducts(prev => [...prev, newProduct])
                  toast.success('Prodotto aggiunto!')
                }
                setShowAddModal(false)
                setEditingProduct(null)
              } catch (error) {
                console.error('[DashboardProducts] Error saving product:', error)
                const errorMsg = error.response?.data?.message || 'Errore durante il salvataggio'
                toast.error(errorMsg)
              }
            }}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

function ProductModal({ product, onClose, onSave }) {
  const [formData, setFormData] = useState(product || {
    name: '',
    type: 'red',
    region: '',
    grape_variety: '',
    vintage: new Date().getFullYear(),
    price: '',
    description: '',
    tasting_notes: '',
    is_available: true
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    await onSave(formData)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-burgundy-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-burgundy-100 flex items-center justify-between">
          <h2 className="font-display text-xl font-bold text-burgundy-900">
            {product ? 'Modifica Vino' : 'Aggiungi Vino'}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-burgundy-100 rounded-lg">
            <X className="w-5 h-5 text-burgundy-600" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-burgundy-700 mb-1">Nome *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="input-field"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-burgundy-700 mb-1">Tipo *</label>
              <select
                value={formData.type}
                onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value }))}
                className="input-field"
              >
                <option value="red">Rosso</option>
                <option value="white">Bianco</option>
                <option value="rose">Rosato</option>
                <option value="sparkling">Spumante</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-burgundy-700 mb-1">Regione</label>
              <input
                type="text"
                value={formData.region}
                onChange={(e) => setFormData(prev => ({ ...prev, region: e.target.value }))}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-burgundy-700 mb-1">Vitigno</label>
              <input
                type="text"
                value={formData.grape_variety}
                onChange={(e) => setFormData(prev => ({ ...prev, grape_variety: e.target.value }))}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-burgundy-700 mb-1">Annata</label>
              <input
                type="number"
                value={formData.vintage}
                onChange={(e) => setFormData(prev => ({ ...prev, vintage: parseInt(e.target.value) }))}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-burgundy-700 mb-1">Prezzo (€) *</label>
              <input
                type="number"
                step="0.01"
                value={formData.price}
                onChange={(e) => setFormData(prev => ({ ...prev, price: parseFloat(e.target.value) }))}
                className="input-field"
                required
              />
            </div>
            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_available}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_available: e.target.checked }))}
                  className="w-4 h-4 text-burgundy-900 rounded"
                />
                <span className="text-sm font-medium text-burgundy-700">Disponibile</span>
              </label>
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-burgundy-700 mb-1">Descrizione</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="input-field"
                rows={3}
              />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-burgundy-700 mb-1">Note di Degustazione</label>
              <textarea
                value={formData.tasting_notes}
                onChange={(e) => setFormData(prev => ({ ...prev, tasting_notes: e.target.value }))}
                className="input-field"
                rows={2}
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-outline">
              Annulla
            </button>
            <button type="submit" className="btn-primary flex items-center gap-2">
              <Save className="w-4 h-4" />
              Salva
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  )
}

export default DashboardProducts

