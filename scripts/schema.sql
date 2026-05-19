-- ============================================================
-- Schema: bank_reviews
-- Description: Stores scraped and analyzed bank app reviews
-- Author: Sosina Ayele
-- ============================================================

-- Banks table
CREATE TABLE IF NOT EXISTS banks (
    bank_id     SERIAL PRIMARY KEY,
    bank_name   VARCHAR(255) NOT NULL UNIQUE,
    app_name    VARCHAR(255)
);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    review_id        SERIAL PRIMARY KEY,
    bank_id          INTEGER REFERENCES banks(bank_id),
    review_text      TEXT,
    rating           INTEGER CHECK (rating BETWEEN 1 AND 5),
    review_date      DATE,
    sentiment_label  VARCHAR(50),
    sentiment_score  FLOAT,
    identified_theme VARCHAR(100),
    source           VARCHAR(100)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_reviews_bank_id ON reviews(bank_id);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON reviews(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(review_date);

-- ── Verification Queries ────────────────────────────────────────

-- Count reviews per bank
SELECT b.bank_name, COUNT(r.review_id) as review_count
FROM banks b
LEFT JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_name
ORDER BY review_count DESC;

-- Average rating per bank
SELECT b.bank_name, ROUND(AVG(r.rating)::numeric, 2) as avg_rating
FROM banks b
LEFT JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_name
ORDER BY avg_rating DESC;

-- Sentiment distribution
SELECT sentiment_label, COUNT(*) as count
FROM reviews
GROUP BY sentiment_label
ORDER BY count DESC;

-- Check nulls in key columns
SELECT
    SUM(CASE WHEN review_text IS NULL THEN 1 ELSE 0 END) as null_reviews,
    SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) as null_ratings,
    SUM(CASE WHEN sentiment_label IS NULL THEN 1 ELSE 0 END) as null_sentiment
FROM reviews;
