-- Add new columns to the photos table for enhanced search capabilities

ALTER TABLE public.photos
ADD COLUMN IF NOT EXISTS intent_tags TEXT[],
ADD COLUMN IF NOT EXISTS mood_tags TEXT[],
ADD COLUMN IF NOT EXISTS complexity_level INTEGER;

-- Note: The description_vector column (VECTOR type) requires the pg_vector extension.
-- This should be enabled in your Supabase project settings.
-- The following line is commented out as it might fail if the extension is not enabled.
-- ALTER TABLE public.photos ADD COLUMN IF NOT EXISTS description_vector VECTOR(384);

COMMENT ON COLUMN public.photos.intent_tags IS 'Tags representing the user intent (e.g., casual, intimate, specific).';
COMMENT ON COLUMN public.photos.mood_tags IS 'Tags representing the mood of the photo (e.g., happy, sad, romantic).';
COMMENT ON COLUMN public.photos.complexity_level IS 'A score representing the complexity or intimacy of the photo.';
-- COMMENT ON COLUMN public.photos.description_vector IS 'Vector representation of the photo description for semantic search.';
