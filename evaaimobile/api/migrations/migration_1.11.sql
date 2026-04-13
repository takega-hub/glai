ALTER TABLE user_character_state
ALTER COLUMN layers_unlocked TYPE JSONB USING layers_unlocked::jsonb,
ALTER COLUMN content_unlocked TYPE JSONB USING content_unlocked::jsonb;