import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Wine, 
  Sparkles,
  ChefHat,
  Menu,
  ExternalLink,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { venueService } from '../services/api'
import Logo from '../components/ui/Logo'

function VenueLanding() {
  const { venueSlug } = useParams()
  const navigate = useNavigate()
  const [venue, setVenue] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadVenue()
  }, [venueSlug])

  const loadVenue = async () => {
    try {
      setError(null)
      const response = await venueService.getVenue(venueSlug)
      setVenue(response.data)
    } catch (err) {
      console.error('Error loading venue:', err)
      setError('Impossibile caricare il ristorante. Verifica il link e riprova.')
    } finally {
      setLoading(false)
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-burgundy-950 via-burgundy-900 to-burgundy-950 flex items-center justify-center">
        <div className="text-center">
          <Logo size="xl" animate className="mx-auto mb-4" />
          <p className="text-cream-100/70">Caricamento...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error || !venue) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-burgundy-950 via-burgundy-900 to-burgundy-950 flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-10 h-10 text-red-400" />
          </div>
          <h2 className="font-display text-2xl font-bold text-cream-50 mb-4">
            Errore di Caricamento
          </h2>
          <p className="text-cream-100/70 mb-6">{error || 'Ristorante non trovato'}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-gold-500 text-burgundy-900 rounded-xl font-semibold hover:bg-gold-400 transition-colors"
          >
            Riprova
          </button>
        </div>
      </div>
    )
  }

  // Check which buttons should be shown
  const showMenuButton = venue.menu_link_enabled && venue.menu_link
  const showWineListButton = venue.wine_list_link_enabled && venue.wine_list_link

  return (
    <div className="min-h-screen bg-gradient-to-br from-burgundy-950 via-burgundy-900 to-burgundy-950">
      {/* Header */}
      <header className="bg-burgundy-900/50 backdrop-blur-sm border-b border-burgundy-800 px-4 py-6">
        <div className="max-w-2xl mx-auto flex items-center justify-center gap-4">
          {venue.logo_url ? (
            <img 
              src={venue.logo_url} 
              alt={venue.name}
              className="h-16 w-16 object-contain rounded-xl"
            />
          ) : (
            <Logo size="lg" className="rounded-xl" />
          )}
          <div className="text-center">
            <h1 className="font-display font-bold text-2xl text-cream-50">
              {venue.name}
            </h1>
            {venue.description && (
              <p className="text-sm text-cream-100/70 mt-1">{venue.description}</p>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-2xl mx-auto px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring' }}
            className="w-32 h-32 bg-gradient-to-br from-gold-400 to-gold-600 rounded-full flex items-center justify-center mx-auto mb-8 shadow-lg"
          >
            <Wine className="w-16 h-16 text-burgundy-900" />
          </motion.div>
          
          <h2 className="font-display text-3xl font-bold text-cream-50 mb-4">
            Benvenuto!
          </h2>
          
          <p className="text-cream-100/80 text-lg leading-relaxed max-w-md mx-auto">
            Scegli come vuoi esplorare la nostra offerta
          </p>
        </motion.div>

        {/* Action Buttons */}
        <div className="space-y-4 max-w-md mx-auto">
          {/* Menu Button */}
          {showMenuButton && (
            <motion.a
              href={venue.menu_link}
              target="_blank"
              rel="noopener noreferrer"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="block w-full"
            >
              <button className="w-full flex items-center justify-between p-6 bg-burgundy-800/50 hover:bg-burgundy-800 rounded-2xl border-2 border-burgundy-700/50 hover:border-gold-500/50 transition-all group">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-gold-500/20 rounded-xl flex items-center justify-center group-hover:bg-gold-500/30 transition-colors">
                    <Menu className="w-7 h-7 text-gold-400" />
                  </div>
                  <div className="text-left">
                    <h3 className="font-display font-bold text-xl text-cream-50">
                      Menù
                    </h3>
                    <p className="text-sm text-cream-100/70">
                      Visualizza il nostro menù digitale
                    </p>
                  </div>
                </div>
                <ExternalLink className="w-5 h-5 text-cream-100/50 group-hover:text-gold-400 transition-colors" />
              </button>
            </motion.a>
          )}

          {/* Wine List Button */}
          {showWineListButton && (
            <motion.a
              href={venue.wine_list_link}
              target="_blank"
              rel="noopener noreferrer"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="block w-full"
            >
              <button className="w-full flex items-center justify-between p-6 bg-burgundy-800/50 hover:bg-burgundy-800 rounded-2xl border-2 border-burgundy-700/50 hover:border-gold-500/50 transition-all group">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-gold-500/20 rounded-xl flex items-center justify-center group-hover:bg-gold-500/30 transition-colors">
                    <Wine className="w-7 h-7 text-gold-400" />
                  </div>
                  <div className="text-left">
                    <h3 className="font-display font-bold text-xl text-cream-50">
                      Carta dei vini
                    </h3>
                    <p className="text-sm text-cream-100/70">
                      Esplora la nostra selezione di vini
                    </p>
                  </div>
                </div>
                <ExternalLink className="w-5 h-5 text-cream-100/50 group-hover:text-gold-400 transition-colors" />
              </button>
            </motion.a>
          )}

          {/* Sommelier Button - Always visible */}
          <motion.button
            onClick={() => navigate(`/v/${venueSlug}`)}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="w-full flex items-center justify-between p-6 bg-gold-500 hover:bg-gold-400 text-burgundy-900 rounded-2xl border-2 border-gold-400 hover:border-gold-300 transition-all group shadow-lg"
          >
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-burgundy-900/20 rounded-xl flex items-center justify-center group-hover:bg-burgundy-900/30 transition-colors">
                <Sparkles className="w-7 h-7 text-burgundy-900" />
              </div>
              <div className="text-left">
                <h3 className="font-display font-bold text-xl">
                  Liber - Il tuo sommelier
                </h3>
                <p className="text-sm text-burgundy-900/80">
                  Chiedi consiglio al nostro sommelier virtuale
                </p>
              </div>
            </div>
            <ChefHat className="w-5 h-5 text-burgundy-900" />
          </motion.button>
        </div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-12 text-center"
        >
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-burgundy-800/50 rounded-full text-cream-100/70 text-sm">
            <Sparkles className="w-4 h-4 text-gold-400" />
            Powered by Liber
          </span>
        </motion.div>
      </div>
    </div>
  )
}

export default VenueLanding
