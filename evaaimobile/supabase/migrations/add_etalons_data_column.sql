-- Add etalons_data column to characters table to store both textual and visual etalons
ALTER TABLE characters 
ADD COLUMN IF NOT EXISTS etalons_data JSONB DEFAULT '{}';

-- Add comment to explain the new column
COMMENT ON COLUMN characters.etalons_data IS 'Stores both textual and visual etalons for character consistency: {textual_etalon: {...}, visual_etalon_path: "...", created_at: "..."}';