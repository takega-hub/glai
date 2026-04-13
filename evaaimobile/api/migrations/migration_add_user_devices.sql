-- Description: Creates the user_devices table for storing push notification tokens.

CREATE TABLE user_devices (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_token TEXT NOT NULL UNIQUE,
    device_type VARCHAR(20) NOT NULL, -- e.g., 'ios', 'android'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_devices_user_id ON user_devices(user_id);

COMMENT ON TABLE user_devices IS 'Stores device tokens for sending push notifications.';
COMMENT ON COLUMN user_devices.device_token IS 'The unique token provided by the push service (APNs, FCM).';
