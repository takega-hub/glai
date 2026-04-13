ALTER TABLE users ADD COLUMN display_name VARCHAR(100);
ALTER TABLE users RENAME COLUMN last_active TO last_active_at;