-- Recreate token_packages table with UUID primary key

DROP TABLE IF EXISTS token_packages CASCADE;

CREATE TABLE token_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    token_amount INT NOT NULL,
    price_usd NUMERIC(10, 2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    bonus_tokens INT DEFAULT 0
);

INSERT INTO token_packages (name, token_amount, price_usd, bonus_tokens) VALUES
('Starter Pack', 100, 0.99, 10),
('Basic Pack', 500, 4.99, 50),
('Premium Pack', 1000, 9.99, 150),
('Mega Pack', 5000, 39.99, 1000);
