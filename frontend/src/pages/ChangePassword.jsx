import { useState } from 'react'
import { motion } from 'framer-motion'
import { Lock, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import Logo from '../components/ui/Logo'

function ChangePassword() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showCurrent, setShowCurrent] = useState(false)
  const [showNew, setShowNew] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { changePassword, user } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (newPassword !== confirmPassword) {
      toast.error('La nuova password e la conferma non coincidono')
      return
    }
    if (newPassword.length < 8) {
      toast.error('La nuova password deve essere di almeno 8 caratteri')
      return
    }
    setIsLoading(true)
    const result = await changePassword(currentPassword, newPassword)
    if (!result.success) {
      toast.error(result.error)
    }
    setIsLoading(false)
  }

  return (
    <div className="min-h-screen bg-cream-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="flex justify-center mb-8">
          <Logo size="lg" className="rounded-xl" />
        </div>
        <h1 className="font-display text-2xl font-bold text-burgundy-900 mb-2 text-center">
          Cambia password
        </h1>
        <p className="text-burgundy-600 mb-8 text-center">
          {user?.must_change_password
            ? 'Per accedere all\'app, imposta una nuova password personale.'
            : 'Inserisci la password corrente e scegli una nuova password.'}
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="current" className="block text-sm font-medium text-burgundy-700 mb-2">
              Password attuale
            </label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-burgundy-400" />
              <input
                id="current"
                type={showCurrent ? 'text' : 'password'}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="input-field pl-12 pr-12"
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                onClick={() => setShowCurrent(!showCurrent)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-burgundy-400 hover:text-burgundy-600"
              >
                {showCurrent ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div>
            <label htmlFor="new" className="block text-sm font-medium text-burgundy-700 mb-2">
              Nuova password
            </label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-burgundy-400" />
              <input
                id="new"
                type={showNew ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="input-field pl-12 pr-12"
                placeholder="Almeno 8 caratteri"
                required
                minLength={8}
              />
              <button
                type="button"
                onClick={() => setShowNew(!showNew)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-burgundy-400 hover:text-burgundy-600"
              >
                {showNew ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div>
            <label htmlFor="confirm" className="block text-sm font-medium text-burgundy-700 mb-2">
              Conferma nuova password
            </label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-burgundy-400" />
              <input
                id="confirm"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input-field pl-12"
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full flex items-center justify-center gap-2 py-3"
          >
            {isLoading ? 'Salvataggio...' : 'Salva nuova password'}
          </button>
        </form>
      </motion.div>
    </div>
  )
}

export default ChangePassword
