import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Sparkles, QrCode, BarChart3, MessageSquare, ArrowRight, CheckCircle2 } from 'lucide-react'
import Logo from '../components/ui/Logo'

function LandingPage() {
  const features = [
    {
      icon: MessageSquare,
      title: 'Sommelier AI',
      description: 'Un sommelier virtuale che consiglia i vini perfetti ai tuoi clienti basandosi sulle loro preferenze e portate.'
    },
    {
      icon: QrCode,
      title: 'QR Code al Tavolo',
      description: 'I clienti accedono al sommelier digitale semplicemente scansionando un QR code dal loro smartphone.'
    },
    {
      icon: BarChart3,
      title: 'Analytics Avanzate',
      description: 'Monitora le preferenze dei clienti, i vini più richiesti e ottimizza la tua carta vini.'
    },
    {
      icon: Sparkles,
      title: 'Selezione Intelligente',
      description: 'Ti aiutiamo a selezionare i prodotti per la tua carta vini in base al tipo di cucina e clientela.'
    }
  ]

  const benefits = [
    'Aumenta i margini da vino fino al 30%',
    'Migliora l\'esperienza cliente',
    'Ottimizza la tua carta vini',
    'Gestisci la rotazione grazie all\'IA e ai dati'
  ]

  return (
    <div className="min-h-screen bg-cream-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-effect border-b border-burgundy-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Logo size="md" />
              <span className="font-display text-2xl font-bold text-burgundy-900">LIBER</span>
            </div>
            <div className="flex items-center gap-4">
              <Link to="/login" className="text-burgundy-900 hover:text-burgundy-700 font-medium">
                Accedi
              </Link>
              <Link to="/register" className="btn-primary">
                Inizia Ora
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 bg-wine-pattern">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-gold-100 text-gold-700 rounded-full text-sm font-medium mb-6">
                <Sparkles className="w-4 h-4" />
                Powered by AI
              </div>
              <h1 className="font-display text-5xl lg:text-6xl font-bold text-burgundy-900 leading-tight mb-6">
                Il Sommelier AI per il tuo{' '}
                <span className="gradient-text">Ristorante</span>
              </h1>
              <p className="text-lg text-burgundy-700 mb-8 leading-relaxed">
                Trasforma l'esperienza enologica dei tuoi clienti con un sommelier virtuale 
                intelligente. Suggerimenti personalizzati, carta vini ottimizzata e analytics 
                avanzate per il tuo locale.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link to="/register" className="btn-primary inline-flex items-center justify-center gap-2">
                  Inizia Ora
                  <ArrowRight className="w-5 h-5" />
                </Link>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative"
            >
              {/* Phone mockup */}
              <div className="relative mx-auto w-72 h-[580px] bg-burgundy-900 rounded-[3rem] p-3 shadow-2xl">
                <div className="w-full h-full bg-cream-50 rounded-[2.5rem] overflow-hidden relative">
                  {/* Phone notch */}
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-6 bg-burgundy-900 rounded-b-2xl" />
                  
                  {/* Chat preview */}
                  <div className="pt-10 px-4 h-full flex flex-col">
                    <div className="text-center py-4 border-b border-burgundy-100">
                      <p className="font-display font-semibold text-burgundy-900">Ristorante Da Mario</p>
                      <p className="text-sm text-burgundy-500">Sommelier AI</p>
                    </div>
                    
                    <div className="flex-1 py-4 space-y-3 overflow-hidden">
                      <div className="chat-bubble-ai text-sm">
                        Buonasera! Sono il sommelier di Ristorante Da Mario. Come posso aiutarla nella scelta del vino?
                      </div>
                      <div className="chat-bubble-user text-sm">
                        Che vino mi consigli con la tagliata di manzo?
                      </div>
                      <div className="chat-bubble-ai text-sm">
                        Ottima scelta! Per la tagliata le consiglio il nostro Brunello di Montalcino 2018...
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating elements */}
              <motion.div
                animate={{ y: [0, -10, 0] }}
                transition={{ duration: 3, repeat: Infinity }}
                className="absolute -left-8 top-20 bg-white rounded-xl shadow-wine p-4"
              >
                <Logo size="md" />
              </motion.div>
              <motion.div
                animate={{ y: [0, 10, 0] }}
                transition={{ duration: 3, repeat: Infinity, delay: 0.5 }}
                className="absolute -right-8 bottom-32 bg-gold-500 rounded-xl shadow-gold p-4"
              >
                <Sparkles className="w-8 h-8 text-burgundy-900" />
              </motion.div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-16 bg-burgundy-900">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {benefits.map((benefit, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center gap-3 text-cream-50"
              >
                <CheckCircle2 className="w-6 h-6 text-gold-500 flex-shrink-0" />
                <span className="text-sm lg:text-base">{benefit}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-4">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="font-display text-4xl font-bold text-burgundy-900 mb-4">
              Tutto ciò che ti serve
            </h2>
            <p className="text-lg text-burgundy-600 max-w-2xl mx-auto">
              Una piattaforma completa per gestire l'esperienza enologica del tuo ristorante
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="card-wine text-center group"
              >
                <div className="w-14 h-14 mx-auto mb-4 bg-burgundy-100 rounded-2xl flex items-center justify-center group-hover:bg-gold-500 transition-colors">
                  <feature.icon className="w-7 h-7 text-burgundy-900" />
                </div>
                <h3 className="font-display text-xl font-semibold text-burgundy-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-burgundy-600">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4 bg-gradient-to-br from-burgundy-900 via-burgundy-800 to-burgundy-900">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-display text-4xl lg:text-5xl font-bold text-cream-50 mb-6">
              Pronto a trasformare il tuo ristorante?
            </h2>
            <p className="text-lg text-cream-100/80 mb-8">
              Porta l'esperienza enologica del tuo locale al livello successivo.
            </p>
            <Link 
              to="/register" 
              className="btn-secondary inline-flex items-center gap-2 text-lg px-8 py-4"
            >
              Registra il tuo Ristorante
              <ArrowRight className="w-5 h-5" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-burgundy-950 text-cream-100 py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <Logo size="md" />
              <span className="font-display text-xl font-bold">LIBER</span>
            </div>
            <p className="text-sm text-cream-100/60">
              © 2024 LIBER. Tutti i diritti riservati.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage

