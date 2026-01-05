-- Create access_tokens table for B2C customer access tokens
-- These tokens are one-time use and time-limited to prevent URL sharing abuse

CREATE TABLE IF NOT EXISTS access_tokens (
    id SERIAL PRIMARY KEY,
    venue_id INTEGER NOT NULL,
    
    -- Token identification
    token VARCHAR(100) NOT NULL UNIQUE,
    
    -- Usage tracking
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP NULL,
    session_id INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    
    -- Foreign Keys
    CONSTRAINT fk_access_tokens_venue FOREIGN KEY (venue_id) 
        REFERENCES venues(id) ON DELETE CASCADE,
    CONSTRAINT fk_access_tokens_session FOREIGN KEY (session_id) 
        REFERENCES sessions(id) ON DELETE SET NULL
);

-- Indexes for access_tokens
CREATE INDEX IF NOT EXISTS idx_access_tokens_token ON access_tokens(token);
CREATE INDEX IF NOT EXISTS idx_access_tokens_venue_id ON access_tokens(venue_id);
CREATE INDEX IF NOT EXISTS idx_access_tokens_is_used ON access_tokens(is_used);
CREATE INDEX IF NOT EXISTS idx_access_tokens_expires_at ON access_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_access_tokens_created_at ON access_tokens(created_at);

