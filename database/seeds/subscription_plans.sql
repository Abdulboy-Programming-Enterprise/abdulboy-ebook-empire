-- =============================================================================
-- SEED: SUBSCRIPTION PLANS
-- =============================================================================
-- Creates subscription plans for the platform
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Free Plan
-- -----------------------------------------------------------------------------
INSERT INTO app.subscription_plans (
    id,
    name,
    slug,
    description,
    price,
    currency,
    duration_days,
    features,
    books_per_month,
    download_limit,
    sort_order,
    is_active,
    created_at
) VALUES (
    'f1111111-f111-f111-f111-f11111111111',
    'Free',
    'free',
    'Access to free books only',
    0.00,
    'USD',
    365,
    '["Access to free books", "Limited previews", "Basic support"]'::jsonb,
    3,
    3,
    1,
    true,
    NOW()
);

-- -----------------------------------------------------------------------------
-- Basic Plan
-- -----------------------------------------------------------------------------
INSERT INTO app.subscription_plans (
    id,
    name,
    slug,
    description,
    price,
    currency,
    duration_days,
    features,
    books_per_month,
    download_limit,
    sort_order,
    is_active,
    created_at
) VALUES (
    'f2222222-f222-f222-f222-f22222222222',
    'Basic',
    'basic',
    'Access to all books with limited monthly reads',
    9.99,
    'USD',
    30,
    '["Access to all books", "10 books per month", "Download up to 5 books", "Email support"]'::jsonb,
    10,
    5,
    2,
    true,
    NOW()
);

-- -----------------------------------------------------------------------------
-- Premium Plan
-- -----------------------------------------------------------------------------
INSERT INTO app.subscription_plans (
    id,
    name,
    slug,
    description,
    price,
    currency,
    duration_days,
    features,
    books_per_month,
    download_limit,
    sort_order,
    is_active,
    created_at
) VALUES (
    'f3333333-f333-f333-f333-f33333333333',
    'Premium',
    'premium',
    'Unlimited access to all books with premium features',
    19.99,
    'USD',
    30,
    '["Unlimited books", "Unlimited downloads", "Offline reading", "Priority support", "Early access to new releases", "Ad-free experience"]'::jsonb,
    NULL,
    NULL,
    3,
    true,
    NOW()
);

-- -----------------------------------------------------------------------------
-- Annual Premium Plan (Discounted)
-- -----------------------------------------------------------------------------
INSERT INTO app.subscription_plans (
    id,
    name,
    slug,
    description,
    price,
    currency,
    duration_days,
    features,
    books_per_month,
    download_limit,
    sort_order,
    is_active,
    created_at
) VALUES (
    'f4444444-f444-f444-f444-f44444444444',
    'Premium Annual',
    'premium-annual',
    'Unlimited access for one year at a discounted rate',
    199.99,
    'USD',
    365,
    '["Unlimited books", "Unlimited downloads", "Offline reading", "Priority support", "Early access to new releases", "Ad-free experience", "Exclusive author events"]'::jsonb,
    NULL,
    NULL,
    4,
    true,
    NOW()
);

-- Output the created plans
SELECT 
    name,
    price,
    currency,
    duration_days,
    books_per_month,
    download_limit,
    is_active
FROM app.subscription_plans
ORDER BY sort_order;
