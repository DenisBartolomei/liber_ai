# Istruzioni per eseguire la migration: annual_conversation_limit_start_date

## Problema
La colonna `annual_conversation_limit_start_date` non esiste nel database, causando errori quando l'applicazione cerca di accedere ai dati del venue.

## Soluzione: Eseguire la migration manualmente

### Opzione 1: Tramite Supabase Dashboard (Raccomandato)

1. Accedi al tuo progetto Supabase: https://supabase.com/dashboard
2. Vai su **SQL Editor** (icona del terminale nella sidebar sinistra)
3. Crea una nuova query
4. Copia e incolla il contenuto del file `backend/migrations/add_annual_conversation_limit_start_date.sql`:

```sql
-- Add annual_conversation_limit_start_date column to venues table
-- This tracks when the annual conversation limit period started
-- The limit renews exactly 1 year after this date

ALTER TABLE venues ADD COLUMN IF NOT EXISTS annual_conversation_limit_start_date TIMESTAMP DEFAULT NULL;

-- For existing venues with a limit set, initialize the start date to their creation date
-- This ensures they have a valid start date for the limit period
UPDATE venues 
SET annual_conversation_limit_start_date = created_at 
WHERE annual_conversation_limit IS NOT NULL 
  AND annual_conversation_limit_start_date IS NULL;

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_venues_conversation_limit_start_date 
ON venues(annual_conversation_limit_start_date) 
WHERE annual_conversation_limit_start_date IS NOT NULL;
```

5. Clicca su **Run** (o premi Ctrl+Enter)
6. Verifica che la query sia stata eseguita con successo

### Opzione 2: Tramite psql (Command Line)

Se hai accesso al database tramite psql:

```bash
psql "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres" -f backend/migrations/add_annual_conversation_limit_start_date.sql
```

Sostituisci:
- `[PASSWORD]` con la password del database
- `[HOST]` con l'host del database Supabase

### Verifica

Dopo aver eseguito la migration, verifica che la colonna esista:

```sql
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'venues' 
  AND column_name = 'annual_conversation_limit_start_date';
```

Dovresti vedere:
- `column_name`: `annual_conversation_limit_start_date`
- `data_type`: `timestamp without time zone`
- `is_nullable`: `YES`

## Note

- La migration è **idempotente** (può essere eseguita più volte senza problemi grazie a `IF NOT EXISTS`)
- Per i venue esistenti con un limite già impostato, la data di inizio viene inizializzata alla loro data di creazione
- Dopo aver eseguito la migration, l'applicazione dovrebbe funzionare correttamente

