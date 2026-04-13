-- Add is_hot column to characters table to mark sexualized characters
ALTER TABLE characters ADD COLUMN IF NOT EXISTS is_hot BOOLEAN DEFAULT FALSE;