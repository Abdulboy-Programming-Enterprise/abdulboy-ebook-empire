-- =============================================================================
-- SEED: SAMPLE BOOKS
-- =============================================================================
-- Creates sample books for testing and demonstration
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Book 1: The African Writer's Journey (Free)
-- -----------------------------------------------------------------------------
INSERT INTO app.books (
    id,
    title,
    slug,
    description,
    author_name,
    price,
    is_free,
    total_pages,
    preview_pages,
    cover_image_url,
    language,
    status,
    published_at,
    created_at
) VALUES (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'The African Writer''s Journey',
    'african-writers-journey',
    'A comprehensive guide for aspiring African writers. Learn the art of storytelling, publishing strategies, and how to reach global audiences.',
    'Chinua Adebayo',
    0.00,
    true,
    250,
    50,
    '/images/books/covers/african-writers-journey.jpg',
    'en',
    'published',
    NOW(),
    NOW()
);

-- -----------------------------------------------------------------------------
-- Book 2: Python for Everyone (Paid)
-- -----------------------------------------------------------------------------
INSERT INTO app.books (
    id,
    title,
    slug,
    description,
    author_name,
    price,
    is_free,
    total_pages,
    preview_pages,
    cover_image_url,
    language,
    status,
    published_at,
    created_at
) VALUES (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'Python for Everyone: From Zero to Hero',
    'python-for-everyone',
    'Master Python programming from scratch. This book covers everything from basic syntax to advanced concepts like web development, data science, and machine learning.',
    'Dr. Ada Okonkwo',
    29.99,
    false,
    450,
    30,
    '/images/books/covers/python-for-everyone.jpg',
    'en',
    'published',
    NOW(),
    NOW()
);

-- -----------------------------------------------------------------------------
-- Book 3: Digital Marketing Mastery (Paid)
-- -----------------------------------------------------------------------------
INSERT INTO app.books (
    id,
    title,
    slug,
    description,
    author_name,
    price,
    is_free,
    total_pages,
    preview_pages,
    cover_image_url,
    language,
    status,
    published_at,
    created_at
) VALUES (
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'Digital Marketing Mastery: Grow Your Online Business',
    'digital-marketing-mastery',
    'Learn proven digital marketing strategies to grow your online business. Includes SEO, social media marketing, email marketing, and paid advertising.',
    'Sarah Johnson',
    39.99,
    false,
    ********, 35,
    '/images/books/covers/digital-marketing-mastery.jpg',
    'en',
    'published',
    NOW(),
    NOW()
);

-- -----------------------------------------------------------------------------
-- Book 4: Mindfulness for Busy People (Free)
-- -----------------------------------------------------------------------------
INSERT INTO app.books (
    id,
    title,
    slug,
    description,
    author_name,
    price,
    is_free,
    total_pages,
    preview_pages,
    cover_image_url,
    language,
    status,
    published_at,
    created_at
) VALUES (
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'Mindfulness for Busy People: 5-Minute Practices',
    'mindfulness-busy-people',
    'Simple mindfulness exercises that take just 5 minutes. Perfect for busy professionals and entrepreneurs who want to reduce stress and increase focus.',
    'Michael Chen',
    0.00,
    true,
    120,
    40,
    '/images/books/covers/mindfulness-busy-people.jpg',
    'en',
    'published',
    NOW(),
    NOW()
);

-- -----------------------------------------------------------------------------
-- Book 5: Financial Freedom (Paid)
-- -----------------------------------------------------------------------------
INSERT INTO app.books (
    id,
    title,
    slug,
    description,
    author_name,
    price,
    is_free,
    total_pages,
    preview_pages,
    cover_image_url,
    language,
    status,
    published_at,
    created_at
) VALUES (
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    'Financial Freedom: The African Investor''s Guide',
    'financial-freedom',
    'Build wealth and achieve financial independence. Tailored specifically for African markets with practical investment strategies.',
    'Olumide Adewale',
    49.99,
    false,
    380,
    40,
    '/images/books/covers/financial-freedom.jpg',
    'en',
    'published',
    NOW(),
    NOW()
);

-- -----------------------------------------------------------------------------
-- Add tags to books
-- -----------------------------------------------------------------------------
-- Insert tags
INSERT INTO app.tags (id, name, slug) VALUES
    ('11111111-aaaa-1111-aaaa-111111111111', 'Fiction', 'fiction'),
    ('22222222-bbbb-2222-bbbb-222222222222', 'Non-Fiction', 'non-fiction'),
    ('33333333-cccc-3333-cccc-333333333333', 'Programming', 'programming'),
    ('44444444-dddd-4444-dddd-444444444444', 'Marketing', 'marketing'),
    ('55555555-eeee-5555-eeee-555555555555', 'Self-Help', 'self-help'),
    ('66666666-ffff-6666-ffff-666666666666', 'Finance', 'finance'),
    ('77777777-gggg-7777-gggg-777777777777', 'Technology', 'technology')
ON CONFLICT (name) DO NOTHING;

-- Associate tags with books
-- Book 1: The African Writer's Journey
INSERT INTO app.book_tags (book_id, tag_id) VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '22222222-bbbb-2222-bbbb-222222222222'),
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '55555555-eeee-5555-eeee-555555555555');

-- Book 2: Python for Everyone
INSERT INTO app.book_tags (book_id, tag_id) VALUES
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '33333333-cccc-3333-cccc-333333333333'),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '77777777-gggg-7777-gggg-777777777777');

-- Book 3: Digital Marketing Mastery
INSERT INTO app.book_tags (book_id, tag_id) VALUES
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', '44444444-dddd-4444-dddd-444444444444'),
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', '22222222-bbbb-2222-bbbb-222222222222');

-- Book 4: Mindfulness for Busy People
INSERT INTO app.book_tags (book_id, tag_id) VALUES
    ('dddddddd-dddd-dddd-dddd-dddddddddddd', '55555555-eeee-5555-eeee-555555555555');

-- Book 5: Financial Freedom
INSERT INTO app.book_tags (book_id, tag_id) VALUES
    ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '66666666-ffff-6666-ffff-666666666666'),
    ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '22222222-bbbb-2222-bbbb-222222222222');

-- Output the created books
SELECT 
    title,
    author_name,
    price,
    status,
    published_at
FROM app.books
WHERE status = 'published'
ORDER BY created_at DESC;
