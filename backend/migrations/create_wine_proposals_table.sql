-- ===========================================
-- Create wine_proposals table for analytics
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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_wine_proposals_session ON wine_proposals(session_id);
CREATE INDEX IF NOT EXISTS idx_wine_proposals_product ON wine_proposals(product_id);
CREATE INDEX IF NOT EXISTS idx_wine_proposals_group ON wine_proposals(proposal_group_id);
CREATE INDEX IF NOT EXISTS idx_wine_proposals_rank ON wine_proposals(proposal_rank);
CREATE INDEX IF NOT EXISTS idx_wine_proposals_selected ON wine_proposals(is_selected);
CREATE INDEX IF NOT EXISTS idx_wine_proposals_created ON wine_proposals(created_at);
CREATE INDEX IF NOT EXISTS idx_wine_proposals_message ON wine_proposals(message_id) WHERE message_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_wine_proposals_journey ON wine_proposals(journey_id) WHERE journey_id IS NOT NULL;

