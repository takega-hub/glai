ALTER TABLE character_llm_prompts
ADD COLUMN identity TEXT,
ADD COLUMN personality TEXT,
ADD COLUMN voice_style TEXT,
ADD COLUMN the_secret TEXT,
ADD COLUMN behavior_rules TEXT,
ADD COLUMN layer_behavior TEXT,
ADD COLUMN format_rules TEXT;