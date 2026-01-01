import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Check, AlertCircle, RefreshCw, FileText, Image as ImageIcon } from 'lucide-react'
import { productService } from '../../services/api'
import toast from 'react-hot-toast'

function WineDescriptionGenerator({ wines, onDescriptionsGenerated, onLabelImageUpload }) {
  const [winesWithStatus, setWinesWithStatus] = useState([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [expandedWine, setExpandedWine] = useState(null)
  const [editingDescription, setEditingDescription] = useState(null)

  useEffect(() => {
    // Initialize wines with status
    if (wines && wines.length > 0) {
      setWinesWithStatus(
        wines.map(wine => ({
          ...wine,
          description_status: wine.description ? 'completed' : 'pending',
          description: wine.description || null
        }))
      )
    }
  }, [wines])

  const handleGenerateAll = async () => {
    if (!winesWithStatus || winesWithStatus.length === 0) {
      toast.error('Nessun vino da processare')
      return
    }

    setIsGenerating(true)
    setGenerationProgress(0)

    try {
      const venueId = JSON.parse(localStorage.getItem('venue') || '{}').id
      if (!venueId) {
        throw new Error('ID locale non trovato')
      }

      // Get wines without descriptions
      const winesToGenerate = winesWithStatus
        .filter(w => !w.description || w.description_status === 'error')
        .map(w => ({
          name: w.name,
          type: w.type,
          region: w.region,
          grape_variety: w.grape_variety,
          vintage: w.vintage,
          producer: w.producer,
          price: w.price
        }))

      if (winesToGenerate.length === 0) {
        toast.info('Tutti i vini hanno già una descrizione')
        setIsGenerating(false)
        return
      }

      const response = await productService.generateWineDescriptions(venueId, winesToGenerate)
      const generatedWines = response.data.wines || []

      // Update wines with generated descriptions
      setWinesWithStatus(prev => {
        const updated = [...prev]
        generatedWines.forEach(generatedWine => {
          const index = updated.findIndex(w => 
            w.name === generatedWine.name && 
            w.type === generatedWine.type
          )
          if (index !== -1) {
            updated[index] = {
              ...updated[index],
              description: generatedWine.description,
              description_status: generatedWine.description_status || 'completed',
              description_error: generatedWine.description_error
            }
          }
        })
        return updated
      })

      setGenerationProgress(100)
      toast.success(
        `${response.data.stats.completed} descrizioni generate con successo!`
      )

      if (response.data.stats.errors > 0) {
        toast.error(`${response.data.stats.errors} errori durante la generazione`)
      }

      // Notify parent
      if (onDescriptionsGenerated) {
        const allWines = winesWithStatus.map(w => {
          const generated = generatedWines.find(g => 
            g.name === w.name && g.type === w.type
          )
          return generated || w
        })
        onDescriptionsGenerated(allWines)
      }

    } catch (error) {
      console.error('Error generating descriptions:', error)
      toast.error(error.response?.data?.message || 'Errore durante la generazione delle descrizioni')
    } finally {
      setIsGenerating(false)
      setTimeout(() => setGenerationProgress(0), 2000)
    }
  }

  const handleRegenerateSingle = async (wineIndex) => {
    const wine = winesWithStatus[wineIndex]
    if (!wine) return

    setIsGenerating(true)

    try {
      const venueId = JSON.parse(localStorage.getItem('venue') || '{}').id
      if (!venueId) {
        throw new Error('ID locale non trovato')
      }

      const response = await productService.generateWineDescriptions(venueId, [{
        name: wine.name,
        type: wine.type,
        region: wine.region,
        grape_variety: wine.grape_variety,
        vintage: wine.vintage,
        producer: wine.producer,
        price: wine.price
      }])

      const generatedWine = response.data.wines[0]
      if (generatedWine) {
        setWinesWithStatus(prev => {
          const updated = [...prev]
          updated[wineIndex] = {
            ...updated[wineIndex],
            description: generatedWine.description,
            description_status: generatedWine.description_status || 'completed',
            description_error: generatedWine.description_error
          }
          return updated
        })
        toast.success('Descrizione rigenerata!')
      }

    } catch (error) {
      console.error('Error regenerating description:', error)
      toast.error('Errore durante la rigenerazione')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDescriptionChange = (index, newDescription) => {
    setWinesWithStatus(prev => {
      const updated = [...prev]
      updated[index] = {
        ...updated[index],
        description: newDescription
      }
      return updated
    })
  }

  const handleLabelImageUpload = async (wineIndex, file) => {
    const wine = winesWithStatus[wineIndex]
    
    // For onboarding, wines don't have IDs yet, so we just store the image locally
    // The image will be uploaded when the wine is saved
    if (!wine) {
      toast.error('Vino non trovato')
      return
    }

    // Validate file
    if (!file.type.startsWith('image/')) {
      toast.error('Il file deve essere un\'immagine')
      return
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.error('L\'immagine deve essere inferiore a 5MB')
      return
    }

    try {
      // Create preview URL for immediate display
      const previewUrl = URL.createObjectURL(file)
      
      // Store file and preview URL in wine object
      // The actual upload will happen when wine is saved during onboarding
      setWinesWithStatus(prev => {
        const updated = [...prev]
        updated[wineIndex] = {
          ...updated[wineIndex],
          image_file: file, // Store file for later upload
          image_url: previewUrl, // Preview URL
          image_preview: previewUrl
        }
        return updated
      })

      // Notify parent component with both preview URL and file
      if (onLabelImageUpload) {
        onLabelImageUpload(wineIndex, previewUrl, file)
      }

      toast.success('Foto etichetta aggiunta! Verrà caricata al salvataggio.')

    } catch (error) {
      console.error('Error handling label image:', error)
      toast.error('Errore durante il caricamento della foto')
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <Check className="w-4 h-4 text-green-600" />
      case 'generating':
        return <div className="w-4 h-4 border-2 border-burgundy-600 border-t-transparent rounded-full animate-spin" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      default:
        return <div className="w-4 h-4 border-2 border-burgundy-300 rounded-full" />
    }
  }

  const pendingCount = winesWithStatus.filter(w => 
    !w.description || w.description_status === 'error'
  ).length

  return (
    <div className="space-y-4">
      {/* Header with Generate Button */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-burgundy-900 mb-1">
            Generazione Descrizioni
          </h3>
          <p className="text-sm text-burgundy-600">
            {pendingCount > 0 
              ? `${pendingCount} vini senza descrizione`
              : 'Tutti i vini hanno una descrizione'
            }
          </p>
        </div>
        <button
          onClick={handleGenerateAll}
          disabled={isGenerating || pendingCount === 0}
          className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGenerating ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Generazione...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              Genera Descrizioni
            </>
          )}
        </button>
      </div>

      {/* Progress Bar */}
      {isGenerating && generationProgress > 0 && (
        <div className="w-full bg-burgundy-100 rounded-full h-2">
          <motion.div
            className="bg-gold-500 h-2 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${generationProgress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      )}

      {/* Wines List */}
      <div className="space-y-2 max-h-[60vh] overflow-y-auto">
        <AnimatePresence>
          {winesWithStatus.map((wine, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="bg-white rounded-lg border border-burgundy-100 p-4"
            >
              <div className="flex items-start gap-3">
                {/* Status Icon */}
                <div className="mt-1">
                  {getStatusIcon(wine.description_status)}
                </div>

                {/* Wine Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium text-burgundy-900 truncate">
                      {wine.name}
                    </h4>
                    <span className="px-2 py-0.5 rounded text-xs bg-burgundy-100 text-burgundy-700">
                      {wine.type}
                    </span>
                    {wine.vintage && (
                      <span className="text-sm text-burgundy-500">
                        {wine.vintage}
                      </span>
                    )}
                  </div>

                  {/* Description */}
                  {expandedWine === index ? (
                    <div className="space-y-2">
                      {editingDescription === index ? (
                        <textarea
                          value={wine.description || ''}
                          onChange={(e) => handleDescriptionChange(index, e.target.value)}
                          className="w-full p-2 border border-burgundy-200 rounded text-sm resize-none"
                          rows={4}
                          onBlur={() => setEditingDescription(null)}
                          autoFocus
                        />
                      ) : (
                        <div className="text-sm text-burgundy-700 whitespace-pre-wrap">
                          {wine.description || (
                            <span className="text-burgundy-400 italic">
                              Nessuna descrizione disponibile
                            </span>
                          )}
                        </div>
                      )}

                      {wine.description_error && (
                        <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
                          {wine.description_error}
                        </div>
                      )}

                      <div className="flex gap-2">
                        {!editingDescription && wine.description && (
                          <button
                            onClick={() => setEditingDescription(index)}
                            className="text-xs text-burgundy-600 hover:text-burgundy-900"
                          >
                            Modifica
                          </button>
                        )}
                        {wine.description_status === 'error' && (
                          <button
                            onClick={() => handleRegenerateSingle(index)}
                            disabled={isGenerating}
                            className="text-xs text-gold-600 hover:text-gold-700 flex items-center gap-1"
                          >
                            <RefreshCw className="w-3 h-3" />
                            Rigenera
                          </button>
                        )}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-burgundy-600 line-clamp-2">
                      {wine.description || 'Nessuna descrizione'}
                    </p>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2 mt-2">
                    {wine.description && (
                      <button
                        onClick={() => setExpandedWine(expandedWine === index ? null : index)}
                        className="text-xs text-burgundy-600 hover:text-burgundy-900 flex items-center gap-1"
                      >
                        <FileText className="w-3 h-3" />
                        {expandedWine === index ? 'Riduci' : 'Espandi'}
                      </button>
                    )}
                    
                    {/* Label Image Upload */}
                    <label className="text-xs text-burgundy-600 hover:text-burgundy-900 flex items-center gap-1 cursor-pointer">
                      <ImageIcon className="w-3 h-3" />
                      {wine.image_url ? 'Cambia foto' : 'Carica etichetta'}
                      <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => {
                          const file = e.target.files[0]
                          if (file) {
                            handleLabelImageUpload(index, file)
                          }
                        }}
                      />
                    </label>

                    {(wine.image_url || wine.image_preview) && (
                      <img
                        src={wine.image_preview || wine.image_url}
                        alt={`Etichetta ${wine.name}`}
                        className="w-8 h-8 object-cover rounded border border-burgundy-200"
                      />
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default WineDescriptionGenerator

