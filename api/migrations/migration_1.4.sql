CREATE TABLE IF NOT EXISTS reference_photos (
    id SERIAL PRIMARY KEY,
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    prompt TEXT NOT NULL,
    media_url VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(character_id, description)
);
