-- Add must_change_password to users table (onboarding: force change on first login)
ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN users.must_change_password IS 'When true, user must change password on next login (e.g. after onboarding)';
