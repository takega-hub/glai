-- Add notifications_enabled column to control push notification preferences
ALTER TABLE user_character_state ADD COLUMN notifications_enabled BOOLEAN DEFAULT true;

-- Create index for faster queries on notification preferences
CREATE INDEX IF NOT EXISTS idx_user_character_state_notifications ON user_character_state(notifications_enabled) WHERE notifications_enabled = true;
