import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Wine, ArrowLeft, Search, Filter, MessageSquare } from 'lucide-react'
import { productService, venueService } from '../services/api'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import WineCard from '../components/chat/WineCard'

function VenueMenu() {
  const { venueSlug } = useParams()
  const [venue, setVenue] = useState(null)
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState('all')

  useEffect(() => {
    loadData()
  }, [venueSlug])

  const loadData = async () => {
    try {
      const [venueRes, productsRes] = await Promise.all([
        venueService.getVenue(venueSlug),
        productService.getProducts(venueSlug)
      ])
      setVenue(venueRes.data)
      setProducts(productsRes.data)
    } catch (err) {
      // Demo data
      setVenue({ name: 'Ristorante Demo', cuisine_type: 'Italiana' })
      setProducts([
        { id: 1, name: 'Brunello di Montalcino 2018', type: 'red', region: 'Toscana', grape_variety: 'Sangiovese', vintage: 2018, price: 85, description: 'Elegante e strutturato con note di ciliegia e spezie' },
        { id: 2, name: 'Barolo DOCG 2017', type: 'red', region: 'Piemonte', grape_variety: 'Nebbiolo', vintage: 2017, price: 120, description: 'Potente e complesso con tannini vellutati' },
        { id: 3, name: 'Gavi di Gavi 2022', type: 'white', region: 'Piemonte', grape_variety: 'Cortese', vintage: 2022, price: 35, description: 'Fresco e minerale, perfetto con pesce e antipasti' },
        { id: 4, name: 'Franciacorta Brut', type: 'sparkling', region: 'Lombardia', grape_variety: 'Chardonnay', vintage: 2020, price: 55, description: 'Bollicine eleganti con note di frutta e brioche' },
        { id: 5, name: 'Amarone della Valpolicella 2016', type: 'red', region: 'Veneto', grape_variety: 'Corvina', vintage: 2016, price: 95, description: 'Ricco e vellutato con aromi di frutta secca' },
        { id: 6, name: 'Vermentino di Sardegna 2023', type: 'white', region: 'Sardegna', grape_variety: 'Vermentino', vintage: 2023, price: 28, description: 'Aromatico e sapido con note di agrumi' }
      ])
    } finally {
      setLoading(false)
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
                         product.region?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         product.grape_variety?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = selectedType === 'all' || product.type === selectedType
    return matchesSearch && matchesType
  })

  if (loading) {
    return (
      <div className="min-h-screen bg-cream-50 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-cream-50">
      {/* Header */}
      <header className="bg-burgundy-900 text-cream-50 px-4 py-4 sticky top-0 z-10 shadow-lg">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <Link 
              to={`/v/${venueSlug}`}
              className="flex items-center gap-2 text-cream-100 hover:text-cream-50"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Torna al sommelier</span>
            </Link>
            <div className="flex items-center gap-2">
              <Wine className="w-6 h-6 text-gold-500" />
            </div>
          </div>
          <h1 className="font-display text-2xl font-bold">{venue?.name}</h1>
          <p className="text-cream-100/70 text-sm">Carta dei Vini</p>
        </div>
      </header>

      {/* Search & Filters */}
      <div className="sticky top-[88px] z-10 bg-cream-50 border-b border-burgundy-100 px-4 py-3">
        <div className="max-w-4xl mx-auto">
          {/* Search */}
          <div className="relative mb-3">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-burgundy-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Cerca per nome, regione o vitigno..."
              className="input-field pl-12"
            />
          </div>

          {/* Type filters */}
          <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
            {wineTypes.map(type => (
              <button
                key={type.value}
                onClick={() => setSelectedType(type.value)}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                  selectedType === type.value
                    ? 'bg-burgundy-900 text-cream-50'
                    : 'bg-white text-burgundy-700 hover:bg-burgundy-100'
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Wine List */}
      <main className="px-4 py-6">
        <div className="max-w-4xl mx-auto">
          {filteredProducts.length === 0 ? (
            <div className="text-center py-12">
              <Wine className="w-12 h-12 text-burgundy-300 mx-auto mb-4" />
              <p className="text-burgundy-600">Nessun vino trovato</p>
              <p className="text-sm text-burgundy-400">Prova a modificare i filtri di ricerca</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {filteredProducts.map((wine, index) => (
                <motion.div
                  key={wine.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <WineCard wine={wine} expanded />
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Floating Chat Button */}
      <Link
        to={`/v/${venueSlug}`}
        className="fixed bottom-6 right-6 w-14 h-14 bg-burgundy-900 text-cream-50 rounded-full shadow-wine flex items-center justify-center hover:bg-burgundy-800 transition-colors"
      >
        <MessageSquare className="w-6 h-6" />
      </Link>
    </div>
  )
}

export default VenueMenu

