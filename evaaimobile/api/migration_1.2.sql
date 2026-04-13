-- Миграция для добавления поля avatar_url в таблицу characters
-- Версия: 1.2

ALTER TABLE characters ADD COLUMN avatar_url VARCHAR(512);

-- КОНЕЦ МИГРАЦИИ --
