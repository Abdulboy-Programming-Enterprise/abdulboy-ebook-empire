-- =============================================================================
-- DATABASE TRIGGERS
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Audit Triggers
-- -----------------------------------------------------------------------------

-- Trigger to log INSERT operations
CREATE OR REPLACE FUNCTION audit.log_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit.admin_actions (admin_id, action_type, target_type, target_id, new_values)
    VALUES (
        NULL, -- Will be set by application
        'INSERT',
        TG_TABLE_NAME,
        NEW.id,
        to_jsonb(NEW)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to log UPDATE operations
CREATE OR REPLACE FUNCTION audit.log_update()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW != OLD THEN
        INSERT INTO audit.admin_actions (admin_id, action_type, target_type, target_id, old_values, new_values)
        VALUES (
            NULL,
            'UPDATE',
            TG_TABLE_NAME,
            NEW.id,
            to_jsonb(OLD),
            to_jsonb(NEW)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to log DELETE operations
CREATE OR REPLACE FUNCTION audit.log_delete()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit.admin_actions (admin_id, action_type, target_type, target_id, old_values)
    VALUES (
        NULL,
        'DELETE',
        TG_TABLE_NAME,
        OLD.id,
        to_jsonb(OLD)
    );
    RETURN OLD;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply audit triggers to critical tables (optional - can be enabled as needed)
-- CREATE TRIGGER audit_users_insert AFTER INSERT ON app.users FOR EACH ROW EXECUTE FUNCTION audit.log_insert();
-- CREATE TRIGGER audit_users_update AFTER UPDATE ON app.users FOR EACH ROW EXECUTE FUNCTION audit.log_update();
-- CREATE TRIGGER audit_users_delete AFTER DELETE ON app.users FOR EACH ROW EXECUTE FUNCTION audit.log_delete();

-- -----------------------------------------------------------------------------
-- Business Logic Triggers
-- -----------------------------------------------------------------------------

-- Update book search vector on change
CREATE OR REPLACE FUNCTION app.update_book_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
                         setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
                         setweight(to_tsvector('english', COALESCE(NEW.author_name, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_book_search_vector ON app.books;
CREATE TRIGGER trigger_update_book_search_vector
    BEFORE INSERT OR UPDATE OF title, description, author_name ON app.books
    FOR EACH ROW
    EXECUTE FUNCTION app.update_book_search_vector();

-- Update user subscription status when subscription expires
CREATE OR REPLACE FUNCTION app.update_expired_subscriptions()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.end_date < NOW() AND NEW.status = 'active' THEN
        UPDATE app.user_subscriptions
        SET status = 'expired'
        WHERE id = NEW.id;
        
        UPDATE app.users
        SET subscription_status = 'expired',
            subscription_ends_at = NULL
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_check_subscription_expiry ON app.user_subscriptions;
CREATE TRIGGER trigger_check_subscription_expiry
    BEFORE UPDATE OF end_date ON app.user_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION app.update_expired_subscriptions();

-- Update user's reading streak when activity recorded
CREATE OR REPLACE FUNCTION app.update_reading_streak()
RETURNS TRIGGER AS $$
DECLARE
    v_last_active DATE;
    v_streak INTEGER;
BEGIN
    -- Get user's last activity date
    SELECT MAX(activity_date) INTO v_last_active
    FROM app.reading_activity
    WHERE user_id = NEW.user_id
    AND activity_date < NEW.activity_date;
    
    -- Calculate streak
    IF v_last_active IS NULL OR v_last_active = NEW.activity_date - INTERVAL '1 day' THEN
        -- Continuous streak
        SELECT reading_streak + 1 INTO v_streak
        FROM app.users
        WHERE id = NEW.user_id;
    ELSE
        -- Streak broken
        v_streak := 1;
    END IF;
    
    -- Update user's streak
    UPDATE app.users
    SET reading_streak = v_streak,
        last_active_at = NOW()
    WHERE id = NEW.user_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_reading_streak ON app.reading_activity;
CREATE TRIGGER trigger_update_reading_streak
    AFTER INSERT ON app.reading_activity
    FOR EACH ROW
    EXECUTE FUNCTION app.update_reading_streak();

-- Prevent deletion of admin users
CREATE OR REPLACE FUNCTION app.prevent_admin_deletion()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.account_type = 'admin' THEN
        RAISE EXCEPTION 'Cannot delete admin user accounts';
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_prevent_admin_deletion ON app.users;
CREATE TRIGGER trigger_prevent_admin_deletion
    BEFORE DELETE ON app.users
    FOR EACH ROW
    EXECUTE FUNCTION app.prevent_admin_deletion();

-- Soft delete books instead of hard delete
CREATE OR REPLACE FUNCTION app.soft_delete_book()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE app.books
    SET deleted_at = NOW(),
        status = 'archived'
    WHERE id = OLD.id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_soft_delete_book ON app.books;
CREATE TRIGGER trigger_soft_delete_book
    INSTEAD OF DELETE ON app.books
    FOR EACH ROW
    EXECUTE FUNCTION app.soft_delete_book();

-- -----------------------------------------------------------------------------
-- Referential Integrity Triggers
-- -----------------------------------------------------------------------------

-- Cascade user deletion to related records (soft delete)
CREATE OR REPLACE FUNCTION app.cascade_user_deletion()
RETURNS TRIGGER AS $$
BEGIN
    -- Soft delete user's subscriptions
    UPDATE app.user_subscriptions
    SET status = 'cancelled',
        cancelled_at = NOW()
    WHERE user_id = OLD.id AND status = 'active';
    
    -- Mark user's payments as anonymized
    UPDATE app.payments
    SET metadata = metadata || jsonb_build_object('user_deleted', true)
    WHERE user_id = OLD.id;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_cascade_user_deletion ON app.users;
CREATE TRIGGER trigger_cascade_user_deletion
    BEFORE DELETE ON app.users
    FOR EACH ROW
    EXECUTE FUNCTION app.cascade_user_deletion();

-- -----------------------------------------------------------------------------
-- Maintenance Triggers
-- -----------------------------------------------------------------------------

-- Auto-vacuum trigger for high-traffic tables (PostgreSQL 13+)
-- Note: This is managed by PostgreSQL's autovacuum daemon
-- These settings are configured via ALTER TABLE statements

ALTER TABLE analytics.events SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02,
    autovacuum_vacuum_threshold = 1000,
    autovacuum_analyze_threshold = 500
);

ALTER TABLE app.payments SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

ALTER TABLE app.user_book_purchases SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

-- -----------------------------------------------------------------------------
-- Notification Triggers
-- -----------------------------------------------------------------------------

-- Trigger to create notification on new custom booking
CREATE OR REPLACE FUNCTION app.notify_new_booking()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert into notifications table (assuming it exists)
    INSERT INTO app.notifications (user_id, type, title, message, metadata)
    VALUES (
        NULL, -- Admin notification
        'new_booking',
        'New Custom Book Request',
        format('User has requested a custom book: %s', NEW.title),
        jsonb_build_object('booking_id', NEW.id, 'user_id', NEW.user_id)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_notify_new_booking ON app.bookings;
CREATE TRIGGER trigger_notify_new_booking
    AFTER INSERT ON app.bookings
    FOR EACH ROW
    WHEN (NEW.status = 'pending')
    EXECUTE FUNCTION app.notify_new_booking();

-- Trigger for successful payment notification
CREATE OR REPLACE FUNCTION app.notify_payment_success()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status = 'pending' THEN
        INSERT INTO app.notifications (user_id, type, title, message, metadata)
        VALUES (
            NEW.user_id,
            'payment_success',
            'Payment Successful',
            format('Your payment of %s %s was successful.', NEW.amount, NEW.currency),
            jsonb_build_object('payment_id', NEW.id, 'item_type', NEW.item_type)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_notify_payment_success ON app.payments;
CREATE TRIGGER trigger_notify_payment_success
    AFTER UPDATE OF status ON app.payments
    FOR EACH ROW
    EXECUTE FUNCTION app.notify_payment_success();
