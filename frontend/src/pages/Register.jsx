import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mail, Lock, User, Building2, ArrowRight, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import Logo from '../components/ui/Logo'

function Register() {
  const [formData, setFormData] = useState({
    venueName: '',
    email: '',
    password: '',
    confirmPassword: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { register } = useAuth()

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (formData.password !== formData.confirmPassword) {
      toast.error('Le password non coincidono')
      return
    }

    if (formData.password.length < 8) {
      toast.error('La password deve essere di almeno 8 caratteri')
      return
    }

    setIsLoading(true)
    
    const result = await register({
      venue_name: formData.venueName,
      email: formData.email,
      password: formData.password
    })
    
    if (!result.success) {
      toast.error(result.error)
    } else {
      toast.success('Registrazione completata!')
    }
    
    setIsLoading(false)
  }

  return (
    <div className="min-h-screen bg-cream-50 flex">
      {/* Left side - Image/Pattern */}
      <div className="hidden lg:flex flex-1 bg-burgundy-900 items-center justify-center p-12">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="w-32 h-32 mx-auto mb-8 bg-gold-500 rounded-3xl flex items-center justify-center">
            <Logo size="xl" />
          </div>
          <h2 className="font-display text-3xl font-bold text-cream-50 mb-4">
            Unisciti a LIBER
          </h2>
          <p className="text-cream-100/80 max-w-sm">
            Il sommelier AI per il tuo ristorante.
          </p>
          
          <div className="mt-12 space-y-4 text-left">
            {[
              'Sommelier AI personalizzato',
              'QR code per ogni tavolo',
              'Analytics avanzate',
              'Supporto dedicato'
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className="flex items-center gap-3 text-cream-100"
              >
                <div className="w-2 h-2 bg-gold-500 rounded-full" />
                <span>{feature}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Right side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md"
        >
          {/* Logo */}
          <Link to="/" className="inline-flex items-center gap-2 mb-8">
            <div className="w-10 h-10 bg-burgundy-900 rounded-xl flex items-center justify-center">
              <Logo size="sm" />
            </div>
            <span className="font-display text-2xl font-bold text-burgundy-900">LIBER</span>
          </Link>

          <h1 className="font-display text-3xl font-bold text-burgundy-900 mb-2">
            Crea il tuo account
          </h1>
          <p className="text-burgundy-600 mb-8">
            Configura il sommelier AI per il tuo ristorante
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="venueName" className="block text-sm font-medium text-burgundy-700 mb-2">
                Nome del Ristorante
              </label>
              <div className="relative">
                <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-burgundy-400" />
                <input
                  id="venueName"
                  name="venueName"
                  type="text"
                  value={formData.venueName}
                  onChange={handleChange}
                  className="input-field pl-12"
                  placeholder="Es. Ristorante Da Mario"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-burgundy-700 mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-burgundy-400" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="input-field pl-12"
                  placeholder="nome@ristorante.it"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-burgundy-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-burgundy-400" />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={handleChange}
                  className="input-field pl-12 pr-12"
                  placeholder="Minimo 8 caratteri"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-burgundy-400 hover:text-burgundy-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-burgundy-700 mb-2">
                Conferma Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-burgundy-400" />
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className="input-field pl-12"
                  placeholder="Ripeti la password"
                  required
                />
              </div>
            </div>

            <div className="flex items-start">
              <input 
                type="checkbox" 
                id="terms"
                required
                className="w-4 h-4 mt-1 text-burgundy-900 border-burgundy-300 rounded focus:ring-gold-500" 
              />
              <label htmlFor="terms" className="ml-2 text-sm text-burgundy-600">
                Accetto i{' '}
                <Link to="/terms" className="text-gold-600 hover:text-gold-700">
                  Termini di Servizio
                </Link>
                {' '}e la{' '}
                <Link to="/privacy" className="text-gold-600 hover:text-gold-700">
                  Privacy Policy
                </Link>
              </label>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <span>Creazione account...</span>
              ) : (
                <>
                  <span>Crea Account</span>
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-burgundy-600">
            Hai già un account?{' '}
            <Link to="/login" className="text-gold-600 hover:text-gold-700 font-semibold">
              Accedi
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}

export default Register

