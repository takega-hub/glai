
-- Новая таблица для отслеживания разблокированного контента пользователем
CREATE TABLE user_unlocked_content (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    content_id UUID NOT NULL, -- Не ссылаемся на content(id), т.к. id из JSONB
    unlocked_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, character_id, content_id)
);
