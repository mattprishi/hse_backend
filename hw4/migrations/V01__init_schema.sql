-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create ads table
CREATE TABLE IF NOT EXISTS ads (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    category INTEGER NOT NULL CHECK (category >= 0 AND category <= 100),
    images_qty INTEGER NOT NULL CHECK (images_qty >= 0 AND images_qty <= 10),
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create index for foreign key
CREATE INDEX IF NOT EXISTS idx_ads_user_id ON ads(user_id);
