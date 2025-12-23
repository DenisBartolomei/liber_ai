import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mail, Lock, ArrowRight, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import Logo from '../components/ui/Logo'

function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    
    const result = await login(email, password)
    
    if (!result.success) {
      toast.error(result.error)
    }
    
    setIsLoading(false)
  }

  return (
    <div className="min-h-screen bg-cream-50 flex">
      {/* Left side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md"
        >
          {/* Logo */}
          <Link to="/" className="inline-flex items-center gap-2 mb-8">
            <Logo size="md" className="rounded-xl" />
            <span className="font-display text-2xl font-bold text-burgundy-900">LIBER</span>
          </Link>

          <h1 className="font-display text-3xl font-bold text-burgundy-900 mb-2">
            Bentornato
          </h1>
          <p className="text-burgundy-600 mb-8">
            Accedi al tuo account per gestire il tuo sommelier AI
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-burgundy-700 mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-burgundy-400" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
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
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pl-12 pr-12"
                  placeholder="••••••••"
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

            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input type="checkbox" className="w-4 h-4 text-burgundy-900 border-burgundy-300 rounded focus:ring-gold-500" />
                <span className="ml-2 text-sm text-burgundy-600">Ricordami</span>
              </label>
              <Link to="/forgot-password" className="text-sm text-gold-600 hover:text-gold-700 font-medium">
                Password dimenticata?
              </Link>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <span>Accesso in corso...</span>
              ) : (
                <>
                  <span>Accedi</span>
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-burgundy-600">
            Non hai un account?{' '}
            <Link to="/register" className="text-gold-600 hover:text-gold-700 font-semibold">
              Registrati gratis
            </Link>
          </p>
        </motion.div>
      </div>

      {/* Right side - Image/Pattern */}
      <div className="hidden lg:flex flex-1 bg-burgundy-900 items-center justify-center p-12">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="text-center"
        >
          <div className="w-32 h-32 mx-auto mb-8 bg-gold-500 rounded-3xl flex items-center justify-center">
            <Logo size="xl" />
          </div>
          <h2 className="font-display text-3xl font-bold text-cream-50 mb-4">
            LIBER
          </h2>
          <p className="text-cream-100/80 max-w-sm">
            Il sommelier virtuale che trasforma l'esperienza enologica dei tuoi clienti
          </p>
        </motion.div>
      </div>
    </div>
  )
}

export default Login

