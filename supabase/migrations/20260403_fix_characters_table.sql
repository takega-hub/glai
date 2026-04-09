-- Fix characters table schema inconsistencies
ALTER TABLE characters
    ADD COLUMN IF NOT EXISTS archetype VARCHAR(100),
    ADD COLUMN IF NOT EXISTS visual_description JSONB,
    ADD COLUMN IF NOT EXISTS is_hot BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(512);

-- Rename personality_type to archetype if it exists, then drop it
DO $$
BEGIN
   IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='characters' AND column_name='personality_type') THEN
      -- Drop the old column
      ALTER TABLE characters DROP COLUMN personality_type;
   END IF;
END $$;

-- Make display_name not null if it was just added
UPDATE characters SET display_name = name WHERE display_name IS NULL;
-- ALTER TABLE characters ALTER COLUMN display_name SET NOT NULL; -- This might fail if the column doesn't exist, let's handle that

DO $$
BEGIN
   IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='characters' AND column_name='display_name') THEN
      ALTER TABLE characters ADD COLUMN display_name VARCHAR(100);
   END IF;
END $$;

UPDATE characters SET display_name = name WHERE display_name IS NULL;
ALTER TABLE characters ALTER COLUMN display_name SET NOT NULL;
