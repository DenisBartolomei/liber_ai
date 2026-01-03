import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { Upload, FileText, X, Check, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

function CsvWineUpload({ onWinesParsed, venueId }) {
  const [isDragging, setIsDragging] = useState(false)
  const [isParsing, setIsParsing] = useState(false)
  const [parsedWines, setParsedWines] = useState([])
  const [errors, setErrors] = useState([])
  const fileInputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const validateFile = (file) => {
    if (!file.name.endsWith('.csv')) {
      toast.error('Il file deve essere un CSV')
      return false
    }
    return true
  }

  const handleFileSelect = async (file) => {
    if (!validateFile(file)) return

    setIsParsing(true)
    setErrors([])
    setParsedWines([])

    try {
      const formData = new FormData()
      formData.append('file', file)

      const token = localStorage.getItem('token')
      const response = await fetch(`/api/products/parse-csv/${venueId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
          // Note: Do NOT set Content-Type header - browser sets it automatically for FormData
        },
        body: formData
      })

      // Check if response is JSON before parsing
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text()
        console.error('Server returned non-JSON response:', text.substring(0, 200))
        throw new Error(`Errore del server (${response.status}): La risposta non è in formato JSON`)
      }

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || `Errore durante il parsing del CSV (${response.status})`)
      }

      setParsedWines(data.wines || [])
      setErrors(data.errors || [])
      
      if (data.wines && data.wines.length > 0) {
        const savedCount = data.saved || data.wines.length
        toast.success(`${savedCount} vini salvati nel database${data.errors && data.errors.length > 0 ? `, ${data.errors.length} errori` : ''}`)
        onWinesParsed(data.wines)
      } else if (data.saved === 0) {
        // No wines saved
        if (data.errors && data.errors.length > 0) {
          toast.error(`Nessun vino salvato. ${data.errors.length} errori trovati nel CSV`, {
            duration: 5000
          })
        } else {
          toast.error('Nessun vino trovato nel CSV')
        }
      }

      if (data.errors && data.errors.length > 0 && data.wines && data.wines.length > 0) {
        // Show errors as warning if some wines were saved
        toast.error(`${data.errors.length} errori trovati nel CSV`, {
          duration: 5000
        })
      }

    } catch (error) {
      console.error('Error parsing CSV:', error)
      toast.error(error.message || 'Errore durante il parsing del CSV')
    } finally {
      setIsParsing(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  const handleFileInput = (e) => {
    const file = e.target.files[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  const clearResults = () => {
    setParsedWines([])
    setErrors([])
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-4">
      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-xl p-8 text-center transition-colors
          ${isDragging 
            ? 'border-gold-500 bg-gold-50' 
            : 'border-burgundy-200 hover:border-burgundy-400'
          }
          ${isParsing ? 'opacity-50 pointer-events-none' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileInput}
          className="hidden"
        />

        <div className="flex flex-col items-center gap-4">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
            isDragging ? 'bg-gold-100' : 'bg-burgundy-100'
          }`}>
            {isParsing ? (
              <div className="w-8 h-8 border-4 border-burgundy-600 border-t-transparent rounded-full animate-spin" />
            ) : (
              <Upload className="w-8 h-8 text-burgundy-600" />
            )}
          </div>

          <div>
            <p className="font-medium text-burgundy-900 mb-1">
              {isParsing ? 'Elaborazione in corso...' : 'Trascina qui il file CSV'}
            </p>
            <p className="text-sm text-burgundy-600">
              oppure{' '}
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-gold-600 hover:text-gold-700 underline"
              >
                seleziona un file
              </button>
            </p>
          </div>

          <div className="text-xs text-burgundy-500 bg-burgundy-50 px-4 py-2 rounded-lg">
            <p className="font-medium mb-1">Formato CSV richiesto:</p>
            <p>Colonne obbligatorie: nome, tipo, prezzo</p>
            <p>Colonne opzionali: regione, vitigno, anno, produttore</p>
          </div>
        </div>
      </div>

      {/* Errors Display */}
      {errors.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-50 border border-red-200 rounded-lg p-4"
        >
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <h4 className="font-semibold text-red-900">
              Errori trovati nel CSV ({errors.length})
            </h4>
          </div>
          <div className="max-h-40 overflow-y-auto space-y-1">
            {errors.map((error, idx) => (
              <p key={idx} className="text-sm text-red-700">
                Riga {error.row}: {error.error}
              </p>
            ))}
          </div>
        </motion.div>
      )}

      {/* Parsed Wines Preview */}
      {parsedWines.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl border border-burgundy-200 p-4"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Check className="w-5 h-5 text-green-600" />
              <h4 className="font-semibold text-burgundy-900">
                {parsedWines.length} vini estratti
              </h4>
            </div>
            <button
              onClick={clearResults}
              className="text-sm text-burgundy-600 hover:text-burgundy-900 flex items-center gap-1"
            >
              <X className="w-4 h-4" />
              Ricarica
            </button>
          </div>

          <div className="max-h-60 overflow-y-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-burgundy-100">
                  <th className="text-left py-2 px-2 font-semibold text-burgundy-900">Nome</th>
                  <th className="text-left py-2 px-2 font-semibold text-burgundy-900">Tipo</th>
                  <th className="text-left py-2 px-2 font-semibold text-burgundy-900">Prezzo</th>
                  <th className="text-left py-2 px-2 font-semibold text-burgundy-900">Regione</th>
                </tr>
              </thead>
              <tbody>
                {parsedWines.map((wine, idx) => (
                  <tr key={idx} className="border-b border-burgundy-50">
                    <td className="py-2 px-2 text-burgundy-700">{wine.name}</td>
                    <td className="py-2 px-2">
                      <span className="px-2 py-0.5 rounded text-xs bg-burgundy-100 text-burgundy-700">
                        {wine.type}
                      </span>
                    </td>
                    <td className="py-2 px-2 text-burgundy-900 font-medium">€{wine.price}</td>
                    <td className="py-2 px-2 text-burgundy-600">{wine.region || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default CsvWineUpload

