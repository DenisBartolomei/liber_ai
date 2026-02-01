-- ===========================================
-- MIGRAZIONE: Da products a wines + venue_wines
-- ===========================================
-- Questa migrazione rivoluziona la gestione dei vini:
-- - wines: catalogo master globale (un vino esiste una sola volta)
-- - venue_wines: associazione venue-vino con prezzi e disponibilità specifici
--
-- ESEGUIRE IN ORDINE:
-- 1. Fase 1: Creare nuove tabelle
-- 2. Fase 2: Migrare dati (eseguire con attenzione)
-- 3. Fase 3: Aggiornare FK e creare view compatibilità
-- 4. Fase 4: Cleanup (solo dopo aver verificato che tutto funziona)
-- ===========================================

-- ===========================================
-- FASE 1: CREARE NUOVE TABELLE
-- ===========================================

-- Tabella master dei vini (catalogo globale)
CREATE TABLE IF NOT EXISTS wines (
    id SERIAL PRIMARY KEY,

    -- Identificazione
    name VARCHAR(255) NOT NULL,
    producer VARCHAR(255),
    type VARCHAR(50) NOT NULL,  -- red, white, rose, sparkling, dessert, fortified
    category VARCHAR(100),

    -- Provenienza
    region VARCHAR(255),
    country VARCHAR(100) DEFAULT 'Italia',
    appellation VARCHAR(255),  -- DOC, DOCG, IGT, etc.

    -- Caratteristiche base
    grape_variety VARCHAR(255),
    alcohol_content REAL,

    -- Profilo sensoriale
    body INTEGER CHECK (body IS NULL OR (body >= 1 AND body <= 10)),
    sweetness VARCHAR(50),
    tannin_level INTEGER CHECK (tannin_level IS NULL OR (tannin_level >= 1 AND tannin_level <= 10)),
    acidity_level INTEGER CHECK (acidity_level IS NULL OR (acidity_level >= 1 AND acidity_level <= 10)),
    color VARCHAR(255),
    aromas TEXT,
    aroma_profile JSONB,

    -- Descrizioni
    description TEXT,
    tasting_notes TEXT,

    -- Abbinamenti
    food_pairings JSONB,
    pairing_notes TEXT,

    -- Servizio
    serving_temperature VARCHAR(50),
    decanting_time VARCHAR(50),
    glass_type VARCHAR(100),

    -- Produttore info
    winemaker VARCHAR(255),

    -- Immagine di riferimento (etichetta generica del vino)
    image_url VARCHAR(500),

    -- Vector DB (per uso futuro)
    qdrant_id VARCHAR(100) UNIQUE,
    embedding_updated_at TIMESTAMP,

    -- Metadati
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger per updated_at su wines
CREATE TRIGGER update_wines_updated_at
    BEFORE UPDATE ON wines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Indici per wines
CREATE INDEX IF NOT EXISTS idx_wines_name ON wines(name);
CREATE INDEX IF NOT EXISTS idx_wines_producer ON wines(producer);
CREATE INDEX IF NOT EXISTS idx_wines_type ON wines(type);
CREATE INDEX IF NOT EXISTS idx_wines_region ON wines(region);
CREATE INDEX IF NOT EXISTS idx_wines_country ON wines(country);
CREATE INDEX IF NOT EXISTS idx_wines_grape ON wines(grape_variety);
CREATE INDEX IF NOT EXISTS idx_wines_qdrant_id ON wines(qdrant_id);
CREATE INDEX IF NOT EXISTS idx_wines_name_producer ON wines(name, producer);
CREATE INDEX IF NOT EXISTS idx_wines_name_type_region ON wines(name, type, region);

-- ===========================================
-- Tabella associazione venue-vino
-- ===========================================
CREATE TABLE IF NOT EXISTS venue_wines (
    id SERIAL PRIMARY KEY,
    venue_id INTEGER NOT NULL,
    wine_id INTEGER NOT NULL,

    -- Dati specifici del venue
    vintage INTEGER,  -- L'annata può variare per venue

    -- Prezzi (specifici per locale)
    price NUMERIC(10,2) NOT NULL,
    price_glass NUMERIC(10,2),
    cost_price NUMERIC(10,2),
    margin NUMERIC(10,2),

    -- Disponibilità
    is_available BOOLEAN DEFAULT TRUE,
    stock_quantity INTEGER,

    -- Immagine specifica (es. foto dell'etichetta del ristorante)
    image_url VARCHAR(500),

    -- Tracking
    external_id VARCHAR(100),  -- ID dal sistema gestionale del cliente
    notes TEXT,  -- Note specifiche del ristorante

    -- Riferimento al vecchio product_id (per migrazione)
    legacy_product_id INTEGER,

    -- Metadati
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Keys
    CONSTRAINT fk_venue_wines_venue FOREIGN KEY (venue_id)
        REFERENCES venues(id) ON DELETE CASCADE,
    CONSTRAINT fk_venue_wines_wine FOREIGN KEY (wine_id)
        REFERENCES wines(id) ON DELETE CASCADE,

    -- Un vino può apparire una sola volta per venue/annata
    -- (NULL vintage è trattato come distinto)
    CONSTRAINT unique_venue_wine_vintage UNIQUE (venue_id, wine_id, vintage)
);

-- Trigger per updated_at su venue_wines
CREATE TRIGGER update_venue_wines_updated_at
    BEFORE UPDATE ON venue_wines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger per calcolo margine su venue_wines
CREATE TRIGGER trigger_calculate_venue_wine_margin
    BEFORE INSERT OR UPDATE OF price, cost_price ON venue_wines
    FOR EACH ROW EXECUTE FUNCTION calculate_product_margin();

-- Indici per venue_wines
CREATE INDEX IF NOT EXISTS idx_venue_wines_venue_id ON venue_wines(venue_id);
CREATE INDEX IF NOT EXISTS idx_venue_wines_wine_id ON venue_wines(wine_id);
CREATE INDEX IF NOT EXISTS idx_venue_wines_available ON venue_wines(is_available);
CREATE INDEX IF NOT EXISTS idx_venue_wines_price ON venue_wines(price);
CREATE INDEX IF NOT EXISTS idx_venue_wines_venue_available ON venue_wines(venue_id, is_available);
CREATE INDEX IF NOT EXISTS idx_venue_wines_legacy ON venue_wines(legacy_product_id);

-- ===========================================
-- FASE 2: MIGRARE DATI
-- ===========================================
-- ATTENZIONE: Eseguire questa sezione con cura!
-- Prima della migrazione, fare un backup del database.

-- Step 2.1: Popolare wines da products (con deduplicazione base)
-- Ogni combinazione unica di (name, producer, type, region, grape_variety) diventa un wine
INSERT INTO wines (
    name, producer, type, category,
    region, country, appellation, grape_variety,
    alcohol_content, body, sweetness, tannin_level, acidity_level,
    color, aromas, aroma_profile,
    description, tasting_notes,
    food_pairings, pairing_notes,
    serving_temperature, decanting_time, glass_type,
    winemaker, image_url,
    qdrant_id, embedding_updated_at,
    created_at
)
SELECT DISTINCT ON (name, COALESCE(producer, ''), type, COALESCE(region, ''), COALESCE(grape_variety, ''))
    name,
    producer,
    type,
    category,
    region,
    country,
    appellation,
    grape_variety,
    alcohol_content,
    body,
    sweetness,
    tannin_level,
    acidity_level,
    color,
    aromas,
    aroma_profile,
    description,
    tasting_notes,
    food_pairings,
    pairing_notes,
    serving_temperature,
    decanting_time,
    glass_type,
    winemaker,
    image_url,
    NULL AS qdrant_id,  -- Reset qdrant_id per il nuovo schema
    NULL AS embedding_updated_at,
    MIN(created_at) AS created_at
FROM products
GROUP BY
    name, producer, type, category,
    region, country, appellation, grape_variety,
    alcohol_content, body, sweetness, tannin_level, acidity_level,
    color, aromas, aroma_profile,
    description, tasting_notes,
    food_pairings, pairing_notes,
    serving_temperature, decanting_time, glass_type,
    winemaker, image_url
ORDER BY name, COALESCE(producer, ''), type, COALESCE(region, ''), COALESCE(grape_variety, ''), MIN(created_at);

-- Step 2.2: Popolare venue_wines collegando ogni product al wine corrispondente
INSERT INTO venue_wines (
    venue_id, wine_id, vintage,
    price, price_glass, cost_price, margin,
    is_available, stock_quantity,
    image_url, external_id,
    legacy_product_id,
    created_at
)
SELECT
    p.venue_id,
    w.id AS wine_id,
    p.vintage,
    p.price,
    p.price_glass,
    p.cost_price,
    p.margin,
    COALESCE(p.is_available, TRUE),
    p.stock_quantity,
    p.image_url,
    p.external_id,
    p.id AS legacy_product_id,
    p.created_at
FROM products p
JOIN wines w ON
    p.name = w.name
    AND COALESCE(p.producer, '') = COALESCE(w.producer, '')
    AND p.type = w.type
    AND COALESCE(p.region, '') = COALESCE(w.region, '')
    AND COALESCE(p.grape_variety, '') = COALESCE(w.grape_variety, '');

-- ===========================================
-- FASE 3: AGGIORNARE FOREIGN KEYS
-- ===========================================

-- Step 3.1: Aggiungere colonna venue_wine_id a wine_proposals
ALTER TABLE wine_proposals
    ADD COLUMN IF NOT EXISTS venue_wine_id INTEGER;

-- Step 3.2: Popolare venue_wine_id usando il mapping legacy_product_id
UPDATE wine_proposals wp
SET venue_wine_id = vw.id
FROM venue_wines vw
WHERE vw.legacy_product_id = wp.product_id;

-- Step 3.3: Aggiungere FK constraint (dopo aver popolato i dati)
ALTER TABLE wine_proposals
    ADD CONSTRAINT fk_wine_proposals_venue_wine
    FOREIGN KEY (venue_wine_id) REFERENCES venue_wines(id) ON DELETE CASCADE;

-- Step 3.4: Creare indice su venue_wine_id
CREATE INDEX IF NOT EXISTS idx_wine_proposals_venue_wine ON wine_proposals(venue_wine_id);

-- ===========================================
-- FASE 4: CREARE VIEW DI COMPATIBILITÀ
-- ===========================================
-- Questa view permette al codice legacy di continuare a funzionare
-- mentre migriamo gradualmente

CREATE OR REPLACE VIEW products_compat AS
SELECT
    vw.id,
    vw.venue_id,
    w.name,
    w.type,
    w.category,
    w.region,
    w.country,
    w.appellation,
    w.grape_variety,
    vw.vintage,
    w.producer,
    w.winemaker,
    w.alcohol_content,
    w.body,
    w.sweetness,
    w.tannin_level,
    w.acidity_level,
    w.color,
    w.aromas,
    vw.price,
    vw.price_glass,
    vw.cost_price,
    vw.margin,
    w.description,
    w.tasting_notes,
    w.aroma_profile,
    w.food_pairings,
    w.pairing_notes,
    w.serving_temperature,
    w.decanting_time,
    w.glass_type,
    w.qdrant_id,
    w.embedding_updated_at,
    vw.is_available,
    vw.stock_quantity,
    COALESCE(vw.image_url, w.image_url) AS image_url,
    vw.external_id,
    vw.created_at,
    vw.updated_at,
    -- Campi extra per il nuovo schema
    w.id AS wine_id,
    vw.id AS venue_wine_id
FROM venue_wines vw
JOIN wines w ON vw.wine_id = w.id;

-- ===========================================
-- FASE 5: CLEANUP (ESEGUIRE SOLO DOPO VERIFICA!)
-- ===========================================
-- ATTENZIONE: Eseguire solo dopo aver verificato che:
-- 1. Tutti i dati sono stati migrati correttamente
-- 2. wine_proposals.venue_wine_id è popolato per tutti i record
-- 3. L'applicazione funziona con le nuove tabelle
--
-- Decommentare e eseguire manualmente quando pronti:

-- -- Rendere venue_wine_id NOT NULL (dopo aver verificato che tutti hanno un valore)
-- ALTER TABLE wine_proposals ALTER COLUMN venue_wine_id SET NOT NULL;

-- -- Rimuovere la vecchia FK e colonna product_id
-- ALTER TABLE wine_proposals DROP CONSTRAINT IF EXISTS fk_wine_proposals_product;
-- ALTER TABLE wine_proposals DROP COLUMN IF EXISTS product_id;

-- -- Rinominare products in products_backup
-- ALTER TABLE products RENAME TO products_backup;

-- -- Oppure eliminare products (più rischioso)
-- -- DROP TABLE products CASCADE;

-- ===========================================
-- QUERY DI VERIFICA
-- ===========================================

-- Verifica conteggi dopo migrazione:
-- SELECT 'products' AS table_name, COUNT(*) AS count FROM products
-- UNION ALL
-- SELECT 'wines', COUNT(*) FROM wines
-- UNION ALL
-- SELECT 'venue_wines', COUNT(*) FROM venue_wines;

-- Verifica che tutti i wine_proposals hanno venue_wine_id:
-- SELECT COUNT(*) AS total,
--        COUNT(venue_wine_id) AS with_venue_wine_id,
--        COUNT(*) - COUNT(venue_wine_id) AS missing
-- FROM wine_proposals;

-- Verifica mapping corretto:
-- SELECT wp.id, wp.product_id, wp.venue_wine_id, vw.legacy_product_id
-- FROM wine_proposals wp
-- LEFT JOIN venue_wines vw ON wp.venue_wine_id = vw.id
-- WHERE wp.venue_wine_id IS NULL OR vw.legacy_product_id != wp.product_id
-- LIMIT 10;
