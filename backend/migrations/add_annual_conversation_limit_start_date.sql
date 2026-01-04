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

