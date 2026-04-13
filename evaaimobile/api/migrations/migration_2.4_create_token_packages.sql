CREATE TABLE token_packages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    token_amount INT NOT NULL,
    price_usd NUMERIC(10, 2) NOT NULL,
    bonus_tokens INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);