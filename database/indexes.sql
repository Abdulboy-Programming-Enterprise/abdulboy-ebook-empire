-- =============================================================================
-- ADDITIONAL INDEXES FOR PERFORMANCE
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Users table indexes
-- -----------------------------------------------------------------------------

-- For fast login lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_lower ON app.users(LOWER(email));

-- For filtering by account type
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_account_type ON app.users(account_type) WHERE deleted_at IS NULL;

-- For active subscription checks
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_subscription_status ON app.users(subscription_status, subscription_ends_at) 
WHERE subscription_status IN ('basic', 'premium') AND subscription_ends_at > NOW();

-- For gamification leaderboards
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_points ON app.users(total_points DESC) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_streak ON app.users(reading_streak DESC) WHERE deleted_at IS NULL;

-- For recently active users
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_active ON app.users(last_active_at DESC) WHERE deleted_at IS NULL;

-- -----------------------------------------------------------------------------
-- Books table indexes
-- -----------------------------------------------------------------------------

-- For filtering by price and status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_price_status ON app.books(price, status) WHERE status = 'published';

-- For filtering by language
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_language_published ON app.books(language, status, published_at DESC) 
WHERE status = 'published';

-- For free books listing
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_free ON app.books(id) WHERE is_free = true AND status = 'published';

-- For popular books (by downloads)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_downloads ON app.books(downloads_count DESC, views_count DESC) 
WHERE status = 'published';

-- For author lookup
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_author_name ON app.books(author_name);

-- For date range queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_published_date ON app.books(published_at DESC) WHERE status = 'published';

-- For JSONB queries (if any)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_metadata ON app.books USING GIN (metadata);

-- -----------------------------------------------------------------------------
-- Payments table indexes
-- -----------------------------------------------------------------------------

-- For user payment history
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payments_user_status ON app.payments(user_id, status, created_at DESC);

-- For revenue reporting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payments_date_amount ON app.payments(paid_at, amount) WHERE status = 'completed';

-- For gateway transaction lookup
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payments_gateway_id ON app.payments(gateway_transaction_id);

-- For refund tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payments_refunded ON app.payments(refunded_at) WHERE status = 'refunded';

-- For subscription renewal lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payments_subscription ON app.payments(item_type, item_id, status) 
WHERE item_type = 'subscription';

-- -----------------------------------------------------------------------------
-- Subscriptions indexes
-- -----------------------------------------------------------------------------

-- For expiring subscriptions (daily cron job)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_subscriptions_expiring ON app.user_subscriptions(end_date, status) 
WHERE status = 'active' AND end_date > NOW() AND end_date < NOW() + INTERVAL '7 days';

-- For auto-renewal processing
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_subscriptions_auto_renew ON app.user_subscriptions(user_id, plan_id, status) 
WHERE auto_renew = true AND status = 'active';

-- -----------------------------------------------------------------------------
-- Bookings indexes
-- -----------------------------------------------------------------------------

-- For pending bookings (admin dashboard)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bookings_pending ON app.bookings(status, created_at) 
WHERE status = 'pending';

-- For user booking history
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bookings_user_status ON app.bookings(user_id, status, created_at DESC);

-- For deadline monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bookings_deadline_upcoming ON app.bookings(deadline, status) 
WHERE status IN ('accepted', 'in_progress') AND deadline > NOW();

-- -----------------------------------------------------------------------------
-- Reading activity indexes
-- -----------------------------------------------------------------------------

-- For streak calculation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reading_activity_streak ON app.reading_activity(user_id, activity_date DESC);

-- For user reading statistics
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reading_activity_stats ON app.reading_activity(user_id, book_id, total_time_seconds);

-- For popular books tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reading_activity_book ON app.reading_activity(book_id, activity_date DESC);

-- -----------------------------------------------------------------------------
-- Analytics events indexes (if using regular table instead of partitioned)
-- -----------------------------------------------------------------------------

-- For time-series queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_time_user ON analytics.events(created_at, user_id, event_type);

-- For session analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_session_time ON analytics.events(session_id, created_at);

-- For daily active users calculation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_dau ON analytics.events(DATE(created_at), user_id) 
WHERE event_type = 'login' OR event_type = 'page_view';

-- -----------------------------------------------------------------------------
-- Audit log indexes
-- -----------------------------------------------------------------------------

-- For admin action audit trail
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_admin_time ON audit.admin_actions(admin_id, created_at DESC);

-- For target entity audit trail
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_target ON audit.admin_actions(target_type, target_id, created_at DESC);

-- For action type analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_action_type ON audit.admin_actions(action_type, created_at DESC);

-- -----------------------------------------------------------------------------
-- Composite indexes for common query patterns
-- -----------------------------------------------------------------------------

-- Dashboard: Recent books with author info
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_listing ON app.books(status, published_at DESC, downloads_count DESC) 
WHERE status = 'published' INCLUDE (id, title, author_name, cover_image_url, price, is_free);

-- Search: Combined with filter
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_search_filter ON app.books(search_vector, status, price, language) 
WHERE status = 'published';

-- User library: Books purchased by user
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_purchases_library ON app.user_book_purchases(user_id, purchased_at DESC, book_id);

-- -----------------------------------------------------------------------------
-- Partial indexes for specific queries
-- -----------------------------------------------------------------------------

-- Active users only (exclude deleted)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_only ON app.users(id, email, full_name) WHERE deleted_at IS NULL;

-- Published books only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_published_only ON app.books(id, title, slug, price) WHERE status = 'published';

-- Completed payments only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payments_completed_only ON app.payments(user_id, amount, paid_at) WHERE status = 'completed';

-- Active subscriptions only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_active_only ON app.user_subscriptions(user_id, plan_id, end_date) WHERE status = 'active';

-- -----------------------------------------------------------------------------
-- Covering indexes (index-only scans)
-- -----------------------------------------------------------------------------

-- Covering index for book listings (avoids table lookup)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_covering_listing ON app.books(status, published_at DESC) 
INCLUDE (id, title, author_name, cover_image_url, price, is_free, slug);

-- Covering index for user profile (avoids table lookup)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_covering_profile ON app.users(id) 
INCLUDE (email, full_name, avatar_url, account_type, total_points);

-- -----------------------------------------------------------------------------
-- Maintenance: Remove unused indexes (run periodically)
-- -----------------------------------------------------------------------------

-- Query to find unused indexes:
-- SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
-- FROM pg_stat_user_indexes
-- WHERE idx_scan = 0
-- ORDER BY idx_tup_read DESC;
