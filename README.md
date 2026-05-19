## Setup

### 1. Clone the repository
```bash
git clone https://github.com/sosina14/fintech-review-analytics.git
cd fintech-review-analytics
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

### 3. PostgreSQL Database Setup

#### Install PostgreSQL
- Download PostgreSQL 17 from https://www.postgresql.org/download/
- During installation set password to: `postgres123`
- Keep default port: `5432`

#### Create the database
```bash
psql -U postgres -c "CREATE DATABASE bank_reviews;"
```
Or use pgAdmin to create a database named `bank_reviews`.

#### Database Schema
Two tables are created automatically by the setup script:

**banks table:**
| Column   | Type         | Description          |
|----------|--------------|----------------------|
| bank_id  | SERIAL PK    | Auto-increment ID    |
| bank_name| VARCHAR(255) | Name of the bank     |
| app_name | VARCHAR(255) | Google Play app ID   |

**reviews table:**
| Column           | Type         | Description              |
|------------------|--------------|--------------------------|
| review_id        | SERIAL PK    | Auto-increment ID        |
| bank_id          | INTEGER FK   | References banks table   |
| review_text      | TEXT         | Raw review content       |
| rating           | INTEGER      | Star rating (1-5)        |
| review_date      | DATE         | Date of review           |
| sentiment_label  | VARCHAR(50)  | positive/neutral/negative|
| sentiment_score  | FLOAT        | VADER compound score     |
| identified_theme | VARCHAR(100) | Theme category           |
| source           | VARCHAR(100) | Google Play              |

#### Run the database setup script
```bash
python scripts/database_setup.py
```

This will:
- Create both tables automatically
- Insert all three banks
- Insert 1,141 reviews
- Run verification queries

#### Verification queries
```sql
-- Count reviews per bank
SELECT b.bank_name, COUNT(r.review_id)
FROM banks b
LEFT JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_name;

-- Average rating per bank
SELECT b.bank_name, ROUND(AVG(r.rating)::numeric, 2)
FROM banks b
LEFT JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_name;
```

## Run Pipeline

### Step 1 — Scrape reviews
```bash
python -X utf8 scripts/scrape_reviews.py
```

### Step 2 — Sentiment and thematic analysis
```bash
python -X utf8 scripts/sentiment_analysis.py
```

### Step 3 — Database insertion
```bash
python scripts/database_setup.py
```

## Results
- 1,141 reviews collected across 3 banks
- 100% sentiment coverage
- 5 themes identified per bank
- 0 null values in key columns

## Database Results
| Bank | Reviews | Avg Rating |
|------|---------|------------|
| Commercial Bank of Ethiopia | 354 | 3.89 |
| Dashen Bank | 404 | 3.78 |
| Bank of Abyssinia | 383 | 3.30 |
EOF