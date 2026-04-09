-- Migration to create comfy_workflows table
-- Version: 2.8

CREATE TABLE comfy_workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    workflow_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_comfy_workflows_name ON comfy_workflows(name);
CREATE INDEX idx_comfy_workflows_is_active ON comfy_workflows(is_active);

-- Function to ensure only one workflow is active
CREATE OR REPLACE FUNCTION ensure_single_active_workflow() RETURNS TRIGGER AS $$
BEGIN
    -- If the new row is being set to active, deactivate all others.
    IF NEW.is_active THEN
        UPDATE comfy_workflows SET is_active = FALSE WHERE id != NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to enforce the single active workflow rule
CREATE TRIGGER trigger_ensure_single_active_workflow
BEFORE INSERT OR UPDATE ON comfy_workflows
FOR EACH ROW
EXECUTE FUNCTION ensure_single_active_workflow();

-- Set the updated_at timestamp on update
CREATE OR REPLACE FUNCTION set_updated_at_timestamp() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_updated_at
BEFORE UPDATE ON comfy_workflows
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_timestamp();

-- End of migration
