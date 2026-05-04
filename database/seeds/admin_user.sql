-- =============================================================================
-- SEED: ADMIN USER
-- =============================================================================
-- Creates the initial admin user for the platform
-- =============================================================================

-- Enable pgcrypto for password hashing
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create admin user
-- Password: Admin@123456 (change immediately after first login)
INSERT INTO app.users (
    id,
    email,
    password_hash,
    full_name,
    account_type,
    email_verified_at,
    subscription_status,
    created_at,
    updated_at
) VALUES (
    '11111111-1111-1111-1111-111111111111',
    'admin@abdulboy-ebook.com',
    crypt('Admin@123456', gen_salt('bf', 12)),
    'System Administrator',
    'admin',
    NOW(),
    'premium',
    NOW(),
    NOW()
) ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    updated_at = NOW();

-- Create special user (VIP - free access to all books)
INSERT INTO app.users (
    id,
    email,
    password_hash,
    full_name,
    account_type,
    email_verified_at,
    subscription_status,
    subscription_started_at,
    subscription_ends_at,
    created_at,
    updated_at
) VALUES (
    '22222222-2222-2222-2222-222222222222',
    'special@abdulboy-ebook.com',
    crypt('Special@123456', gen_salt('bf', 12)),
    'VIP Special User',
    'special',
    NOW(),
    'premium',
    NOW(),
    NOW() + INTERVAL '100 years',
    NOW(),
    NOW()
) ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    updated_at = NOW();

-- Create normal test user
INSERT INTO app.users (
    id,
    email,
    password_hash,
    full_name,
    account_type,
    email_verified_at,
    subscription_status,
    created_at,
    updated_at
) VALUES (
    '33333333-3333-3333-3333-333333333333',
    'user@example.com',
    crypt('User@123456', gen_salt('bf', 12)),
    'Test Normal User',
    'normal',
    NOW(),
    'free',
    NOW(),
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Output the created users
SELECT 
    email,
    full_name,
    account_type,
    subscription_status,
    created_at
FROM app.users
WHERE email IN ('admin@abdulboy-ebook.com', 'special@abdulboy-ebook.com', 'user@example.com');
