-- Migration: Add session rate limiting for B2C anti-abuse
-- Date: 2026-01-31
-- Description:
--   1. Remove WiFi verification fields from venues (no longer used)
--   2. Add session rate limiting configuration to venues
--   3. Add rate limiting fields to sessions for B2C anti-abuse

-- ============================================
-- PART 1: Remove WiFi verification from venues
-- ============================================

-- Remove WiFi fields (backwards migration data loss is acceptable - feature removed)
ALTER TABLE venues DROP COLUMN IF EXISTS wifi_ip_address;
ALTER TABLE venues DROP COLUMN IF EXISTS wifi_ip_range;
ALTER TABLE venues DROP COLUMN IF EXISTS wifi_verification_enabled;


-- ============================================
-- PART 2: Add session rate limiting config to venues
-- ============================================

-- Session duration in minutes (default 45)
ALTER TABLE venues ADD COLUMN IF NOT EXISTS session_duration_minutes INTEGER DEFAULT 45;

-- Max AI requests per session (default 15)
ALTER TABLE venues ADD COLUMN IF NOT EXISTS session_max_requests INTEGER DEFAULT 15;


-- ============================================
-- PART 3: Add rate limiting fields to sessions
-- ============================================

-- Session expiration timestamp
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP;

-- Max requests allowed for this session
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS max_requests INTEGER DEFAULT 15;

-- AI request counter (separate from message_count)
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS request_count INTEGER DEFAULT 0;

-- List of IP addresses that used this session (JSON array)
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS ip_addresses JSONB DEFAULT '[]'::jsonb;

-- Add index for efficient expiration checks
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);


-- ============================================
-- VERIFICATION
-- ============================================

-- Verify venues columns
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'venues'
AND column_name IN ('session_duration_minutes', 'session_max_requests');

-- Verify sessions columns
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'sessions'
AND column_name IN ('expires_at', 'max_requests', 'request_count', 'ip_addresses');

-- Confirm WiFi columns removed from venues
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'venues'
AND column_name LIKE 'wifi%';
