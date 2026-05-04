-- =============================================================================
-- SEED: BADGES AND GAMIFICATION
-- =============================================================================
-- Creates achievement badges for gamification system
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Reading Badges
-- -----------------------------------------------------------------------------
INSERT INTO app.badges (
    id,
    name,
    slug,
    description,
    image_url,
    criteria_type,
    criteria_value,
    points,
    rarity,
    is_active,
    created_at
) VALUES 
-- Book reading milestones
(
    'b1111111-b111-b111-b111-b11111111111',
    'First Chapter',
    'first-chapter',
    'Read your first book on the platform',
    '/images/badges/first-chapter.svg',
    'books_read',
    1,
    50,
    'common',
    true,
    NOW()
),
(
    'b2222222-b222-b222-b222-b22222222222',
    'Bookworm',
    'bookworm',
    'Read 10 books on the platform',
    '/images/badges/bookworm.svg',
    'books_read',
    10,
    200,
    'common',
    true,
    NOW()
),
(
    'b3333333-b333-b333-b333-b33333333333',
    'Voracious Reader',
    'voracious-reader',
    'Read 50 books on the platform',
    '/images/badges/voracious-reader.svg',
    'books_read',
    50,
    500,
    'rare',
    true,
    NOW()
),
(
    'b4444444-b444-b444-b444-b44444444444',
    'Library Master',
    'library-master',
    'Read 100 books on the platform',
    '/images/badges/library-master.svg',
    'books_read',
    100,
    1000,
    'epic',
    true,
    NOW()
),
(
    'b5555555-b555-b555-b555-b55555555555',
    'Legendary Reader',
    'legendary-reader',
    'Read 500 books on the platform',
    '/images/badges/legendary-reader.svg',
    'books_read',
    500,
    5000,
    'legendary',
    true,
    NOW()
),

-- -----------------------------------------------------------------------------
-- Streak Badges
-- -----------------------------------------------------------------------------
(
    'b6666666-b666-b666-b666-b66666666666',
    'Consistent Reader',
    'consistent-reader',
    'Maintain a 7-day reading streak',
    '/images/badges/consistent-reader.svg',
    'streak_days',
    7,
    100,
    'common',
    true,
    NOW()
),
(
    'b7777777-b777-b777-b777-b77777777777',
    'Dedicated Reader',
    'dedicated-reader',
    'Maintain a 30-day reading streak',
    '/images/badges/dedicated-reader.svg',
    'streak_days',
    30,
    500,
    'rare',
    true,
    NOW()
),
(
    'b8888888-b888-b888-b888-b88888888888',
    'Unstoppable',
    'unstoppable',
    'Maintain a 100-day reading streak',
    '/images/badges/unstoppable.svg',
    'streak_days',
    100,
    2000,
    'epic',
    true,
    NOW()
),
(
    'b9999999-b999-b999-b999-b99999999999',
    'Reading Champion',
    'reading-champion',
    'Maintain a 365-day reading streak',
    '/images/badges/reading-champion.svg',
    'streak_days',
    365,
    10000,
    'legendary',
    true,
    NOW()
),

-- -----------------------------------------------------------------------------
-- Purchase Badges
-- -----------------------------------------------------------------------------
(
    'c1111111-c111-c111-c111-c11111111111',
    'First Purchase',
    'first-purchase',
    'Make your first book purchase',
    '/images/badges/first-purchase.svg',
    'purchase_count',
    1,
    50,
    'common',
    true,
    NOW()
),
(
    'c2222222-c222-c222-c222-c22222222222',
    'Book Collector',
    'book-collector',
    'Purchase 10 books',
    '/images/badges/book-collector.svg',
    'purchase_count',
    10,
    200,
    'common',
    true,
    NOW()
),
(
    'c3333333-c333-c333-c333-c33333333333',
    'Bibliophile',
    'bibliophile',
    'Purchase 50 books',
    '/images/badges/bibliophile.svg',
    'purchase_count',
    50,
    1000,
    'rare',
    true,
    NOW()
),

-- -----------------------------------------------------------------------------
-- Review Badges
-- -----------------------------------------------------------------------------
(
    'c4444444-c444-c444-c444-c44444444444',
    'First Review',
    'first-review',
    'Write your first book review',
    '/images/badges/first-review.svg',
    'reviews_written',
    1,
    50,
    'common',
    true,
    NOW()
),
(
    'c5555555-c555-c555-c555-c55555555555',
    'Helpful Reviewer',
    'helpful-reviewer',
    'Write 25 book reviews',
    '/images/badges/helpful-reviewer.svg',
    'reviews_written',
    25,
    500,
    'rare',
    true,
    NOW()
),

-- -----------------------------------------------------------------------------
-- Points Badges
-- -----------------------------------------------------------------------------
(
    'c6666666-c666-c666-c666-c66666666666',
    'Point Gatherer',
    'point-gatherer',
    'Earn 1,000 total points',
    '/images/badges/point-gatherer.svg',
    'total_points',
    1000,
    0,
    'common',
    true,
    NOW()
),
(
    'c7777777-c777-c777-c777-c77777777777',
    'Point Master',
    'point-master',
    'Earn 10,000 total points',
    '/images/badges/point-master.svg',
    'total_points',
    10000,
    0,
    'rare',
    true,
    NOW()
),
(
    'c8888888-c888-c888-c888-c88888888888',
    'Point Legend',
    'point-legend',
    'Earn 100,000 total points',
    '/images/badges/point-legend.svg',
    'total_points',
    100000,
    0,
    'legendary',
    true,
    NOW()
),

-- -----------------------------------------------------------------------------
-- Special Badges
-- -----------------------------------------------------------------------------
(
    'c9999999-c999-c999-c999-c99999999999',
    'Early Adopter',
    'early-adopter',
    'Joined during the first month of launch',
    '/images/badges/early-adopter.svg',
    'special',
    0,
    1000,
    'epic',
    true,
    NOW()
);

-- Output the created badges
SELECT 
    name,
    rarity,
    points,
    criteria_type,
    criteria_value,
    is_active
FROM app.badges
ORDER BY points DESC;
