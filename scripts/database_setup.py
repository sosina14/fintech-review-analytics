# -*- coding: utf-8 -*-
"""
Task 3: Database Setup and Data Insertion
Creates PostgreSQL schema and inserts cleaned review data.
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os

# ── Database Connection Config ──────────────────────────────────
DB_CONFIG = {
    'host':     'localhost',
    'port':     5432,
    'database': 'bank_reviews',
    'user':     'postgres',
    'password': 'postgres123',
}


def get_connection():
    """Create and return a database connection."""
    return psycopg2.connect(**DB_CONFIG)


def create_schema(conn):
    """Create banks and reviews tables."""
    cursor = conn.cursor()

    cursor.execute("""
        DROP TABLE IF EXISTS reviews;
        DROP TABLE IF EXISTS banks;
    """)

    cursor.execute("""
        CREATE TABLE banks (
            bank_id     SERIAL PRIMARY KEY,
            bank_name   VARCHAR(255) NOT NULL UNIQUE,
            app_name    VARCHAR(255)
        );
    """)

    cursor.execute("""
        CREATE TABLE reviews (
            review_id        SERIAL PRIMARY KEY,
            bank_id          INTEGER REFERENCES banks(bank_id),
            review_text      TEXT,
            rating           INTEGER,
            review_date      DATE,
            sentiment_label  VARCHAR(50),
            sentiment_score  FLOAT,
            identified_theme VARCHAR(100),
            source           VARCHAR(100)
        );
    """)

    conn.commit()
    print("Schema created successfully!")
    cursor.close()


def insert_banks(conn):
    """Insert bank metadata."""
    cursor = conn.cursor()

    banks = [
        ('Commercial Bank of Ethiopia', 'com.combanketh.mobilebanking'),
        ('Bank of Abyssinia',           'com.boa.boaMobileBanking'),
        ('Dashen Bank',                 'com.dashen.dashensuperapp'),
    ]

    execute_values(cursor, """
        INSERT INTO banks (bank_name, app_name)
        VALUES %s
        ON CONFLICT (bank_name) DO NOTHING
    """, banks)

    conn.commit()
    print("Banks inserted successfully!")
    cursor.close()


def insert_reviews(conn, df):
    """Insert reviews into the database."""
    cursor = conn.cursor()

    # Get bank_id mapping
    cursor.execute("SELECT bank_id, bank_name FROM banks")
    bank_map = {name: bid for bid, name in cursor.fetchall()}

    records = []
    for _, row in df.iterrows():
        bank_id = bank_map.get(row['bank'])
        if bank_id is None:
            continue

        records.append((
            bank_id,
            str(row['review'])[:2000] if pd.notna(row['review']) else None,
            int(row['rating']) if pd.notna(row['rating']) else None,
            str(row['date']) if pd.notna(row['date']) else None,
            str(row['sentiment_label']) if pd.notna(row.get('sentiment_label')) else None,
            float(row['sentiment_score']) if pd.notna(row.get('sentiment_score')) else None,
            str(row['identified_theme']) if pd.notna(row.get('identified_theme')) else None,
            str(row['source']) if pd.notna(row['source']) else None,
        ))

    execute_values(cursor, """
        INSERT INTO reviews
            (bank_id, review_text, rating, review_date,
             sentiment_label, sentiment_score, identified_theme, source)
        VALUES %s
    """, records)

    conn.commit()
    print(f"Inserted {len(records)} reviews successfully!")
    cursor.close()


def verify_data(conn):
    """Run verification queries."""
    cursor = conn.cursor()

    print("\n=== Reviews per Bank ===")
    cursor.execute("""
        SELECT b.bank_name, COUNT(r.review_id) as review_count
        FROM banks b
        LEFT JOIN reviews r ON b.bank_id = r.bank_id
        GROUP BY b.bank_name
        ORDER BY review_count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} reviews")

    print("\n=== Average Rating per Bank ===")
    cursor.execute("""
        SELECT b.bank_name, ROUND(AVG(r.rating)::numeric, 2) as avg_rating
        FROM banks b
        LEFT JOIN reviews r ON b.bank_id = r.bank_id
        GROUP BY b.bank_name
        ORDER BY avg_rating DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} stars")

    print("\n=== Sentiment Distribution ===")
    cursor.execute("""
        SELECT sentiment_label, COUNT(*) as count
        FROM reviews
        GROUP BY sentiment_label
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    print("\n=== Nulls in Key Columns ===")
    cursor.execute("""
        SELECT
            SUM(CASE WHEN review_text IS NULL THEN 1 ELSE 0 END) as null_reviews,
            SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) as null_ratings,
            SUM(CASE WHEN sentiment_label IS NULL THEN 1 ELSE 0 END) as null_sentiment
        FROM reviews
    """)
    row = cursor.fetchone()
    print(f"  Null reviews: {row[0]}")
    print(f"  Null ratings: {row[1]}")
    print(f"  Null sentiment: {row[2]}")

    cursor.close()


def main():
    print("=" * 50)
    print("Task 3: Database Setup and Data Insertion")
    print("=" * 50)

    # Load data — use analysis results if available
    data_paths = [
        'data/review_analysis.csv',
        'data/bank_reviews.csv',
    ]

    df = None
    for path in data_paths:
        if os.path.exists(path):
            df = pd.read_csv(path, encoding='utf-8-sig')
            print(f"Loaded data from: {path}")
            break

    if df is None:
        print("No data file found!")
        return

    print(f"Total rows: {len(df)}")

    # Connect
    print("\nConnecting to PostgreSQL...")
    conn = get_connection()
    print("Connected!")

    # Setup
    create_schema(conn)
    insert_banks(conn)
    insert_reviews(conn, df)
    verify_data(conn)

    conn.close()
    print("\nDone!")


if __name__ == '__main__':
    main()
