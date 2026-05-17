"""
Script to scrape Google Play Store reviews for three Ethiopian banks.
Banks: Commercial Bank of Ethiopia, Bank of Abyssinia, Dashen Bank
"""

from google_play_scraper import reviews, Sort
import pandas as pd
import os
from datetime import datetime

# ── App IDs from Google Play Store ─────────────────────────────
APPS = {
    'Commercial Bank of Ethiopia': 'com.combanketh.mobilebanking',
    'Bank of Abyssinia':           'com.boa.boaMobileBanking',
    'Dashen Bank':                 'com.dashen.dashensmart',
}

def scrape_bank_reviews(bank_name, app_id, count=500):
    """Scrape reviews for a single bank app."""
    print(f"\nScraping {bank_name}...")
    try:
        result, _ = reviews(
            app_id,
            lang='en',
            country='et',
            sort=Sort.NEWEST,
            count=count,
        )
        # also try with 'us' country if not enough
        if len(result) < 400:
            result2, _ = reviews(
                app_id,
                lang='en',
                country='us',
                sort=Sort.NEWEST,
                count=count,
            )
            result.extend(result2)

        df = pd.DataFrame(result)
        df['bank'] = bank_name
        df['source'] = 'Google Play'
        print(f"  Collected {len(df)} reviews for {bank_name}")
        return df

    except Exception as e:
        print(f"  Error scraping {bank_name}: {e}")
        return pd.DataFrame()


def preprocess(df):
    """Clean and normalize the scraped data."""

    # Keep only needed columns
    df = df[['content', 'score', 'at', 'bank', 'source']].copy()

    # Rename columns
    df.rename(columns={
        'content': 'review',
        'score':   'rating',
        'at':      'date',
    }, inplace=True)

    print(f"\nBefore cleaning: {len(df)} rows")

    # Remove duplicates
    before = len(df)
    df.drop_duplicates(subset=['review', 'bank'], inplace=True)
    print(f"Removed {before - len(df)} duplicates")

    # Handle missing values
    missing_review = df['review'].isna().sum()
    missing_rating = df['rating'].isna().sum()
    print(f"Missing reviews: {missing_review}, Missing ratings: {missing_rating}")
    df.dropna(subset=['review', 'rating'], inplace=True)

    # Normalize dates to YYYY-MM-DD
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

    # Ensure correct column order
    df = df[['review', 'rating', 'date', 'bank', 'source']]

    print(f"After cleaning: {len(df)} rows")
    return df


def main():
    all_reviews = []

    for bank_name, app_id in APPS.items():
        df = scrape_bank_reviews(bank_name, app_id, count=500)
        if not df.empty:
            all_reviews.append(df)

    # Combine all banks
    combined = pd.concat(all_reviews, ignore_index=True)

    # Preprocess
    cleaned = preprocess(combined)

    # Summary
    print("\n=== Scraping Summary ===")
    print(cleaned['bank'].value_counts())
    print(f"\nTotal reviews: {len(cleaned)}")
    print(f"Missing data: {cleaned.isnull().sum().sum()}")
    print(f"Missing %: {cleaned.isnull().sum().sum() / (len(cleaned) * len(cleaned.columns)) * 100:.2f}%")

    # Save to data folder
    os.makedirs('data', exist_ok=True)
    output_path = 'data/bank_reviews.csv'
    cleaned.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")
    print(cleaned.head())


if __name__ == '__main__':
    main()