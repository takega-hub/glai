-- SQL-схема для проекта EVA AI
-- Версия: 2.0
-- Дата: 30.03.2025

-- Расширение для использования UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Перечисление для ролей пользователей
CREATE TYPE user_role AS ENUM ('super_admin', 'content_manager', 'character_writer', 'analyst', 'support', 'user');

-- Перечисление для статуса персонажа
CREATE TYPE character_status AS ENUM ('active', 'draft', 'archived');

-- Перечисление для типа контента
CREATE TYPE content_type AS ENUM ('photo', 'video', 'audio', 'text');

-- Перечисление для типов транзакций
CREATE TYPE transaction_type AS ENUM ('purchase', 'gift_sent', 'gift_received', 'content_unlock', 'on_demand_generation');

-- Таблица пользователей (администраторы и пользователи приложения)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role user_role NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active', -- active/blocked
    tokens INT DEFAULT 0,
    trust_score INT DEFAULT 0
);

-- Таблица AI-персонажей
CREATE TABLE characters (
    id SERIAL PRIMARY KEY,
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
    character_id INT REFERENCES characters(id) ON DELETE CASCADE,
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
    id SERIAL PRIMARY KEY,
    layer_id INT REFERENCES layers(id) ON DELETE SET NULL, -- Контент может быть не привязан к слою
    character_id INT REFERENCES characters(id) ON DELETE CASCADE,
    type content_type NOT NULL,
    url VARCHAR(512) NOT NULL,
    thumbnail_url VARCHAR(512),
    description TEXT,
    is_locked BOOLEAN DEFAULT TRUE,
    tags JSONB, -- ["эротика", "сюжетное", "портрет"]
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица для отслеживания состояния пользователя с персонажем
CREATE TABLE user_character_state (
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    character_id INT REFERENCES characters(id) ON DELETE CASCADE,
    trust_score INT DEFAULT 0,
    current_layer INT DEFAULT 0,
    layers_unlocked JSONB DEFAULT '[]', -- [{"layer_id": 1, "unlocked_at": "..."}]
    content_unlocked JSONB DEFAULT '[]', -- [{"content_id": "...", "unlocked_at": "..."}]
    conversation_history JSONB, -- последние N сообщений
    last_message_date TIMESTAMPTZ,
    PRIMARY KEY (user_id, character_id)
);

-- Таблица для истории изменения trust_score
CREATE TABLE trust_score_history (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    character_id INT NOT NULL,
    points INT NOT NULL,
    reason VARCHAR(255), -- 'message', 'gift', 'penalty', etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id, character_id) REFERENCES user_character_state(user_id, character_id)
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

-- Таблица подарков
CREATE TABLE gifts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    token_cost INT NOT NULL,
    image_url VARCHAR(512),
    category VARCHAR(50) NOT NULL, -- 'virtual', 'premium', 'exclusive'
    trust_score_required INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица для транзакций (покупка токенов, подарки, разблокировка контента)
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    type transaction_type NOT NULL,
    amount INT NOT NULL, -- Положительное для получения, отрицательное для траты
    description TEXT,
    balance_after INT, -- Баланс после транзакции
    related_user_id INT REFERENCES users(id), -- Для подарков
    related_gift_id INT REFERENCES gifts(id), -- Для подарков
    related_content_id INT REFERENCES content(id), -- Для разблокировки контента
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица для on-demand генерации изображений
CREATE TABLE on_demand_generations (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    character_id INT REFERENCES characters(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    image_url VARCHAR(512),
    trust_level INT NOT NULL, -- Уровень доверия, определяющий откровенность
    token_cost INT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Таблица для проактивных сообщений AI
CREATE TABLE proactive_messages (
    id SERIAL PRIMARY KEY,
    character_id INT REFERENCES characters(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(50) NOT NULL, -- 'greeting', 'photo', 'flirt', 'story'
    content TEXT NOT NULL,
    image_url VARCHAR(512),
    trust_score_min INT DEFAULT 0,
    trust_score_max INT,
    last_sent TIMESTAMPTZ,
    send_count INT DEFAULT 0,
    max_sends INT DEFAULT 3,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица для сообщений диалога
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    character_id INT REFERENCES characters(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    trust_score_change INT DEFAULT 0,
    layer_unlocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для ускорения запросов
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_user_character_state_trust_score ON user_character_state(trust_score);
CREATE INDEX idx_trust_score_history_user_character ON trust_score_history(user_id, character_id);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_on_demand_generations_user_id ON on_demand_generations(user_id);
CREATE INDEX idx_on_demand_generations_status ON on_demand_generations(status);
CREATE INDEX idx_proactive_messages_user_id ON proactive_messages(user_id);
CREATE INDEX idx_proactive_messages_character_id ON proactive_messages(character_id);
CREATE INDEX idx_messages_user_id_character_id ON messages(user_id, character_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_content_character_id ON content(character_id);
CREATE INDEX idx_content_layer_id ON content(layer_id);

-- Примеры данных для тестирования
INSERT INTO token_packages (name, token_amount, price_usd, bonus_tokens) VALUES
('Starter Pack', 100, 0.99, 10),
('Basic Pack', 500, 4.99, 50),
('Premium Pack', 1000, 9.99, 150),
('Mega Pack', 5000, 39.99, 1000);

INSERT INTO gifts (name, description, token_cost, image_url, category, trust_score_required) VALUES
('Virtual Rose', 'A beautiful virtual rose to show your affection', 10, '/images/gifts/rose.png', 'virtual', 0),
('Digital Heart', 'Send your heart to show deep feelings', 25, '/images/gifts/heart.png', 'virtual', 10),
('Premium Photo', 'Unlock exclusive photos from your AI companion', 100, '/images/gifts/photo.png', 'premium', 50),
('Exclusive Video', 'Get access to private video messages', 250, '/images/gifts/video.png', 'exclusive', 100),
('VIP Access', 'Unlock premium features and exclusive content', 500, '/images/gifts/vip.png', 'exclusive', 200);

-- КОНЕЦ СХЕМЫ --