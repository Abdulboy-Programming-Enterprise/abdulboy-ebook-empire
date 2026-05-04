-- =============================================================================
-- SEED: TEST DATA
-- =============================================================================
-- Creates test data for development and testing environments
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Create additional test users
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    v_user_ids UUID[] := ARRAY[
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa4',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa5'
    ];
    v_names TEXT[] := ARRAY['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Williams', 'Charlie Brown'];
    v_emails TEXT[] := ARRAY['john@example.com', 'jane@example.com', 'bob@example.com', 'alice@example.com', 'charlie@example.com'];
    v_i INTEGER;
BEGIN
    FOR v_i IN 1..array_length(v_names, 1) LOOP
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
            v_user_ids[v_i],
            v_emails[v_i],
            crypt('Test@123456', gen_salt('bf', 12)),
            v_names[v_i],
            'normal',
            NOW(),
            CASE 
                WHEN v_i = 1 THEN 'premium'
                WHEN v_i = 2 THEN 'basic'
                ELSE 'free'
            END,
            CASE 
                WHEN v_i <= 2 THEN NOW()
                ELSE NULL
            END,
            CASE 
                WHEN v_i = 1 THEN NOW() + INTERVAL '30 days'
                WHEN v_i = 2 THEN NOW() + INTERVAL '15 days'
                ELSE NULL
            END,
            NOW(),
            NOW()
        ) ON CONFLICT (email) DO NOTHING;
    END LOOP;
END $$;

-- -----------------------------------------------------------------------------
-- Create test purchases
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    v_book_ids UUID[] := ARRAY[
        'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
        'cccccccc-cccc-cccc-cccc-cccccccccccc',
        'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'
    ];
    v_user_ids UUID[] := ARRAY[
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3'
    ];
    v_payment_ids UUID[];
    v_i INTEGER;
    v_j INTEGER;
BEGIN
    -- Create payments
    FOR v_i IN 1..array_length(v_user_ids, 1) LOOP
        FOR v_j IN 1..array_length(v_book_ids, 1) LOOP
            IF v_i = v_j OR (v_i = 1 AND v_j <= 2) THEN
                INSERT INTO app.payments (
                    id,
                    user_id,
                    amount,
                    currency,
                    payment_method,
                    item_type,
                    item_id,
                    status,
                    paid_at,
                    gateway_transaction_id,
                    created_at
                ) VALUES (
                    gen_random_uuid(),
                    v_user_ids[v_i],
                    CASE 
                        WHEN v_i = 1 AND v_j = 1 THEN 29.99
                        WHEN v_i = 1 AND v_j = 2 THEN 39.99
                        WHEN v_i = 2 AND v_j = 2 THEN 39.99
                        ELSE 49.99
                    END,
                    'USD',
                    'stripe',
                    'book',
                    v_book_ids[v_j],
                    'completed',
                    NOW() - (v_i * v_j || ' days')::INTERVAL,
                    'test_txn_' || v_i || '_' || v_j,
                    NOW()
                )
                RETURNING id INTO v_payment_ids[v_j];
            END IF;
        END LOOP;
    END LOOP;
    
    -- Create user book purchases
    FOR v_i IN 1..array_length(v_user_ids, 1) LOOP
        FOR v_j IN 1..array_length(v_book_ids, 1) LOOP
            IF v_i = v_j OR (v_i = 1 AND v_j <= 2) THEN
                INSERT INTO app.user_book_purchases (
                    user_id,
                    book_id,
                    payment_id,
                    purchase_price,
                    purchased_at,
                    access_count
                ) VALUES (
                    v_user_ids[v_i],
                    v_book_ids[v_j],
                    (SELECT id FROM app.payments 
                     WHERE user_id = v_user_ids[v_i] 
                     AND item_id = v_book_ids[v_j] 
                     LIMIT 1),
                    CASE 
                        WHEN v_i = 1 AND v_j = 1 THEN 29.99
                        WHEN v_i = 1 AND v_j = 2 THEN 39.99
                        WHEN v_i = 2 AND v_j = 2 THEN 39.99
                        ELSE 49.99
                    END,
                    NOW() - (v_i * v_j || ' days')::INTERVAL,
                    floor(random() * 20 + 1)::INTEGER
                ) ON CONFLICT (user_id, book_id) DO NOTHING;
            END IF;
        END LOOP;
    END LOOP;
END $$;

-- -----------------------------------------------------------------------------
-- Create test reading activity
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    v_user_ids UUID[] := ARRAY[
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa4'
    ];
    v_book_ids UUID[] := ARRAY[
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
        'cccccccc-cccc-cccc-cccc-cccccccccccc',
        'dddddddd-dddd-dddd-dddd-dddddddddddd'
    ];
    v_i INTEGER;
    v_j INTEGER;
    v_k INTEGER;
BEGIN
    FOR v_i IN 1..array_length(v_user_ids, 1) LOOP
        FOR v_j IN 1..array_length(v_book_ids, 1) LOOP
            -- 15 days of activity
            FOR v_k IN 0..14 LOOP
                IF random() > 0.3 THEN  -- 70% chance of activity
                    INSERT INTO app.reading_activity (
                        user_id,
                        book_id,
                        pages_read,
                        total_time_seconds,
                        last_position,
                        activity_date,
                        created_at
                    ) VALUES (
                        v_user_ids[v_i],
                        v_book_ids[v_j],
                        floor(random() * 30 + 10)::INTEGER,
                        floor(random() * 1800 + 300)::INTEGER,
                        floor(random() * 100)::INTEGER,
                        CURRENT_DATE - (v_k || ' days')::INTERVAL,
                        NOW()
                    );
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;
END $$;

-- -----------------------------------------------------------------------------
-- Create test analytics events
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    v_user_ids UUID[] := ARRAY[
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa4',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa5'
    ];
    v_event_types TEXT[] := ARRAY['page_view', 'book_view', 'search', 'login', 'purchase'];
    v_i INTEGER;
    v_j INTEGER;
BEGIN
    FOR v_i IN 1..array_length(v_user_ids, 1) LOOP
        -- 100 events per user
        FOR v_j IN 1..100 LOOP
            INSERT INTO analytics.events (
                user_id,
                event_type,
                event_data,
                session_id,
                ip_address,
                user_agent,
                created_at
            ) VALUES (
                v_user_ids[v_i],
                v_event_types[floor(random() * array_length(v_event_types, 1) + 1)],
                jsonb_build_object(
                    'page', CASE floor(random() * 5)::INTEGER
                        WHEN 0 THEN '/books'
                        WHEN 1 THEN '/about'
                        WHEN 2 THEN '/pricing'
                        WHEN 3 THEN '/book/'
                        ELSE '/'
                    END,
                    'timestamp', EXTRACT(EPOCH FROM NOW())
                ),
                gen_random_uuid(),
                '192.168.1.' || floor(random() * 254 + 1)::INTEGER,
                'Mozilla/5.0 (Test Agent)',
                NOW() - (floor(random() * 30) || ' days')::INTERVAL
            );
        END LOOP;
    END LOOP;
END $$;

-- -----------------------------------------------------------------------------
-- Create test notifications
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    v_user_ids UUID[] := ARRAY[
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3',
        '11111111-1111-1111-1111-111111111111'
    ];
    v_i INTEGER;
    v_j INTEGER;
BEGIN
    FOR v_i IN 1..array_length(v_user_ids, 1) LOOP
        FOR v_j IN 1..5 LOOP
            INSERT INTO app.notifications (
                user_id,
                type,
                title,
                message,
                is_read,
                metadata,
                created_at
            ) VALUES (
                v_user_ids[v_i],
                CASE v_j
                    WHEN 1 THEN 'welcome'
                    WHEN 2 THEN 'new_book'
                    WHEN 3 THEN 'subscription'
                    ELSE 'system'
                END,
                CASE v_j
                    WHEN 1 THEN 'Welcome to Abdulboy Ebook Empire!'
                    WHEN 2 THEN 'New books available'
                    WHEN 3 THEN 'Your subscription is active'
                    ELSE 'System update'
                END,
                CASE v_j
                    WHEN 1 THEN 'Thank you for joining our platform. Start exploring thousands of books!'
                    WHEN 2 THEN 'Check out our latest additions to the library.'
                    WHEN 3 THEN 'You now have access to all premium features.'
                    ELSE 'System maintenance completed successfully.'
                END,
                v_j = 1,  -- First notification unread
                jsonb_build_object('test', true),
                NOW() - (v_j || ' days')::INTERVAL
            );
        END LOOP;
    END LOOP;
END $$;

-- -----------------------------------------------------------------------------
-- Create test custom bookings
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    v_user_ids UUID[] := ARRAY[
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2'
    ];
    v_i INTEGER;
BEGIN
    FOR v_i IN 1..array_length(v_user_ids, 1) LOOP
        INSERT INTO app.bookings (
            user_id,
            title,
            description,
            genre,
            word_count,
            deadline,
            budget,
            requirements,
            status,
            created_at
        ) VALUES (
            v_user_ids[v_i],
            'Custom ' || CASE v_i WHEN 1 THEN 'Thriller' ELSE 'Romance' END || ' Novel',
            'A custom-written novel about ' || CASE v_i WHEN 1 THEN 'mystery and suspense' ELSE 'love and relationships' END,
            CASE v_i WHEN 1 THEN 'Thriller' ELSE 'Romance' END,
            CASE v_i WHEN 1 THEN 50000 ELSE 40000 END,
            NOW() + INTERVAL '60 days',
            CASE v_i WHEN 1 THEN 1500 ELSE 1200 END,
            '{"chapters": 20, "include_illustrations": true, "target_audience": "adults"}'::jsonb,
            CASE v_i WHEN 1 THEN 'pending' ELSE 'accepted' END,
            NOW() - (v_i * 10 || ' days')::INTERVAL
        );
    END LOOP;
END $$;

-- Output summary
SELECT 'Test Data Seeded Successfully' as status;
SELECT 
    COUNT(*) as total_users,
    COUNT(DISTINCT user_id) as users_with_purchases,
    COUNT(*) as total_purchases
FROM app.user_book_purchases;
