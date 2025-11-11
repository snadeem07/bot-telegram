-- Database Schema for Telegram Expense Tracker Bot
-- PostgreSQL 15+
--
-- Usage: psql -h localhost -U your_user -d expense_tracker < schema.sql

-- Create banks table
CREATE TABLE IF NOT EXISTS banks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create merchants table
CREATE TABLE IF NOT EXISTS merchants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    merchant_id INTEGER REFERENCES merchants(id),
    bank_id INTEGER REFERENCES banks(id),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create receipts table
CREATE TABLE IF NOT EXISTS receipts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    merchant_id INTEGER REFERENCES merchants(id),
    receipt_date TIMESTAMP NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create receipt_items table
CREATE TABLE IF NOT EXISTS receipt_items (
    id SERIAL PRIMARY KEY,
    receipt_id INTEGER REFERENCES receipts(id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_receipts_user_id ON receipts(user_id);
CREATE INDEX IF NOT EXISTS idx_receipt_items_receipt_id ON receipt_items(receipt_id);

-- Insert sample data (optional - comment out if not needed)

-- Sample banks
INSERT INTO banks (name, description) VALUES
    ('Chase Bank', 'Primary checking account'),
    ('Bank of America', 'Savings account'),
    ('Wells Fargo', 'Credit card'),
    ('Citi Bank', 'Business account')
ON CONFLICT DO NOTHING;

-- Sample categories
INSERT INTO categories (name, description) VALUES
    ('Food & Dining', 'Restaurants, groceries, and food delivery'),
    ('Transportation', 'Gas, public transit, parking, and ride-sharing'),
    ('Shopping', 'Clothing, electronics, and general shopping'),
    ('Entertainment', 'Movies, concerts, games, and hobbies'),
    ('Bills & Utilities', 'Rent, electricity, water, internet, phone'),
    ('Healthcare', 'Medical expenses, pharmacy, insurance'),
    ('Education', 'Books, courses, tuition'),
    ('Travel', 'Hotels, flights, vacation expenses'),
    ('Personal Care', 'Haircuts, cosmetics, gym membership'),
    ('Groceries', 'Supermarket and grocery stores'),
    ('Home', 'Furniture, repairs, home improvement'),
    ('Gifts & Donations', 'Gifts and charitable donations'),
    ('Other', 'Miscellaneous expenses')
ON CONFLICT (name) DO NOTHING;

-- Sample merchants
INSERT INTO merchants (name, category_id) VALUES
    ('Starbucks', (SELECT id FROM categories WHERE name = 'Food & Dining')),
    ('McDonald''s', (SELECT id FROM categories WHERE name = 'Food & Dining')),
    ('Whole Foods', (SELECT id FROM categories WHERE name = 'Groceries')),
    ('Target', (SELECT id FROM categories WHERE name = 'Shopping')),
    ('Amazon', (SELECT id FROM categories WHERE name = 'Shopping')),
    ('Shell Gas Station', (SELECT id FROM categories WHERE name = 'Transportation')),
    ('Uber', (SELECT id FROM categories WHERE name = 'Transportation')),
    ('Netflix', (SELECT id FROM categories WHERE name = 'Entertainment')),
    ('CVS Pharmacy', (SELECT id FROM categories WHERE name = 'Healthcare')),
    ('LA Fitness', (SELECT id FROM categories WHERE name = 'Personal Care'))
ON CONFLICT DO NOTHING;

-- Verify table creation
SELECT 'Tables created successfully!' as status;
SELECT 'Banks count: ' || COUNT(*) FROM banks;
SELECT 'Categories count: ' || COUNT(*) FROM categories;
SELECT 'Merchants count: ' || COUNT(*) FROM merchants;
