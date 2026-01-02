# Fix: Eseguire Migration per annual_conversation_limit

## Problema
Il modello Python include la colonna `annual_conversation_limit`, ma questa non esiste ancora nel database Supabase. Questo causa errori quando SQLAlchemy cerca di caricare i dati.

## Soluzione

### Opzione 1: Eseguire SQL direttamente su Supabase (Raccomandato)

1. Vai alla Dashboard di Supabase: https://app.supabase.com
2. Seleziona il tuo progetto
3. Vai su **SQL Editor** (menu laterale)
4. Esegui questo SQL:

```sql
-- Aggiungi colonna annual_conversation_limit se non esiste
ALTER TABLE venues 
ADD COLUMN IF NOT EXISTS annual_conversation_limit INTEGER DEFAULT NULL;

-- Imposta limite per venue demo (ID 2)
UPDATE venues 
SET annual_conversation_limit = 20000 
WHERE id = 2 AND annual_conversation_limit IS NULL;
```

5. Clicca su **Run** o premi `Ctrl+Enter` (o `Cmd+Enter` su Mac)

### Opzione 2: Usare psql (se hai accesso da terminale)

Se hai installato `psql` e conosci le credenziali del database:

```bash
psql "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres" -f backend/migrations/add_annual_conversation_limit.sql
```

Sostituisci:
- `[PASSWORD]` con la password del database
- `[HOST]` con l'host di Supabase (es. `db.xxxxx.supabase.co`)

### Verifica

Dopo aver eseguito la migration, verifica che la colonna esista:

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'venues' 
  AND column_name = 'annual_conversation_limit';
```

Dovresti vedere una riga con:
- `column_name`: `annual_conversation_limit`
- `data_type`: `integer`
- `is_nullable`: `YES`

## Nota Importante

Se hai abilitato RLS (Row Level Security) prima di eseguire questa migration, potrebbe essere necessario verificare che le policies permettano l'accesso. Tuttavia, se usi il service role (postgres), le policies dovrebbero funzionare.

