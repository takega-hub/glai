ALTER TABLE users DROP COLUMN trust_score;

CREATE TABLE IF NOT EXISTS user_character_state (
    id SERIAL PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    character_id uuid NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    trust_score INTEGER NOT NULL DEFAULT 0,
    current_layer INTEGER NOT NULL DEFAULT 0,
    conversation_history JSONB,
    last_message_date TIMESTAMP,
    UNIQUE(user_id, character_id)
);