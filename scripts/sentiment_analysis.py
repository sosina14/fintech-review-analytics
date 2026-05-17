# -*- coding: utf-8 -*-
"""
Task 2: Sentiment and Thematic Analysis
Analyzes Google Play Store reviews for three Ethiopian banks.
Uses VADER for sentiment analysis and TF-IDF for thematic analysis.
"""

import os
import re
import pandas as pd
import numpy as np
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk

# Download required NLTK data
nltk.download('vader_lexicon', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('punkt_tab', quiet=True)

# ── Tool Selection Rationale ────────────────────────────────────
# VADER is chosen over TextBlob and DistilBERT because:
# 1. Designed for short texts like app reviews
# 2. No GPU required — runs on any machine
# 3. Fast processing for 1000+ reviews
# 4. Handles financial/banking language well
# 5. Produces confidence scores (compound score)
# DistilBERT would require significant compute resources
# ───────────────────────────────────────────────────────────────

# ── Theme Definitions ───────────────────────────────────────────
# Themes are defined by keyword groups based on common banking app issues
THEME_KEYWORDS = {
    'Account Access Issues': [
        'login', 'password', 'locked', 'access', 'otp', 'pin',
        'authentication', 'sign', 'logout', 'session', 'expired'
    ],
    'Transaction Performance': [
        'transfer', 'transaction', 'slow', 'fast', 'payment',
        'send', 'receive', 'money', 'delay', 'failed', 'error',
        'loading', 'crash', 'freeze', 'stuck'
    ],
    'UI and Design': [
        'interface', 'design', 'ui', 'update', 'button', 'screen',
        'easy', 'simple', 'navigation', 'user', 'friendly', 'layout',
        'feature', 'app', 'new', 'old', 'version'
    ],
    'Customer Support': [
        'support', 'service', 'customer', 'help', 'response',
        'staff', 'agent', 'call', 'contact', 'feedback', 'complaint',
        'solve', 'fix', 'issue', 'problem'
    ],
    'Feature Requests': [
        'add', 'need', 'want', 'wish', 'please', 'request',
        'improve', 'better', 'option', 'functionality', 'missing',
        'balance', 'statement', 'notification', 'fingerprint', 'biometric'
    ],
}


def load_data(path='data/bank_reviews.csv'):
    """Load the scraped reviews dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    df = pd.read_csv(path, encoding='utf-8-sig')
    df = df.dropna(subset=['review', 'rating'])
    df['review_id'] = range(1, len(df) + 1)
    print(f"Loaded {len(df)} reviews")
    print(df['bank'].value_counts().to_string())
    return df


def preprocess_text(text):
    """
    Tokenize, remove stopwords, and lemmatize review text.
    Returns cleaned text string.
    """
    if not isinstance(text, str):
        return ''

    # Lowercase
    text = text.lower()

    # Remove special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)

    # Tokenize
    tokens = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [t for t in tokens if t not in stop_words and len(t) > 2]

    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(t) for t in tokens]

    return ' '.join(tokens)


def analyze_sentiment(df):
    """
    Apply VADER sentiment analysis to each review.
    Returns df with sentiment_label and sentiment_score columns.
    """
    sia = SentimentIntensityAnalyzer()

    def get_sentiment(text):
        if not isinstance(text, str):
            return 0.0
        return sia.polarity_scores(str(text))['compound']

    def label_sentiment(score):
        if score >= 0.05:
            return 'positive'
        elif score <= -0.05:
            return 'negative'
        return 'neutral'

    df['sentiment_score'] = df['review'].apply(get_sentiment)
    df['sentiment_label'] = df['sentiment_score'].apply(label_sentiment)

    print("\n=== Sentiment Distribution ===")
    print(df['sentiment_label'].value_counts().to_string())

    print("\n=== Sentiment by Bank ===")
    bank_sentiment = df.groupby('bank')['sentiment_score'].mean().round(4)
    print(bank_sentiment.to_string())

    print("\n=== Mean Sentiment by Star Rating ===")
    rating_sentiment = df.groupby('rating')['sentiment_score'].mean().round(4)
    print(rating_sentiment.to_string())

    return df


def identify_theme(text):
    """
    Assign a theme to a review based on keyword matching.
    Returns the most matching theme name.
    """
    if not isinstance(text, str):
        return 'General'

    text_lower = text.lower()
    theme_scores = {}

    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        theme_scores[theme] = score

    best_theme = max(theme_scores, key=theme_scores.get)

    # If no keywords matched, return General
    if theme_scores[best_theme] == 0:
        return 'General'

    return best_theme


def extract_tfidf_keywords(df, bank_name, top_n=15):
    """Extract top TF-IDF keywords for a specific bank."""
    bank_reviews = df[df['bank'] == bank_name]['cleaned_review'].dropna()
    bank_reviews = bank_reviews[bank_reviews.str.strip() != '']

    if len(bank_reviews) < 5:
        return pd.DataFrame()

    tfidf = TfidfVectorizer(
        max_features=50,
        stop_words='english',
        ngram_range=(1, 2)
    )

    matrix = tfidf.fit_transform(bank_reviews)
    scores = pd.DataFrame({
        'keyword': tfidf.get_feature_names_out(),
        'score': matrix.sum(axis=0).A1
    }).sort_values('score', ascending=False)

    return scores.head(top_n)


def thematic_analysis(df):
    """Run full thematic analysis on reviews."""

    # Clean text for TF-IDF
    print("\nPreprocessing text...")
    df['cleaned_review'] = df['review'].apply(preprocess_text)

    # Assign themes
    df['identified_theme'] = df['review'].apply(identify_theme)

    print("\n=== Theme Distribution ===")
    print(df['identified_theme'].value_counts().to_string())

    print("\n=== Themes by Bank ===")
    theme_bank = df.groupby(['bank', 'identified_theme']).size().unstack(fill_value=0)
    print(theme_bank.to_string())

    # TF-IDF keywords per bank
    print("\n=== Top Keywords per Bank (TF-IDF) ===")
    for bank in df['bank'].unique():
        print(f"\n--- {bank} ---")
        keywords = extract_tfidf_keywords(df, bank, top_n=10)
        if not keywords.empty:
            print(keywords.to_string(index=False))

    return df


def save_results(df, path='data/review_analysis.csv'):
    """Save analysis results to CSV."""
    output = df[[
        'review_id', 'review', 'rating', 'date', 'bank', 'source',
        'sentiment_label', 'sentiment_score', 'identified_theme'
    ]].copy()

    os.makedirs('data', exist_ok=True)
    output.to_csv(path, index=False, encoding='utf-8-sig')
    print(f"\nResults saved to {path}")
    print(f"Total reviews analyzed: {len(output)}")
    coverage = (output['sentiment_label'].notna().sum() / len(output)) * 100
    print(f"Sentiment coverage: {coverage:.1f}%")


def main():
    print("=" * 50)
    print("Task 2: Sentiment and Thematic Analysis")
    print("=" * 50)

    # Load data
    df = load_data('data/bank_reviews.csv')

    # Sentiment analysis
    print("\n--- Running Sentiment Analysis ---")
    df = analyze_sentiment(df)

    # Thematic analysis
    print("\n--- Running Thematic Analysis ---")
    df = thematic_analysis(df)

    # Save results
    save_results(df)

    print("\nDone!")


if __name__ == '__main__':
    main()
