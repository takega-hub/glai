-- Add user_unlocked_content table to track user-specific content access
CREATE TABLE user_unlocked_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    content_id UUID NOT NULL,
    unlocked_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_content UNIQUE (user_id, character_id, content_id)
);

CREATE INDEX idx_user_unlocked_content_user_id ON user_unlocked_content(user_id);
CREATE INDEX idx_user_unlocked_content_character_id ON user_unlocked_content(character_id);