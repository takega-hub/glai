-- Add last_viewed_at column to track when user last viewed a character chat
ALTER TABLE user_character_state ADD COLUMN last_viewed_at TIMESTAMP DEFAULT NOW();

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_user_character_state_last_viewed_at ON user_character_state(last_viewed_at);
