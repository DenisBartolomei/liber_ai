-- Migration: Add precomputed_ranking_json column to sessions table
-- Purpose: Store precomputed wine rankings JSON separately from context for reliability
-- Date: 2026-01-17

-- Add the new column (nullable, JSON type)
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS precomputed_ranking_json JSONB;

-- Add a comment for documentation
COMMENT ON COLUMN sessions.precomputed_ranking_json IS 'Precomputed wine rankings JSON from fine-tuned model. Structure: {wines: [...], journeys: [...]}';

