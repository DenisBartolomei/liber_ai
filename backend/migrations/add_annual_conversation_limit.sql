-- Add annual_conversation_limit column to venues table
ALTER TABLE venues ADD COLUMN IF NOT EXISTS annual_conversation_limit INTEGER DEFAULT NULL;

-- Set demo venue (ID 2) to 20000 conversations
UPDATE venues SET annual_conversation_limit = 20000 WHERE id = 2;

