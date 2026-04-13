DROP TABLE IF EXISTS layers CASCADE;

CREATE TABLE layers (
    id SERIAL PRIMARY KEY,
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    layer_order INTEGER NOT NULL,
    min_trust_score INTEGER NOT NULL DEFAULT 0,
    max_trust_score INTEGER,
    requirements JSONB,
    initiator_prompt TEXT,
    system_prompt_override TEXT,
    emotional_state VARCHAR(255),
    what_is_revealed TEXT,
    content_plan JSONB,
    type VARCHAR(50),
    photo_prompt TEXT,
    video_prompt TEXT,
    audio_prompt TEXT,
    text_prompt TEXT,
    is_erotic BOOLEAN DEFAULT FALSE,
    media_url VARCHAR(255),
    parent_layer_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(character_id, layer_order)
);
