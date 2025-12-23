-- ===========================================
-- LIBER - Database Schema
-- PostgreSQL (Supabase)
-- ===========================================

-- Note: Supabase creates the database automatically, so no CREATE DATABASE needed

-- ===========================================
-- FUNCTION: Update updated_at timestamp
-- ===========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ===========================================
-- FUNCTION: Calculate product margin
-- ===========================================
CREATE OR REPLACE FUNCTION calculate_product_margin()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.price IS NOT NULL AND NEW.cost_price IS NOT NULL THEN
        NEW.margin = GREATEST(0, NEW.price - NEW.cost_price);
    ELSE
        NEW.margin = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- VENUES TABLE
-- ===========================================
CREATE TABLE IF NOT EXISTS venues (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    
    -- Restaurant characteristics
    cuisine_type VARCHAR(100),
    menu_style JSONB,
    preferences JSONB,
    target_audience JSONB,
    
    -- QR Code and branding
    qr_code_url VARCHAR(500),
    logo_url VARCHAR(500),
    primary_color VARCHAR(7) DEFAULT '#722F37',
    
    -- AI Customization
    welcome_message TEXT,
    sommelier_style VARCHAR(50) DEFAULT 'professional',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_onboarded BOOLEAN DEFAULT FALSE,
    
    -- Subscription
    plan VARCHAR(50) DEFAULT 'trial',
    trial_ends_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create trigger for updated_at on venues
CREATE TRIGGER update_venues_updated_at BEFORE UPDATE ON venues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Indexes for venues
CREATE INDEX IF NOT EXISTS idx_venues_slug ON venues(slug);
CREATE INDEX IF NOT EXISTS idx_venues_is_active ON venues(is_active);
CREATE INDEX IF NOT EXISTS idx_venues_created_at ON venues(created_at);

-- ===========================================
-- USERS TABLE
-- ===========================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    venue_id INTEGER NOT NULL,
    
    -- Authentication
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Profile
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    
    -- Role and Permissions
    role VARCHAR(50) DEFAULT 'owner',
    permissions JSONB,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- Email verification
    verification_token VARCHAR(255),
    verification_sent_at TIMESTAMP,
    
    -- Password reset
    reset_token VARCHAR(255),
    reset_token_expires_at TIMESTAMP,
    
    -- Login tracking
    last_login_at TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_users_venue FOREIGN KEY (venue_id) 
        REFERENCES venues(id) ON DELETE CASCADE
);

-- Create trigger for updated_at on users
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Indexes for users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_venue_id ON users(venue_id);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- ===========================================
-- PRODUCTS TABLE
-- ===========================================
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    venue_id INTEGER NOT NULL,
    
    -- Basic Info
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    
    -- Wine Details
    region VARCHAR(255),
    country VARCHAR(100) DEFAULT 'Italia',
    appellation VARCHAR(255),
    grape_variety VARCHAR(255),
    vintage INTEGER,
    
    -- Producer Info
    producer VARCHAR(255),
    winemaker VARCHAR(255),
    
    -- Characteristics
    alcohol_content REAL,
    body VARCHAR(50),
    sweetness VARCHAR(50),
    tannin_level VARCHAR(50),
    acidity_level VARCHAR(50),
    
    -- Pricing
    price NUMERIC(10, 2) NOT NULL,
    price_glass NUMERIC(10, 2),
    cost_price NUMERIC(10, 2),
    margin NUMERIC(10, 2),  -- Calculated margin (price - cost_price)
    
    -- Descriptions
    description TEXT,
    tasting_notes TEXT,
    aroma_profile JSONB,
    
    -- Food Pairings
    food_pairings JSONB,
    pairing_notes TEXT,
    
    -- Service
    serving_temperature VARCHAR(50),
    decanting_time VARCHAR(50),
    glass_type VARCHAR(100),
    
    -- Vector DB
    qdrant_id VARCHAR(100) UNIQUE,
    embedding_updated_at TIMESTAMP,
    
    -- Inventory
    is_available BOOLEAN DEFAULT TRUE,
    stock_quantity INTEGER,
    
    -- Metadata
    image_url VARCHAR(500),
    external_id VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_products_venue FOREIGN KEY (venue_id) 
        REFERENCES venues(id) ON DELETE CASCADE
);

-- Create trigger for updated_at on products
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create trigger to auto-calculate margin when price or cost_price changes
CREATE TRIGGER trigger_calculate_product_margin
    BEFORE INSERT OR UPDATE OF price, cost_price ON products
    FOR EACH ROW
    EXECUTE FUNCTION calculate_product_margin();

-- Indexes for products
CREATE INDEX IF NOT EXISTS idx_products_venue_id ON products(venue_id);
CREATE INDEX IF NOT EXISTS idx_products_type ON products(type);
CREATE INDEX IF NOT EXISTS idx_products_region ON products(region);
CREATE INDEX IF NOT EXISTS idx_products_is_available ON products(is_available);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_qdrant_id ON products(qdrant_id);
CREATE INDEX IF NOT EXISTS idx_products_venue_type ON products(venue_id, type);

-- ===========================================
-- SESSIONS TABLE
-- ===========================================
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    venue_id INTEGER NOT NULL,
    user_id INTEGER,
    
    -- Session identification
    session_token VARCHAR(100) NOT NULL UNIQUE,
    
    -- Session type
    mode VARCHAR(20) NOT NULL,
    
    -- Context for AI
    context JSONB,
    
    -- Session metadata
    device_type VARCHAR(50),
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    
    -- Analytics
    message_count INTEGER DEFAULT 0,
    products_recommended JSONB,
    products_selected JSONB,
    products_sold JSONB,  -- Products sold with timestamp: [{"product_id": 1, "sold_at": "2024-01-01T12:00:00"}, ...]
    
    -- Budget and target tracking
    budget_initial NUMERIC(10, 2),  -- Initial budget declared by customer (per bottle)
    num_bottiglie_target INTEGER,  -- Target number of bottles for the journey
    
    -- Satisfaction/Feedback
    rating INTEGER,
    feedback TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_sessions_venue FOREIGN KEY (venue_id) 
        REFERENCES venues(id) ON DELETE CASCADE,
    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for sessions
CREATE INDEX IF NOT EXISTS idx_sessions_session_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_venue_id ON sessions(venue_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_mode ON sessions(mode);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_venue_mode ON sessions(venue_id, mode);

-- ===========================================
-- MESSAGES TABLE
-- ===========================================
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    
    -- Message content
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    
    -- AI-specific metadata
    metadata JSONB,
    
    -- Products mentioned
    products_mentioned JSONB,
    
    -- Feedback
    was_helpful BOOLEAN,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_messages_session FOREIGN KEY (session_id) 
        REFERENCES sessions(id) ON DELETE CASCADE
);

-- Indexes for messages
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_session_created ON messages(session_id, created_at);

-- ===========================================
-- MENU ITEMS TABLE (Food menu for wine pairing)
-- ===========================================
CREATE TABLE IF NOT EXISTS menu_items (
    id SERIAL PRIMARY KEY,
    venue_id INTEGER NOT NULL,
    
    -- Basic Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Category
    category VARCHAR(100),
    
    -- Pairing attributes
    main_ingredient VARCHAR(100),
    cooking_method VARCHAR(100),
    flavor_profile JSONB,
    
    -- Price
    price NUMERIC(10, 2),
    
    -- Status
    is_available BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_menu_items_venue FOREIGN KEY (venue_id) 
        REFERENCES venues(id) ON DELETE CASCADE
);

-- Create trigger for updated_at on menu_items
CREATE TRIGGER update_menu_items_updated_at BEFORE UPDATE ON menu_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Indexes for menu_items
CREATE INDEX IF NOT EXISTS idx_menu_items_venue_id ON menu_items(venue_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_category ON menu_items(category);
CREATE INDEX IF NOT EXISTS idx_menu_items_is_available ON menu_items(is_available);

-- ===========================================
-- WINE PROPOSALS TABLE (Analytics)
-- ===========================================
CREATE TABLE IF NOT EXISTS wine_proposals (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    message_id INTEGER,
    product_id INTEGER NOT NULL,
    proposal_group_id VARCHAR(100),
    proposal_rank INTEGER NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    margin NUMERIC(10, 2),
    proposal_reason TEXT,
    mode VARCHAR(20),
    journey_id INTEGER,
    is_selected BOOLEAN DEFAULT FALSE,
    selected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_wine_proposals_session FOREIGN KEY (session_id) 
        REFERENCES sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_wine_proposals_product FOREIGN KEY (product_id) 
        REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT fk_wine_proposals_message FOREIGN KEY (message_id) 
        REFERENCES messages(id) ON DELETE SET NULL
);

-- Indexes for wine_proposals
CREATE INDEX IF NOT EXISTS idx_wine_proposals_session ON wine_proposals(session_id);
CREATE INDEX IF NOT EXISTS idx_wine_proposals_product ON wine_proposals(product_id);
CREATE INDEX IF NOT EXISTS idx_wine_proposals_group ON wine_proposals(proposal_group_id);
CREATE INDEX IF NOT EXISTS idx_wine_proposals_rank ON wine_proposals(proposal_rank);
CREATE INDEX IF NOT EXISTS idx_wine_proposals_selected ON wine_proposals(is_selected);
CREATE INDEX IF NOT EXISTS idx_wine_proposals_created ON wine_proposals(created_at);
CREATE INDEX IF NOT EXISTS idx_wine_proposals_message ON wine_proposals(message_id) WHERE message_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_wine_proposals_journey ON wine_proposals(journey_id) WHERE journey_id IS NOT NULL;

-- ===========================================
-- SAMPLE DATA FOR TESTING
-- ===========================================

-- Insert a demo venue
INSERT INTO venues (name, slug, description, cuisine_type, menu_style, is_active, is_onboarded, welcome_message)
VALUES (
    'Ristorante Da Mario',
    'ristorante-da-mario-demo123',
    'Ristorante italiano tradizionale nel cuore della città',
    'italian',
    '{"style": "classic", "focus": ["italian", "regional"]}'::jsonb,
    TRUE,
    TRUE,
    'Benvenuto da Mario! Sono il sommelier virtuale e sono qui per aiutarti a scegliere il vino perfetto per la tua serata. Dimmi cosa hai in mente!'
)
ON CONFLICT DO NOTHING;

-- Insert a demo user
INSERT INTO users (venue_id, email, password_hash, first_name, last_name, role, is_active, is_verified)
VALUES (
    1,
    'demo@liber.ai',
    -- Password: 'demo123' (bcrypt hash)
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4tTTvJrDgU7q0Dqu',
    'Mario',
    'Rossi',
    'owner',
    TRUE,
    TRUE
)
ON CONFLICT DO NOTHING;

-- Insert sample products
INSERT INTO products (venue_id, name, type, region, grape_variety, vintage, price, description, tasting_notes, food_pairings, is_available)
VALUES 
(1, 'Brunello di Montalcino DOCG 2018', 'red', 'Toscana', 'Sangiovese', 2018, 85.00, 
 'Un Brunello elegante e strutturato, espressione autentica del terroir di Montalcino.',
 'Note di ciliegia matura, tabacco, cuoio e spezie dolci. Tannini setosi e finale persistente.',
 '["tagliata di manzo", "bistecca fiorentina", "cinghiale", "pecorino stagionato"]'::jsonb, TRUE),

(1, 'Barolo DOCG 2017', 'red', 'Piemonte', 'Nebbiolo', 2017, 120.00,
 'Barolo classico dalle Langhe, potente ed elegante con grande potenziale di invecchiamento.',
 'Aromi di rosa, catrame, tartufo e frutti rossi maturi. Struttura tannica importante, grande complessità.',
 '["brasato", "tartufo", "risotto ai funghi", "formaggi erborinati"]'::jsonb, TRUE),

(1, 'Chianti Classico Riserva DOCG 2019', 'red', 'Toscana', 'Sangiovese', 2019, 45.00,
 'Chianti Classico Riserva dal cuore del Gallo Nero, equilibrato e versatile.',
 'Note di amarena, viola, spezie e sottobosco. Medio corpo con acidità vivace.',
 '["ribollita", "pici al ragù", "arista di maiale", "pecorino toscano"]'::jsonb, TRUE),

(1, 'Amarone della Valpolicella DOCG 2016', 'red', 'Veneto', 'Corvina, Rondinella, Molinara', 2016, 95.00,
 'Amarone potente e vellutato, prodotto con uve appassite secondo tradizione.',
 'Frutta secca, cioccolato, caffè e spezie orientali. Caldo, avvolgente e di grande struttura.',
 '["brasato all amarone", "selvaggina", "formaggi stagionati", "cioccolato fondente"]'::jsonb, TRUE),

(1, 'Gavi di Gavi DOCG 2022', 'white', 'Piemonte', 'Cortese', 2022, 35.00,
 'Gavi elegante e minerale, perfetto aperitivo o compagno di piatti di pesce.',
 'Note di agrumi, mela verde, mandorla e pietra focaia. Fresco, sapido e persistente.',
 '["crudo di pesce", "frittura di paranza", "vitello tonnato", "antipasti di mare"]'::jsonb, TRUE),

(1, 'Vermentino di Sardegna DOC 2023', 'white', 'Sardegna', 'Vermentino', 2023, 28.00,
 'Vermentino aromatico e sapido, espressione del mare e del sole sardo.',
 'Profumi di macchia mediterranea, agrumi e fiori bianchi. Fresco con finale ammandorlato.',
 '["bottarga", "fregola ai frutti di mare", "ostriche", "pesce alla griglia"]'::jsonb, TRUE),

(1, 'Franciacorta Brut DOCG', 'sparkling', 'Lombardia', 'Chardonnay, Pinot Nero', 2020, 55.00,
 'Metodo classico italiano di grande eleganza, alternativa raffinata allo Champagne.',
 'Perlage fine e persistente. Note di agrumi, brioche e nocciola. Cremoso e armonico.',
 '["aperitivo", "frutti di mare", "risotto alla milanese", "formaggi freschi"]'::jsonb, TRUE),

(1, 'Prosecco Superiore DOCG Valdobbiadene', 'sparkling', 'Veneto', 'Glera', 2023, 25.00,
 'Prosecco vivace e fruttato dalle colline di Valdobbiadene.',
 'Bollicine fini con note di mela verde, pera e fiori di acacia. Fresco e piacevolmente dolce.',
 '["aperitivo", "antipasti", "pizza", "dolci secchi"]'::jsonb, TRUE)
ON CONFLICT DO NOTHING;

-- Insert sample menu items (food)
INSERT INTO menu_items (venue_id, name, description, category, main_ingredient, cooking_method, flavor_profile, price, is_available)
VALUES
(1, 'Bruschetta al pomodoro', 'Pane tostato con pomodori freschi e basilico', 'antipasto', 'verdure', 'al_forno', '["leggero", "delicato"]'::jsonb, 8.00, TRUE),
(1, 'Carpaccio di manzo', 'Fettine sottili di manzo crudo con rucola e grana', 'antipasto', 'carne_rossa', 'crudo', '["delicato", "umami"]'::jsonb, 14.00, TRUE),
(1, 'Burrata con pomodorini', 'Burrata fresca con pomodorini pachino e basilico', 'antipasto', 'formaggio', 'crudo', '["grasso", "delicato"]'::jsonb, 12.00, TRUE),
(1, 'Spaghetti alle vongole', 'Spaghetti con vongole veraci, aglio e prezzemolo', 'primo', 'pesce', 'saltato', '["leggero", "umami"]'::jsonb, 16.00, TRUE),
(1, 'Risotto ai funghi porcini', 'Risotto cremoso con porcini freschi', 'primo', 'riso', 'brasato', '["umami", "delicato"]'::jsonb, 18.00, TRUE),
(1, 'Pappardelle al cinghiale', 'Pappardelle con ragù di cinghiale', 'primo', 'carne_rossa', 'brasato', '["grasso", "speziato"]'::jsonb, 15.00, TRUE),
(1, 'Tagliata di manzo', 'Tagliata con rucola, pomodorini e grana', 'secondo', 'carne_rossa', 'grigliato', '["umami", "grasso"]'::jsonb, 24.00, TRUE),
(1, 'Branzino al forno', 'Branzino al forno con patate e olive', 'secondo', 'pesce', 'al_forno', '["leggero", "delicato"]'::jsonb, 22.00, TRUE),
(1, 'Filetto di maiale', 'Filetto di maiale con salsa al vino rosso', 'secondo', 'carne_bianca', 'arrosto', '["speziato", "grasso"]'::jsonb, 20.00, TRUE),
(1, 'Tiramisù', 'Classico tiramisù con mascarpone e caffè', 'dolce', NULL, NULL, '["dolce", "grasso"]'::jsonb, 8.00, TRUE),
(1, 'Panna cotta', 'Panna cotta con frutti di bosco', 'dolce', NULL, NULL, '["dolce", "delicato"]'::jsonb, 7.00, TRUE)
ON CONFLICT DO NOTHING;

-- Display confirmation
SELECT 'Database schema created successfully!' AS status;
SELECT COUNT(*) AS venues_count FROM venues;
SELECT COUNT(*) AS users_count FROM users;
SELECT COUNT(*) AS products_count FROM products;
SELECT COUNT(*) AS menu_items_count FROM menu_items;
