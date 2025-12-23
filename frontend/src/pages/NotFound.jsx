import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Home, ArrowLeft } from 'lucide-react'
import Logo from '../components/ui/Logo'

function NotFound() {
  return (
    <div className="min-h-screen bg-cream-50 flex items-center justify-center p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <motion.div
          animate={{ rotate: [0, -10, 10, -10, 0] }}
          transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
          className="w-24 h-24 mx-auto mb-8 bg-burgundy-100 rounded-3xl flex items-center justify-center"
        >
          <Logo size="lg" />
        </motion.div>
        
        <h1 className="font-display text-8xl font-bold text-burgundy-900 mb-4">
          404
        </h1>
        <h2 className="font-display text-2xl font-semibold text-burgundy-800 mb-4">
          Pagina non trovata
        </h2>
        <p className="text-burgundy-600 mb-8 max-w-md">
          Sembra che questa bottiglia sia stata già stappata altrove. 
          La pagina che cerchi non esiste o è stata spostata.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/" className="btn-primary inline-flex items-center justify-center gap-2">
            <Home className="w-5 h-5" />
            Torna alla Home
          </Link>
          <button 
            onClick={() => window.history.back()}
            className="btn-outline inline-flex items-center justify-center gap-2"
          >
            <ArrowLeft className="w-5 h-5" />
            Torna Indietro
          </button>
        </div>
      </motion.div>
    </div>
  )
}

export default NotFound

