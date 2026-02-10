-- Coffee Tally Database Setup Script
-- Run this script in MySQL to set up the database

-- Create database
CREATE DATABASE IF NOT EXISTS coffee_tally;
USE coffee_tally;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    credit INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_card_id (card_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Optional: Create a dedicated database user
-- Uncomment and modify these lines if you want to create a new user
-- Replace 'your_secure_password' with a strong password

-- CREATE USER IF NOT EXISTS 'coffee_user'@'localhost' IDENTIFIED BY 'your_secure_password';
-- GRANT ALL PRIVILEGES ON coffee_tally.* TO 'coffee_user'@'localhost';
-- FLUSH PRIVILEGES;

-- Optional: Add some test users
-- Uncomment these lines to add test data
-- Replace the card_id values with actual card IDs from your cards

-- INSERT INTO users (card_id, name, credit) VALUES
-- ('04A1B2C3D4E5F6', 'John Doe', 10),
-- ('04F6E5D4C3B2A1', 'Jane Smith', 5),
-- ('0412345678ABCD', 'Test User', 3);

-- Verify table creation
SHOW TABLES;
DESCRIBE users;

-- Show current users (will be empty if test data not inserted)
SELECT * FROM users;
