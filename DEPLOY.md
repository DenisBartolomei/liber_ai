# Deploy Guide - Bacco Sommelier AI su Google Cloud Run

Questa guida descrive come deployare l'applicazione Bacco Sommelier AI su Google Cloud Run.

## Prerequisiti

1. **Account Google Cloud Platform** con billing abilitato
2. **Google Cloud SDK (gcloud CLI)** installato e configurato
3. **Docker** installato (opzionale, Cloud Build può buildare le immagini)
4. **Progetto Google Cloud** creato

## Setup Iniziale

### 1. Installazione Google Cloud SDK

**Windows:**
- Scarica e installa da: https://cloud.google.com/sdk/docs/install
- Oppure usa Chocolatey: `choco install gcloudsdk`

**macOS:**
```bash
brew install google-cloud-sdk
```

**Linux:**
```bash
# Vedi: https://cloud.google.com/sdk/docs/install
```

### 2. Autenticazione

```bash
gcloud auth login
gcloud auth application-default login
```

### 3. Configurazione Progetto

Sostituisci `your-project-id` con l'ID del tuo progetto Google Cloud nel file `deploy.sh`, oppure esporta la variabile:

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west8"  # Opzionale, default è europe-west8 (Milano)
```

### 4. Abilitazione Billing

Assicurati che il billing sia abilitato per il progetto:
- Vai su [Google Cloud Console](https://console.cloud.google.com)
- Seleziona il tuo progetto
- Vai su Billing e associa un account di fatturazione

## Configurazione Variabili d'Ambiente

Puoi passare tutte le variabili d'ambiente inline al comando `deploy.sh`, oppure esportarle prima nel terminale.

**Opzione 1: Passare variabili inline (consigliato):**
```bash
GCP_PROJECT_ID="your-project-id" \
DATABASE_URL="postgresql://..." \
QDRANT_HOST="your-cluster.qdrant.io" \
OPENAI_API_KEY="sk-..." \
... \
./deploy.sh
```

**Opzione 2: Esportare prima:**
```bash
export GCP_PROJECT_ID="your-project-id"
export DATABASE_URL="postgresql://..."
# ... etc
./deploy.sh
```

### Variabili Database

```bash
# Supabase PostgreSQL
export DATABASE_URL="postgresql://user:password@host:6543/dbname"
```

**Nota:** Per Docker/Cloud Run, usa il Connection Pooler (porta 6543) invece della connessione diretta.

### Variabili Qdrant Cloud

```bash
# Qdrant Cloud (crea account su https://cloud.qdrant.io)
export QDRANT_HOST="your-cluster.qdrant.io"
export QDRANT_PORT="6333"
export QDRANT_API_KEY="your-api-key-here"
```

**Setup Qdrant Cloud:**
1. Vai su https://cloud.qdrant.io
2. Crea un account e un cluster
3. Ottieni l'hostname e l'API key dalla dashboard

### Variabili OpenAI

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-5-mini-2025-08-07"
export OPENAI_FINETUNED_MODEL="ft:gpt-4.1-mini-2025-04-14:personal:liber-ai:CoTKB8PZ"
export OPENAI_COMMUNICATION_MODEL="gpt-5-mini-2025-08-07"
export OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
```

### Variabili Supabase Storage

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
export SUPABASE_STORAGE_BUCKET_QRCODES="qrcodes"
export SUPABASE_STORAGE_BUCKET_WINE_LABELS="wine-labels"
```

**Setup Supabase Storage:**
1. Vai su [Supabase Dashboard](https://app.supabase.com)
2. Seleziona il tuo progetto
3. Vai su Settings → API
4. Copia:
   - Project URL → `SUPABASE_URL`
   - Service Role Key (secret) → `SUPABASE_SERVICE_ROLE_KEY`
5. Vai su Storage e crea i bucket:
   - `qrcodes` (privato)
   - `wine-labels` (pubblico)

### Variabili Security

```bash
# Genera chiavi sicure (usa openssl o qualsiasi generatore)
export SECRET_KEY="$(openssl rand -hex 32)"
export JWT_SECRET_KEY="$(openssl rand -hex 32)"
```

**Windows PowerShell:**
```powershell
$env:SECRET_KEY = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
$env:JWT_SECRET_KEY = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

## Deploy

### Opzione 1: Script Deploy (Consigliato)

1. **Rendi eseguibile lo script** (Linux/macOS):
   ```bash
   chmod +x deploy.sh
   ```

2. **Esegui lo script:**
   ```bash
   ./deploy.sh
   ```

   **Windows PowerShell:**
   ```powershell
   bash deploy.sh
   ```

3. **Lo script:**
   - Abilita le API necessarie
   - Builda e deploya il backend
   - Ottiene l'URL del backend
   - Builda il frontend con l'URL del backend
   - Deploya il frontend
   - Aggiorna il backend con l'URL del frontend (per CORS)

### Opzione 2: Deploy Manuale

Se preferisci controllare ogni step:

#### Backend

```bash
# Build
gcloud builds submit --tag gcr.io/${GCP_PROJECT_ID}/liber-backend:latest ./backend

# Deploy
gcloud run deploy liber-backend \
    --image gcr.io/${GCP_PROJECT_ID}/liber-backend:latest \
    --platform managed \
    --region europe-west8 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080 \
    --set-env-vars DATABASE_URL="${DATABASE_URL}",QDRANT_HOST="${QDRANT_HOST}",...
```

#### Frontend

```bash
# Build (con backend URL)
gcloud builds submit \
    --tag gcr.io/${GCP_PROJECT_ID}/liber-frontend:latest \
    --substitutions=_VITE_API_URL=${BACKEND_URL}/api \
    ./frontend

# Deploy
gcloud run deploy liber-frontend \
    --image gcr.io/${GCP_PROJECT_ID}/liber-frontend:latest \
    --platform managed \
    --region europe-west8 \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 5 \
    --min-instances 0 \
    --port 80
```

## Verifica Deploy

Dopo il deploy, dovresti vedere:

```
✅ Deployment completed successfully!

🌐 Service URLs:
   Backend API: https://liber-backend-xxxxx-ew.a.run.app
   Frontend: https://liber-frontend-xxxxx-ew.a.run.app
```

### Test Backend

```bash
curl https://your-backend-url/api/health
```

Dovresti ricevere:
```json
{"status": "healthy", "service": "liber-sommelier-ai"}
```

### Test Frontend

Apri l'URL del frontend nel browser. Dovresti vedere la landing page dell'applicazione.

## Troubleshooting

### Errore: "PROJECT_ID not set"

Assicurati di aver settato `GCP_PROJECT_ID` come variabile d'ambiente o modificato lo script.

### Errore: "Permission denied" su deploy.sh

Linux/macOS:
```bash
chmod +x deploy.sh
```

Windows: Usa `bash deploy.sh` invece di `./deploy.sh`

### Backend non si connette al database

- Verifica che `DATABASE_URL` sia corretto
- Usa il Connection Pooler (porta 6543) per Supabase
- Controlla i log: `gcloud run logs read liber-backend --region=europe-west8`

### Frontend non si connette al backend

- Verifica che `VITE_API_URL` sia stato settato correttamente durante il build
- Controlla la console del browser per errori CORS
- Verifica che `FRONTEND_URL` nel backend corrisponda all'URL del frontend

### Errore Qdrant connection

- Verifica che `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_API_KEY` siano corretti
- Controlla che il cluster Qdrant Cloud sia attivo
- Verifica i log del backend per dettagli sull'errore

### Visualizzare Logs

```bash
# Backend logs
gcloud run logs read liber-backend --region=europe-west8 --limit=50

# Frontend logs
gcloud run logs read liber-frontend --region=europe-west8 --limit=50

# Seguire logs in tempo reale
gcloud run logs tail liber-backend --region=europe-west8
```

## Aggiornare l'Applicazione

Per deployare una nuova versione:

1. **Commit le modifiche** (opzionale, se usi Git)

2. **Riesegui lo script:**
   ```bash
   ./deploy.sh
   ```

Cloud Build ricostruirà le immagini e Cloud Run le aggiornerà automaticamente.

## Costi

Cloud Run è **pay-per-use**:
- **Free tier**: 2 milioni di richieste al mese, 360,000 GB-secondi, 180,000 vCPU-secondi
- **Pricing**: Dopo il free tier, paghi solo per quello che usi
- **Min instances: 0**: I container partono solo quando ricevono richieste

Stima costi per traffico basso/medio: ~$10-50/mese

## Next Steps

1. **Custom Domain**: Configura un dominio personalizzato
2. **SSL**: Cloud Run fornisce SSL automaticamente
3. **Monitoring**: Configura Cloud Monitoring e Alerting
4. **CI/CD**: Setup automatico con Cloud Build triggers da Git
5. **Secrets Management**: Usa Secret Manager invece di env vars per dati sensibili

## Supporto

Per problemi o domande:
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Run Troubleshooting](https://cloud.google.com/run/docs/troubleshooting)

