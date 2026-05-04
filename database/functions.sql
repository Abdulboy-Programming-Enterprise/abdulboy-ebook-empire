-- =============================================================================
-- DATABASE FUNCTIONS
-- =============================================================================

-- -----------------------------------------------------------------------------
-- User Management Functions
-- -----------------------------------------------------------------------------

-- Create new user with validation
CREATE OR REPLACE FUNCTION app.create_user(
    p_email TEXT,
    p_password_hash TEXT,
    p_full_name TEXT,
    p_account_type VARCHAR DEFAULT 'normal'
)
RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
BEGIN
    -- Validate email format
    IF p_email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
        RAISE EXCEPTION 'Invalid email format';
    END IF;
    
    -- Validate account type
    IF p_account_type NOT IN ('admin', 'special', 'normal') THEN
        RAISE EXCEPTION 'Invalid account type';
    END IF;
    
    -- Insert user
    INSERT INTO app.users (email, password_hash, full_name, account_type)
    VALUES (p_email, p_password_hash, p_full_name, p_account_type)
    RETURNING id INTO v_user_id;
    
    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get user by email with active subscription info
CREATE OR REPLACE FUNCTION app.get_user_with_subscription(p_email TEXT)
RETURNS TABLE(
    user_id UUID,
    email CITEXT,
    full_name VARCHAR,
    account_type VARCHAR,
    subscription_status VARCHAR,
    subscription_ends_at TIMESTAMP WITH TIME ZONE,
    is_active_subscription BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id,
        u.email,
        u.full_name,
        u.account_type,
        u.subscription_status,
        u.subscription_ends_at,
        (u.subscription_status IN ('basic', 'premium') AND u.subscription_ends_at > NOW()) AS is_active_subscription
    FROM app.users u
    WHERE u.email = p_email
    AND u.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- -----------------------------------------------------------------------------
-- Book Management Functions
-- -----------------------------------------------------------------------------

-- Search books with filters and pagination
CREATE OR REPLACE FUNCTION app.search_books(
    p_search_query TEXT DEFAULT NULL,
    p_tags TEXT[] DEFAULT NULL,
    p_min_price DECIMAL DEFAULT NULL,
    p_max_price DECIMAL DEFAULT NULL,
    p_language VARCHAR DEFAULT NULL,
    p_sort_by VARCHAR DEFAULT 'relevance',
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE(
    book_id UUID,
    title VARCHAR,
    slug VARCHAR,
    author_name VARCHAR,
    cover_image_url TEXT,
    price DECIMAL,
    is_free BOOLEAN,
    relevance FLOAT4,
    total_count BIGINT
) AS $$
DECLARE
    v_search_query TSQUERY;
    v_total_count BIGINT;
BEGIN
    -- Prepare search query
    IF p_search_query IS NOT NULL AND p_search_query != '' THEN
        v_search_query := plainto_tsquery('english', p_search_query);
    END IF;
    
    -- Get total count
    SELECT COUNT(*) INTO v_total_count
    FROM app.books b
    WHERE b.status = 'published'
    AND (p_search_query IS NULL OR b.search_vector @@ v_search_query)
    AND (p_tags IS NULL OR EXISTS (
        SELECT 1 FROM app.book_tags bt 
        WHERE bt.book_id = b.id AND bt.tag_id = ANY(p_tags)
    ))
    AND (p_min_price IS NULL OR b.price >= p_min_price)
    AND (p_max_price IS NULL OR b.price <= p_max_price)
    AND (p_language IS NULL OR b.language = p_language);
    
    -- Return results
    RETURN QUERY
    SELECT 
        b.id,
        b.title,
        b.slug,
        b.author_name,
        b.cover_image_url,
        b.price,
        b.is_free,
        CASE 
            WHEN p_sort_by = 'relevance' AND p_search_query IS NOT NULL 
                THEN ts_rank(b.search_vector, v_search_query)::FLOAT4
            WHEN p_sort_by = 'price_asc' THEN 0
            WHEN p_sort_by = 'price_desc' THEN 0
            WHEN p_sort_by = 'popular' THEN (b.downloads_count + b.views_count * 0.1)::FLOAT4
            ELSE EXTRACT(EPOCH FROM b.published_at)::FLOAT4
        END AS relevance,
        v_total_count
    FROM app.books b
    WHERE b.status = 'published'
    AND (p_search_query IS NULL OR b.search_vector @@ v_search_query)
    AND (p_tags IS NULL OR EXISTS (
        SELECT 1 FROM app.book_tags bt 
        WHERE bt.book_id = b.id AND bt.tag_id = ANY(p_tags)
    ))
    AND (p_min_price IS NULL OR b.price >= p_min_price)
    AND (p_max_price IS NULL OR b.price <= p_max_price)
    AND (p_language IS NULL OR b.language = p_language)
    ORDER BY
        CASE 
            WHEN p_sort_by = 'price_asc' THEN b.price
            WHEN p_sort_by = 'price_desc' THEN -b.price
            WHEN p_sort_by = 'newest' THEN b.published_at
            WHEN p_sort_by = 'oldest' THEN -EXTRACT(EPOCH FROM b.published_at)
            ELSE relevance
        END DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get popular books based on views and purchases
CREATE OR REPLACE FUNCTION app.get_popular_books(
    p_limit INTEGER DEFAULT 10,
    p_days_back INTEGER DEFAULT 30
)
RETURNS TABLE(
    book_id UUID,
    title VARCHAR,
    author_name VARCHAR,
    cover_image_url TEXT,
    score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.id,
        b.title,
        b.author_name,
        b.cover_image_url,
        (b.downloads_count * 2 + b.views_count * 0.5 + COALESCE(p.purchase_count, 0) * 3)::DECIMAL AS score
    FROM app.books b
    LEFT JOIN (
        SELECT book_id, COUNT(*) as purchase_count
        FROM app.user_book_purchases
        WHERE purchased_at > NOW() - (p_days_back || ' days')::INTERVAL
        GROUP BY book_id
    ) p ON p.book_id = b.id
    WHERE b.status = 'published'
    AND b.published_at > NOW() - (p_days_back || ' days')::INTERVAL
    ORDER BY score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- -----------------------------------------------------------------------------
-- Payment Functions
-- -----------------------------------------------------------------------------

-- Process payment and update relevant records
CREATE OR REPLACE FUNCTION app.process_payment(
    p_payment_id UUID,
    p_gateway_transaction_id TEXT,
    p_gateway_reference TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_payment RECORD;
    v_user_id UUID;
    v_item_type VARCHAR;
    v_item_id UUID;
BEGIN
    -- Get payment details
    SELECT * INTO v_payment
    FROM app.payments
    WHERE id = p_payment_id AND status = 'pending';
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Payment not found or already processed';
    END IF;
    
    v_user_id := v_payment.user_id;
    v_item_type := v_payment.item_type;
    v_item_id := v_payment.item_id;
    
    -- Update payment status
    UPDATE app.payments
    SET 
        status = 'completed',
        gateway_transaction_id = p_gateway_transaction_id,
        gateway_reference = p_gateway_reference,
        paid_at = NOW(),
        updated_at = NOW()
    WHERE id = p_payment_id;
    
    -- Handle based on item type
    CASE v_item_type
        WHEN 'book' THEN
            -- Add book to user's library
            INSERT INTO app.user_book_purchases (user_id, book_id, payment_id, purchase_price)
            SELECT v_user_id, v_item_id, p_payment_id, amount
            FROM app.payments WHERE id = p_payment_id
            ON CONFLICT (user_id, book_id) DO NOTHING;
            
            -- Update book download count
            UPDATE app.books SET downloads_count = downloads_count + 1
            WHERE id = v_item_id;
            
        WHEN 'subscription' THEN
            -- Update user subscription
            UPDATE app.users
            SET 
                subscription_status = (
                    SELECT CASE 
                        WHEN sp.name = 'Basic' THEN 'basic'
                        WHEN sp.name = 'Premium' THEN 'premium'
                        ELSE 'free'
                    END
                    FROM app.subscription_plans sp WHERE sp.id = v_item_id
                ),
                subscription_started_at = NOW(),
                subscription_ends_at = NOW() + (
                    SELECT duration_days || ' days'::INTERVAL
                    FROM app.subscription_plans WHERE id = v_item_id
                ),
                updated_at = NOW()
            WHERE id = v_user_id;
            
            -- Create subscription record
            INSERT INTO app.user_subscriptions (user_id, plan_id, start_date, end_date, auto_renew, status)
            SELECT 
                v_user_id,
                v_item_id,
                NOW(),
                NOW() + (sp.duration_days || ' days'::INTERVAL),
                true,
                'active'
            FROM app.subscription_plans sp WHERE sp.id = v_item_id;
            
        WHEN 'custom_booking' THEN
            -- Update booking status
            UPDATE app.bookings
            SET 
                status = 'accepted',
                accepted_at = NOW(),
                payment_id = p_payment_id,
                updated_at = NOW()
            WHERE id = v_item_id;
            
    END CASE;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- -----------------------------------------------------------------------------
-- Gamification Functions
-- -----------------------------------------------------------------------------

-- Award points to user
CREATE OR REPLACE FUNCTION app.award_points(
    p_user_id UUID,
    p_points INTEGER,
    p_reason TEXT
)
RETURNS INTEGER AS $$
DECLARE
    v_new_total INTEGER;
BEGIN
    UPDATE app.users
    SET total_points = total_points + p_points,
        updated_at = NOW()
    WHERE id = p_user_id
    RETURNING total_points INTO v_new_total;
    
    -- Log point award (optional: create point history table)
    INSERT INTO audit.admin_actions (admin_id, action_type, target_type, target_id, new_values)
    VALUES (NULL, 'AWARD_POINTS', 'user', p_user_id, jsonb_build_object('points', p_points, 'reason', p_reason, 'new_total', v_new_total));
    
    RETURN v_new_total;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Check and award badges based on criteria
CREATE OR REPLACE FUNCTION app.check_and_award_badges(p_user_id UUID)
RETURNS TABLE(badge_id UUID, badge_name VARCHAR) AS $$
DECLARE
    v_user RECORD;
    v_badge RECORD;
BEGIN
    -- Get user stats
    SELECT 
        u.id,
        u.total_points,
        u.reading_streak,
        COALESCE(br.books_read, 0) as books_read,
        COALESCE(rw.reviews_written, 0) as reviews_written,
        COALESCE(pc.purchase_count, 0) as purchase_count
    INTO v_user
    FROM app.users u
    LEFT JOIN (
        SELECT user_id, COUNT(*) as books_read
        FROM app.user_book_purchases
        GROUP BY user_id
    ) br ON br.user_id = u.id
    LEFT JOIN (
        SELECT user_id, COUNT(*) as reviews_written
        -- Assuming a reviews table exists
        FROM app.reviews
        GROUP BY user_id
    ) rw ON rw.user_id = u.id
    LEFT JOIN (
        SELECT user_id, COUNT(*) as purchase_count
        FROM app.payments
        WHERE status = 'completed'
        GROUP BY user_id
    ) pc ON pc.user_id = u.id
    WHERE u.id = p_user_id;
    
    -- Check each badge criteria
    FOR v_badge IN 
        SELECT * FROM app.badges WHERE is_active = true
    LOOP
        -- Check if user already has badge
        IF NOT EXISTS (SELECT 1 FROM app.user_badges WHERE user_id = p_user_id AND badge_id = v_badge.id) THEN
            -- Check criteria
            IF (v_badge.criteria_type = 'books_read' AND v_user.books_read >= v_badge.criteria_value) OR
               (v_badge.criteria_type = 'reviews_written' AND v_user.reviews_written >= v_badge.criteria_value) OR
               (v_badge.criteria_type = 'purchase_count' AND v_user.purchase_count >= v_badge.criteria_value) OR
               (v_badge.criteria_type = 'streak_days' AND v_user.reading_streak >= v_badge.criteria_value) OR
               (v_badge.criteria_type = 'total_points' AND v_user.total_points >= v_badge.criteria_value) THEN
                
                -- Award badge
                INSERT INTO app.user_badges (user_id, badge_id, earned_at)
                VALUES (p_user_id, v_badge.id, NOW());
                
                -- Award points
                PERFORM app.award_points(p_user_id, v_badge.points, 'Earned badge: ' || v_badge.name);
                
                RETURN NEXT;
            END IF;
        END IF;
    END LOOP;
    
    RETURN;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- -----------------------------------------------------------------------------
-- Analytics Functions
-- -----------------------------------------------------------------------------

-- Track user activity
CREATE OR REPLACE FUNCTION analytics.track_event(
    p_user_id UUID,
    p_event_type VARCHAR,
    p_event_data JSONB,
    p_session_id UUID DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
BEGIN
    INSERT INTO analytics.events (user_id, event_type, event_data, session_id, ip_address, user_agent, created_at)
    VALUES (p_user_id, p_event_type, p_event_data, p_session_id, p_ip_address, p_user_agent, NOW())
    RETURNING id INTO v_event_id;
    
    -- Update user last active
    UPDATE app.users SET last_active_at = NOW() WHERE id = p_user_id;
    
    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get daily active users (DAU)
CREATE OR REPLACE FUNCTION analytics.get_daily_active_users(p_date DATE DEFAULT CURRENT_DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(DISTINCT user_id)
        FROM analytics.events
        WHERE DATE(created_at) = p_date
        AND event_type IN ('login', 'page_view', 'book_view')
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- -----------------------------------------------------------------------------
-- Admin Functions
-- -----------------------------------------------------------------------------

-- Create special user account (free access to all books)
CREATE OR REPLACE FUNCTION app.create_special_user(
    p_email TEXT,
    p_full_name TEXT,
    p_created_by_admin_id UUID
)
RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
    v_temp_password TEXT;
BEGIN
    -- Generate temporary password
    v_temp_password := encode(gen_random_bytes(12), 'base64');
    
    -- Create user with special account type
    INSERT INTO app.users (email, password_hash, full_name, account_type, subscription_status)
    VALUES (p_email, crypt(v_temp_password, gen_salt('bf')), p_full_name, 'special', 'premium')
    RETURNING id INTO v_user_id;
    
    -- Grant premium subscription access
    UPDATE app.users
    SET 
        subscription_started_at = NOW(),
        subscription_ends_at = NOW() + INTERVAL '100 years',
        updated_at = NOW()
    WHERE id = v_user_id;
    
    -- Log admin action
    INSERT INTO audit.admin_actions (admin_id, action_type, target_type, target_id, new_values)
    VALUES (p_created_by_admin_id, 'CREATE_SPECIAL_USER', 'user', v_user_id, 
            jsonb_build_object('email', p_email, 'full_name', p_full_name, 'temp_password', v_temp_password));
    
    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
