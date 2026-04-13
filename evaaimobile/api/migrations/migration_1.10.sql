CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message TEXT,
    response TEXT,
    trust_score_change INTEGER,
    layer_unlocked BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE proactive_messages (
    id SERIAL PRIMARY KEY,
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(255),
    content TEXT,
    trust_score_min INTEGER,
    last_sent TIMESTAMP,
    send_count INTEGER
);
