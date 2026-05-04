
---

### FILE 066: `/abdulboy-ebook-empire/database/schema.sql`

```sql
-- =============================================================================
-- ABDULBOY EBOOK EMPIRE - DATABASE SCHEMA
-- =============================================================================
-- PostgreSQL 15+
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "citext";

-- =============================================================================
-- SCHEMAS
-- =============================================================================

-- Core application schema
CREATE SCHEMA IF NOT EXISTS app;
COMMENT ON SCHEMA app IS 'Core application tables';

-- Audit schema for logging
CREATE SCHEMA IF NOT EXISTS audit;
COMMENT ON SCHEMA audit IS 'Audit logging and change tracking';

-- Analytics schema
CREATE SCHEMA IF NOT EXISTS analytics;
COMMENT ON SCHEMA analytics IS 'Analytics and reporting tables';

-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- Users table (3 account types: admin, special, normal)
CREATE TABLE app.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email CITEXT NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    
    -- Account type
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('admin', 'special', 'normal')),
    
    -- User preferences
    theme VARCHAR(20) DEFAULT 'light',
    text_size INTEGER DEFAULT 100,
    email_notifications BOOLEAN DEFAULT true,
    push_notifications BOOLEAN DEFAULT true,
    
    -- Gamification
    total_points INTEGER DEFAULT 0,
    reading_streak INTEGER DEFAULT 0,
    last_active_at TIMESTAMP WITH TIME ZONE,
    
    -- Subscription related
    subscription_status VARCHAR(20) DEFAULT 'free' CHECK (subscription_status IN ('free', 'basic', 'premium', 'cancelled', 'expired')),
    subscription_started_at TIMESTAMP WITH TIME ZONE,
    subscription_ends_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    email_verified_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    CONSTRAINT idx_users_email UNIQUE (email),
    CONSTRAINT chk_subscription_dates CHECK (
        (subscription_status = 'free' AND subscription_started_at IS NULL AND subscription_ends_at IS NULL) OR
        (subscription_status IN ('basic', 'premium') AND subscription_started_at IS NOT NULL AND subscription_ends_at IS NOT NULL)
    )
);

COMMENT ON TABLE app.users IS 'All user accounts including admin, special, and normal users';
COMMENT ON COLUMN app.users.account_type IS 'admin: full system access, special: free access to all books, normal: regular user';
COMMENT ON COLUMN app.users.total_points IS 'Points earned from purchases, reviews, and daily activities';
COMMENT ON COLUMN app.users.reading_streak IS 'Consecutive days with reading activity';

-- Books table
CREATE TABLE app.books (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) NOT NULL UNIQUE,
    description TEXT,
    author_name VARCHAR(255) NOT NULL,
    author_id UUID REFERENCES app.users(id) ON DELETE SET NULL,
    
    -- Pricing
    price DECIMAL(10, 2) DEFAULT 0.00,
    is_free BOOLEAN DEFAULT false,
    
    -- Preview settings
    total_pages INTEGER NOT NULL,
    preview_pages INTEGER DEFAULT 10,
    preview_content TEXT,
    
    -- File references
    pdf_url TEXT,
    epub_url TEXT,
    cover_image_url TEXT,
    
    -- Metadata
    isbn VARCHAR(20),
    language VARCHAR(10) DEFAULT 'en',
    publication_date DATE,
    
    -- Watermarking
    enable_watermark BOOLEAN DEFAULT true,
    watermark_text VARCHAR(255),
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    downloads_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    
    -- Timestamps
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Full-text search
    search_vector TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(author_name, '')), 'B')
    ) STORED,
    
    -- Indexes
    CONSTRAINT idx_books_slug UNIQUE (slug),
    CONSTRAINT chk_price CHECK (price >= 0),
    CONSTRAINT chk_preview_pages CHECK (preview_pages <= total_pages AND preview_pages >= 0)
);

CREATE INDEX idx_books_status_published ON app.books(status, published_at) WHERE status = 'published';
CREATE INDEX idx_books_search ON app.books USING GIN (search_vector);
CREATE INDEX idx_books_author_id ON app.books(author_id);
CREATE INDEX idx_books_language ON app.books(language);
CREATE INDEX idx_books_created_at ON app.books(created_at DESC);

COMMENT ON TABLE app.books IS 'Books available for purchase or subscription reading';

-- Tags table (for book categorization)
CREATE TABLE app.tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Book-Tag association (many-to-many)
CREATE TABLE app.book_tags (
    book_id UUID REFERENCES app.books(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES app.tags(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, tag_id)
);

-- Subscriptions plans table
CREATE TABLE app.subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL,
    slug VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    duration_days INTEGER NOT NULL,
    
    -- Features as JSON
    features JSONB,
    
    -- Limits
    books_per_month INTEGER,
    download_limit INTEGER,
    
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_price_positive CHECK (price >= 0),
    CONSTRAINT chk_duration_positive CHECK (duration_days > 0)
);

COMMENT ON TABLE app.subscription_plans IS 'Available subscription plans (Free, Basic, Premium)';
COMMENT ON COLUMN app.subscription_plans.features IS 'JSON array of plan features';

-- User subscriptions (active/inactive subscriptions)
CREATE TABLE app.user_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES app.subscription_plans(id),
    
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    auto_renew BOOLEAN DEFAULT false,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled', 'pending')),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT idx_user_subscriptions_user_id_status UNIQUE (user_id, status) WHERE status = 'active',
    CONSTRAINT chk_dates CHECK (end_date > start_date)
);

CREATE INDEX idx_user_subscriptions_user_id ON app.user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_end_date ON app.user_subscriptions(end_date) WHERE status = 'active';
CREATE INDEX idx_user_subscriptions_plan_id ON app.user_subscriptions(plan_id);

-- Payments table
CREATE TABLE app.payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app.users(id),
    
    -- Payment details
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method VARCHAR(50) NOT NULL, -- 'stripe', 'opay', 'paypal', 'flutterwave'
    
    -- Item purchased
    item_type VARCHAR(20) NOT NULL CHECK (item_type IN ('book', 'subscription', 'custom_booking')),
    item_id UUID NOT NULL, -- book_id, subscription_plan_id, or booking_id
    
    -- Transaction IDs from gateway
    gateway_transaction_id VARCHAR(255),
    gateway_reference VARCHAR(255),
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    
    -- Metadata
    metadata JSONB,
    error_message TEXT,
    
    -- Timestamps
    paid_at TIMESTAMP WITH TIME ZONE,
    refunded_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_amount_positive CHECK (amount >= 0)
);

CREATE INDEX idx_payments_user_id ON app.payments(user_id);
CREATE INDEX idx_payments_status ON app.payments(status);
CREATE INDEX idx_payments_item ON app.payments(item_type, item_id);
CREATE INDEX idx_payments_gateway_ref ON app.payments(gateway_reference);
CREATE INDEX idx_payments_created_at ON app.payments(created_at DESC);

-- User book purchases (for one-time purchases)
CREATE TABLE app.user_book_purchases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app.users(id),
    book_id UUID NOT NULL REFERENCES app.books(id),
    payment_id UUID NOT NULL REFERENCES app.payments(id),
    
    purchase_price DECIMAL(10, 2),
    purchased_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Access tracking
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0,
    
    UNIQUE(user_id, book_id)
);

CREATE INDEX idx_user_book_purchases_user_id ON app.user_book_purchases(user_id);
CREATE INDEX idx_user_book_purchases_book_id ON app.user_book_purchases(book_id);
CREATE INDEX idx_user_book_purchases_purchased_at ON app.user_book_purchases(purchased_at DESC);

-- Custom book bookings
CREATE TABLE app.bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app.users(id),
    
    -- Booking details
    title VARCHAR(500) NOT NULL,
    description TEXT,
    genre VARCHAR(100),
    word_count INTEGER,
    
    -- Requirements
    deadline DATE,
    budget DECIMAL(10, 2),
    requirements TEXT,
    attachments JSONB,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'in_progress', 'completed', 'cancelled', 'delivered')),
    
    -- Communication
    admin_notes TEXT,
    user_notes TEXT,
    
    -- Delivery
    delivery_url TEXT,
    delivered_at TIMESTAMP WITH TIME ZONE,
    accepted_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    payment_id UUID REFERENCES app.payments(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_bookings_user_id ON app.bookings(user_id);
CREATE INDEX idx_bookings_status ON app.bookings(status);
CREATE INDEX idx_bookings_deadline ON app.bookings(deadline) WHERE status NOT IN ('completed', 'cancelled');
CREATE INDEX idx_bookings_created_at ON app.bookings(created_at DESC);

-- =============================================================================
-- GAMIFICATION TABLES
-- =============================================================================

-- Badges definitions
CREATE TABLE app.badges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    image_url TEXT,
    
    -- Badge criteria
    criteria_type VARCHAR(50) NOT NULL, -- 'books_read', 'reviews_written', 'purchase_count', 'streak_days'
    criteria_value INTEGER NOT NULL,
    
    -- Points awarded
    points INTEGER DEFAULT 100,
    
    rarity VARCHAR(20) DEFAULT 'common' CHECK (rarity IN ('common', 'rare', 'epic', 'legendary')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User earned badges
CREATE TABLE app.user_badges (
    user_id UUID NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    badge_id UUID NOT NULL REFERENCES app.badges(id) ON DELETE CASCADE,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    progress INTEGER DEFAULT 100,
    
    PRIMARY KEY (user_id, badge_id)
);

CREATE INDEX idx_user_badges_user_id ON app.user_badges(user_id);
CREATE INDEX idx_user_badges_earned_at ON app.user_badges(earned_at DESC);

-- Reading activity tracking
CREATE TABLE app.reading_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app.users(id),
    book_id UUID NOT NULL REFERENCES app.books(id),
    
    pages_read INTEGER DEFAULT 0,
    total_time_seconds INTEGER DEFAULT 0,
    last_position INTEGER DEFAULT 0,
    
    activity_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, book_id, activity_date)
);

CREATE INDEX idx_reading_activity_user_date ON app.reading_activity(user_id, activity_date DESC);
CREATE INDEX idx_reading_activity_user_book ON app.reading_activity(user_id, book_id);

-- =============================================================================
-- ANALYTICS TABLES
-- =============================================================================

-- Analytics events (partitioned by month - see partitioning script)
CREATE TABLE analytics.events (
    id UUID DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES app.users(id),
    
    event_type VARCHAR(50) NOT NULL, -- 'page_view', 'book_view', 'purchase', 'search', 'login'
    event_data JSONB,
    
    session_id UUID,
    ip_address INET,
    user_agent TEXT,
    referrer TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_user_id ON analytics.events(user_id);
CREATE INDEX idx_events_type ON analytics.events(event_type);
CREATE INDEX idx_events_created_at ON analytics.events(created_at DESC);
CREATE INDEX idx_events_session ON analytics.events(session_id);

-- =============================================================================
-- AUDIT TABLES
-- =============================================================================

-- Admin action audit log
CREATE TABLE audit.admin_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID REFERENCES app.users(id),
    admin_email CITEXT,
    
    action_type VARCHAR(100) NOT NULL,
    target_type VARCHAR(100), -- 'user', 'book', 'payment', 'subscription'
    target_id UUID,
    
    old_values JSONB,
    new_values JSONB,
    
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_admin_actions_admin_id ON audit.admin_actions(admin_id);
CREATE INDEX idx_admin_actions_created_at ON audit.admin_actions(created_at DESC);
CREATE INDEX idx_admin_actions_action_type ON audit.admin_actions(action_type);
CREATE INDEX idx_admin_actions_target ON audit.admin_actions(target_type, target_id);

-- =============================================================================
-- FUNCTIONS & TRIGGERS (See separate files)
-- =============================================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION app.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables with updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON app.users
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at_column();

CREATE TRIGGER update_books_updated_at
    BEFORE UPDATE ON app.books
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at_column();

CREATE TRIGGER update_bookings_updated_at
    BEFORE UPDATE ON app.bookings
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at_column();

CREATE TRIGGER update_payments_updated_at
    BEFORE UPDATE ON app.payments
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at_column();

-- =============================================================================
-- RBAC: Create roles for application access
-- =============================================================================

-- Create application roles
CREATE ROLE ebook_app WITH LOGIN;
CREATE ROLE ebook_readonly WITH LOGIN;
CREATE ROLE ebook_analytics WITH LOGIN;

-- Grant schema permissions
GRANT USAGE ON SCHEMA app TO ebook_app, ebook_readonly, ebook_analytics;
GRANT USAGE ON SCHEMA analytics TO ebook_analytics;

-- App role: full CRUD on required tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO ebook_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA app TO ebook_app;

-- Readonly role: SELECT only
GRANT SELECT ON ALL TABLES IN SCHEMA app TO ebook_readonly;

-- Analytics role: access to analytics schema
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO ebook_analytics;
