-- SQL-схема для проекта EVA AI (Modified version)
-- Версия: 1.0 (Modified for built-in UUID support)
-- Дата: 30.03.2025

-- Перечисление для ролей пользователей
CREATE TYPE user_role AS ENUM ('super_admin', 'content_manager', 'character_writer', 'analyst', 'support', 'app_user');

-- Перечисление для статуса персонажа
CREATE TYPE character_status AS ENUM ('active', 'draft', 'archived');

-- Перечисление для типа контента
CREATE TYPE content_type AS ENUM ('photo', 'video', 'audio', 'text');

-- Таблица пользователей (администраторы и пользователи приложения)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'app_user',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active' -- active/blocked
);

-- Таблица для профилей пользователей
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    display_name VARCHAR(100),
    about TEXT,
    avatar_url VARCHAR(512),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица AI-персонажей
CREATE TABLE characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    age INT,
    personality_type VARCHAR(100),
    biography TEXT,
    secret TEXT,
    base_prompt TEXT,
    voice_id VARCHAR(100),
    status character_status DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица слоев доверия
CREATE TABLE layers (
    id SERIAL PRIMARY KEY,
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    layer_order INT NOT NULL, -- Порядок слоя (0, 1, 2...)
    min_trust_score INT NOT NULL,
    max_trust_score INT,
    requirements JSONB, -- { "night_conversations": 2, "min_days": 3 }
    initiator_prompt TEXT, -- Что пишет персонаж при открытии
    system_prompt_override TEXT, -- Изменение системного промпта на этом слое
    is_erotic BOOLEAN DEFAULT FALSE,
    UNIQUE(character_id, layer_order)
);

-- Таблица для медиа-контента
CREATE TABLE content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer_id INT REFERENCES layers(id) ON DELETE SET NULL, -- Контент может быть не привязан к слою
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    type content_type NOT NULL,
    url VARCHAR(512) NOT NULL,
    thumbnail_url VARCHAR(512),
    description TEXT,
    prompt TEXT,
    is_locked BOOLEAN DEFAULT TRUE,
    tags JSONB, -- ["эротика", "сюжетное", "портрет"]
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица для отслеживания состояния пользователя с персонажем
CREATE TABLE user_character_state (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    trust_score INT DEFAULT 0,
    current_layer INT DEFAULT 0,
    layers_unlocked JSONB DEFAULT '[]', -- [{"layer_id": 1, "unlocked_at": "..."}]
    content_unlocked JSONB DEFAULT '[]', -- [{"content_id": "...", "unlocked_at": "..."}]
    tokens_balance INT DEFAULT 0,
    conversation_history JSONB, -- последние N сообщений
    last_message_date TIMESTAMPTZ,
    PRIMARY KEY (user_id, character_id)
);

-- Таблица для истории изменения trust_score
CREATE TABLE trust_score_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    character_id UUID NOT NULL,
    points INT NOT NULL,
    reason VARCHAR(255), -- 'message', 'gift', 'penalty', etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id, character_id) REFERENCES user_character_state(user_id, character_id)
);

-- Таблица для подарков
CREATE TABLE gifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    token_cost INT NOT NULL,
    trust_boost INT NOT NULL,
    is_available BOOLEAN DEFAULT TRUE
);

-- Таблица для транзакций (покупка токенов, подарки)
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'token_purchase', 'gift_purchase', 'on_demand_generation'
    amount_usd NUMERIC(10, 2),
    token_amount INT,
    related_id UUID, -- id подарка или on-demand генерации
    status VARCHAR(50) DEFAULT 'completed', -- 'pending', 'completed', 'failed'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица пакетов токенов
CREATE TABLE token_packages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    token_amount INT NOT NULL,
    price_usd NUMERIC(10, 2) NOT NULL,
    bonus_tokens INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для ускорения запросов
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_character_state_trust_score ON user_character_state(trust_score);
CREATE INDEX idx_trust_score_history_user_character ON trust_score_history(user_id, character_id);

-- КОНЕЦ СХЕМЫ --