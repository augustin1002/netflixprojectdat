# 🎬 Netflix Data Engineering Project

## End-to-End Data Pipeline | Python · Pandas · SQLite · SQL · Excel

---

## 📋 Project Overview

This project demonstrates a complete **Data Engineering pipeline** built on the Netflix Titles dataset. It follows real-world data engineering practices including modular code, logging, error handling, ETL architecture, SQL analytics, and automated reporting.

---

## 🗂️ Project Structure

```
Netflix_Data_Engineering_Project/
│
├── data/
│   └── netflix_titles.xlsx          ← Raw input dataset
│
├── scripts/
│   ├── step1_ingest_and_profile.py  ← Data loading & profiling
│   ├── step2_clean_transform.py     ← Data cleaning & enrichment
│   ├── step3_etl_load.py            ← ETL → SQLite database
│   ├── step4_sql_analysis.py        ← SQL business queries + Excel export
│   ├── step5_dashboard.py           ← Excel dashboard builder
│   └── run_pipeline.py              ← Master pipeline runner (runs all steps)
│
├── output/
│   ├── netflix_cleaned.csv          ← Cleaned dataset (CSV)
│   ├── netflix_cleaned.xlsx         ← Cleaned dataset (Excel)
│   ├── netflix.db                   ← SQLite database
│   ├── netflix_analysis.xlsx        ← SQL analysis results (multi-sheet)
│   └── pipeline.log                 ← Full execution log
│
├── dashboard/
│   └── Netflix_Dashboard.xlsx       ← Excel dashboard with charts & KPIs
│
├── sql/
│   └── business_queries.sql         ← All SQL queries (standalone)
│
└── README.md                        ← This file
```

---

## 🚀 How to Run

### Prerequisites
```bash
pip install pandas numpy openpyxl sqlite3
```

### Run the Full Pipeline (All Steps)
```bash
cd Netflix_Data_Engineering_Project
python scripts/run_pipeline.py
```

### Run Individual Steps
```bash
# Step 1: Ingest & Profile
python scripts/step1_ingest_and_profile.py

# Step 2: Clean & Transform
python scripts/step2_clean_transform.py

# Step 3: ETL → SQLite
python scripts/step3_etl_load.py

# Step 4: SQL Analysis
python scripts/step4_sql_analysis.py

# Step 5: Dashboard
python scripts/step5_dashboard.py
```

---

## 📊 Dataset Information

| Attribute    | Value                            |
|-------------|----------------------------------|
| Source       | Netflix Titles Dataset           |
| Format       | Excel (.xlsx)                    |
| Total Rows   | ~8,801                           |
| Columns      | 12 (original) → 17 (after enrichment) |
| Date Range   | 2008 – 2021                      |

### Original Columns
| Column       | Description                     |
|-------------|----------------------------------|
| show_id     | Unique identifier (s1, s2...)    |
| type        | Movie or TV Show                 |
| title       | Title of the content             |
| director    | Director name(s)                 |
| cast        | Main cast members                |
| country     | Country of production            |
| DateAdded   | Date added to Netflix            |
| release_year| Year of original release         |
| rating      | Content rating (PG, TV-MA...)    |
| duration    | Length in minutes or seasons     |
| listed_in   | Genres                           |
| description | Plot summary                     |

### Engineered Columns (Added)
| Column            | Description                            |
|------------------|----------------------------------------|
| date_added       | Renamed + proper datetime format        |
| added_year       | Year extracted from date_added          |
| added_month      | Month number (1–12)                     |
| added_month_name | Month name (January, February...)       |
| content_age      | Current year – release_year             |
| duration_category| Short Film / Standard / Long-Running... |

---

## 🗄️ Database Tables

| Table                | Description                              |
|---------------------|------------------------------------------|
| netflix_titles       | Full cleaned dataset                     |
| netflix_movies       | Movies only                              |
| netflix_tvshows      | TV Shows only                            |
| summary_by_year      | Content count per year                   |
| summary_by_country   | Top 20 producing countries               |
| summary_by_rating    | Rating distribution                      |
| summary_by_genre     | Top 20 genres                            |
| summary_top_directors| Top 20 most prolific directors           |

---

## 📈 Business Questions Answered

1. ❓ How many total titles does Netflix have?
2. ❓ What is the Movies vs TV Shows split?
3. ❓ Which countries produce the most content?
4. ❓ How has Netflix's library grown year over year?
5. ❓ What are the most common content ratings?
6. ❓ Who are the top directors on Netflix?
7. ❓ What genres are most popular?
8. ❓ Which months see the most new additions?
9. ❓ How old is the average Netflix content?
10. ❓ What's the year-over-year content growth rate?

---

## 🛠️ Technologies Used

| Tool       | Purpose                                    |
|-----------|---------------------------------------------|
| Python 3.x | Core programming language                  |
| Pandas     | Data manipulation and analysis             |
| NumPy      | Numerical operations                       |
| SQLite3    | Embedded relational database               |
| SQL        | Business analysis queries                  |
| openpyxl   | Excel file creation and formatting         |
| logging    | Pipeline monitoring and audit trail        |

---

## 🏗️ Data Engineering Concepts Demonstrated

- ✅ **ETL Pipeline** (Extract → Transform → Load)
- ✅ **Data Profiling** (shape, dtypes, nulls, distributions)
- ✅ **Data Cleaning** (nulls, unknowns, duplicates, dates)
- ✅ **Feature Engineering** (calculated columns)
- ✅ **Database Design** (main + subset + summary tables)
- ✅ **SQL Analytics** (GROUP BY, CASE WHEN, window functions)
- ✅ **Modular Code** (separate function per transformation)
- ✅ **Logging** (timestamped audit trail to file)
- ✅ **Error Handling** (try/except, FileNotFoundError)
- ✅ **Reporting Automation** (Excel export via code)

---

## 💼 Interview Q&A

### Data Engineering Fundamentals
**Q: What is an ETL pipeline?**
> Extract-Transform-Load. Extract = read raw data from a source. Transform = clean, validate, enrich. Load = write to destination (database, warehouse).

**Q: Why use SQLite over CSV for storing data?**
> SQLite supports SQL queries (filtering, grouping, joining), handles concurrent access better, enforces data types, and is far more efficient for analytical queries on large datasets.

**Q: What is data profiling?**
> Systematic examination of a dataset to understand its structure, content quality, completeness, and statistical properties before processing.

**Q: Why do we use logging instead of print()?**
> Logging includes timestamps, severity levels, and can write to files for audit trails. Print statements disappear when the script closes. Logs are permanent records.

**Q: What does `if __name__ == "__main__"` mean?**
> It ensures code only runs when you execute the file directly — not when another script imports it. This makes functions reusable across modules.

---

## 📌 Resume Description

**Netflix Data Engineering Project** | Python, Pandas, SQLite, SQL, Excel
- Designed and implemented an end-to-end ETL pipeline processing 8,800+ Netflix titles
- Applied data cleaning techniques: null handling, deduplication, date normalization, and feature engineering (5 new calculated columns)
- Built a SQLite database with 8 analytical tables and executed 12 SQL business queries
- Automated reporting by generating multi-sheet Excel analysis files and an interactive dashboard using openpyxl
- Followed Data Engineering best practices: modular functions, error handling, and pipeline logging

---

## 🔗 LinkedIn Post Template

> Just completed an End-to-End **Netflix Data Engineering Project**! 🎬
>
> Built a full ETL pipeline from scratch:
> 📥 Extracted 8,800+ rows from Excel
> 🔧 Cleaned & enriched data with Pandas (null handling, feature engineering)
> 🗄️ Loaded into SQLite database with 8 analytical tables
> 📊 Answered 10 business questions with SQL
> 📈 Generated an automated Excel dashboard with KPI cards, bar, line & pie charts
>
> Tech stack: #Python #Pandas #SQLite #SQL #openpyxl #DataEngineering
>
> Full project available on GitHub → [link]
>
> #DataEngineering #DataAnalytics #Netflix #Portfolio #Python

---

*Built as a beginner-to-intermediate Data Engineering portfolio project.*
