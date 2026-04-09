CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'token_purchase', 'gift_purchase', 'on_demand_generation'
    amount_usd NUMERIC(10, 2),
    token_amount INT,
    related_id UUID, -- id подарка или on-demand генерации
    status VARCHAR(50) DEFAULT 'completed', -- 'pending', 'completed', 'failed'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gifts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    token_cost INT NOT NULL,
    trust_boost INT NOT NULL,
    is_available BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    layer_id INT REFERENCES layers(id) ON DELETE SET NULL, -- Контент может быть не привязан к слою
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    type content_type NOT NULL,
    url VARCHAR(512) NOT NULL,
    thumbnail_url VARCHAR(512),
    description TEXT,
    is_locked BOOLEAN DEFAULT TRUE,
    tags JSONB, -- ["эротика", "сюжетное", "портрет"]
    created_at TIMESTAMPTZ DEFAULT NOW()
);
