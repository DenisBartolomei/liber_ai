# 🍷 LIBER

Un sommelier virtuale intelligente per ristoranti, powered by AI.

## 📋 Panoramica

LIBER è una web application che offre due funzionalità principali:

1. **B2B - Per Ristoratori**: Assistente AI per la selezione e gestione della carta vini
2. **B2C - Per Clienti**: Sommelier virtuale accessibile via QR code al tavolo

## 🏗️ Architettura

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Dashboard B2B   │  │ Chat Cliente    │  │ Landing Page │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (Flask API)                        │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │ AI Agent      │  │ Vector Search │  │ Conversation Mgr │ │
│  │ (OpenAI GPT)  │  │ (Qdrant)      │  │                  │ │
│  └───────────────┘  └───────────────┘  └──────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                              ▼
┌─────────────────────┐        ┌─────────────────────┐
│  Supabase (PostgreSQL)│      │       Qdrant        │
│  (Data Storage)     │        │  (Vector Search)    │
└─────────────────────┘        └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisiti

- Docker e Docker Compose
- OpenAI API Key
- Account Supabase (per il database PostgreSQL)

### Installazione

1. **Clona il repository**
```bash
git clone <repository-url>
cd liber-sommelier-ai
```

2. **Configura Supabase**
   - Crea un progetto su [Supabase](https://supabase.com)
   - Vai su Settings → Database
   - Copia la Connection String (formato: `postgresql://postgres:[password]@[host]:5432/postgres`)

3. **Configura le variabili d'ambiente**
```bash
# Copia e modifica il file di configurazione
cp backend/.env.example backend/.env

# Imposta le variabili nel file .env
# DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres
# OPENAI_API_KEY=sk-your-api-key
```

4. **Crea le tabelle nel database Supabase**
   - Vai su Supabase Dashboard → SQL Editor
   - Esegui il file `backend/schema.sql` per creare tutte le tabelle

5. **Avvia con Docker Compose**
```bash
docker-compose up -d
```

6. **Accedi all'applicazione**
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000
- Qdrant Dashboard: http://localhost:6333/dashboard

### Sviluppo Locale (senza Docker)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Avvia il server
python run.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📁 Struttura del Progetto

```
liber-sommelier-ai/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   └── prompts/         # AI system prompts
│   ├── migrations/          # Database migrations
│   ├── tests/              
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # API services
│   │   └── context/         # React context
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

## 🔌 API Endpoints

### Autenticazione
- `POST /api/auth/register` - Registrazione venue + utente
- `POST /api/auth/login` - Login
- `GET /api/auth/profile` - Profilo utente

### Venues
- `GET /api/venues/:slug` - Info venue (pubblica)
- `PUT /api/venues/:id` - Aggiorna venue
- `GET /api/venues/:id/qrcode` - Ottieni QR code

### Prodotti
- `GET /api/products/venue/:id` - Lista prodotti
- `POST /api/products` - Crea prodotto
- `PUT /api/products/:id` - Aggiorna prodotto
- `DELETE /api/products/:id` - Elimina prodotto

### Chat B2C (Clienti)
- `POST /api/chat/sessions` - Crea sessione
- `POST /api/chat/messages` - Invia messaggio
- `GET /api/chat/sessions/:token/history` - Storico

### Chat B2B (Ristoratori)
- `POST /api/b2b/chat` - Invia messaggio
- `GET /api/b2b/chat/history` - Storico
- `GET /api/b2b/analytics/dashboard` - Statistiche

## 🗄️ Database Schema

Il database utilizza **PostgreSQL** tramite **Supabase**. Lo schema è definito in `backend/schema.sql`.

### Entità Principali
- **Venues** - Ristoranti/locali
- **Users** - Utenti (proprietari/staff)
- **Products** - Vini/prodotti
- **Sessions** - Sessioni chat
- **Messages** - Messaggi nelle sessioni
- **Menu Items** - Piatti del menu per abbinamenti

### Setup Database

1. Crea un progetto su Supabase
2. Copia la Connection String dalla dashboard (Settings → Database)
3. Imposta `DATABASE_URL` nel file `.env`
4. Esegui `backend/schema.sql` nel SQL Editor di Supabase per creare le tabelle

## 🤖 AI Integration

### OpenAI GPT
- Modello:(configurabile per fine-tuned model)
- System prompts dinamici per B2B e B2C
- Context management per conversazioni coerenti

### Qdrant Vector Search
- Embeddings con `text-embedding-3-small`
- Ricerca semantica per suggerimenti vini
- Filtri per venue, tipo, prezzo, disponibilità

## 🎨 Design System

### Colori
- **Burgundy** `#722F37` - Colore primario
- **Gold** `#D4AF37` - Accenti
- **Cream** `#FFF8E7` - Background

### Font
- **Playfair Display** - Headings
- **Lato** - Body text

## 📱 Funzionalità

### Per i Ristoratori (B2B)
- ✅ Dashboard con analytics
- ✅ Gestione carta vini (CRUD)
- ✅ Assistente AI per selezione vini
- ✅ Generazione QR code
- ✅ Onboarding guidato

### Per i Clienti (B2C)
- ✅ Accesso via QR code (no registrazione)
- ✅ Chat con sommelier AI
- ✅ Suggerimenti personalizzati
- ✅ Visualizzazione carta vini

## 🔐 Sicurezza

- JWT per autenticazione
- Password hashing con bcrypt
- CORS configurato
- Rate limiting (da implementare)

## 📊 Analytics

- Conversazioni totali
- Vini più richiesti
- Messaggi medi per sessione
- Feedback clienti

## 🛠️ Tecnologie

### Backend
- Python 3.11+
- Flask 3.0
- SQLAlchemy
- OpenAI SDK
- Qdrant Client

### Frontend
- React 18
- Vite 5
- TailwindCSS 3
- Framer Motion
- React Router 6

### Infrastructure
- PostgreSQL (Supabase)
- Qdrant
- Docker

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

Sviluppato con ❤️ e 🍷

