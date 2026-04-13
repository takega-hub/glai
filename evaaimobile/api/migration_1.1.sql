-- Миграция для поддержки данных от AI-сценариста
-- Версия: 1.1

-- 1. Изменения в таблице `characters`
ALTER TABLE characters RENAME COLUMN personality_type TO archetype;
ALTER TABLE characters ADD COLUMN sexuality_level INT;
ALTER TABLE characters ADD COLUMN visual_description JSONB;
ALTER TABLE characters ADD COLUMN voice_settings JSONB;

-- 2. Изменения в таблице `layers`
ALTER TABLE layers RENAME COLUMN min_trust_score TO min_trust;
ALTER TABLE layers RENAME COLUMN max_trust_score TO max_trust;
ALTER TABLE layers ADD COLUMN emotional_state TEXT;
ALTER TABLE layers ADD COLUMN what_is_revealed TEXT;
ALTER TABLE layers ADD COLUMN content_plan JSONB;

-- КОНЕЦ МИГРАЦИИ --
