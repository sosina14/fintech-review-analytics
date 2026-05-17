# Scraping Methodology

## Target Banks
- Commercial Bank of Ethiopia (com.combanketh.mobilebanking)
- Bank of Abyssinia (com.boa.boaMobileBanking)
- Dashen Bank (com.dashen.dashensmart)

## Tool Used
- google-play-scraper Python library
- Language: English
- Country: Ethiopia (et), fallback to US (us)
- Sort: Newest first
- Target: 500 reviews per bank

## Limitations
- Google Play Scraper may return fewer reviews than requested
  if the app has fewer English reviews available
- Reviews are limited to what Google Play exposes via its API
- Date range depends on app review history

## Output
- File: data/bank_reviews.csv (excluded from git via .gitignore)
- Columns: review, rating, date, bank, source
