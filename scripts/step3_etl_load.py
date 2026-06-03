"""
=============================================================
STEP 3: ETL PIPELINE — LOAD INTO SQLITE DATABASE
Netflix Data Engineering Project
=============================================================

CONCEPT: What is a Database?
------------------------------
A database is an organized collection of structured data.
Instead of a flat file (CSV/Excel), a database lets you:
  ✅ Query data with SQL (powerful filtering, grouping, joining)
  ✅ Handle large datasets efficiently
  ✅ Store multiple related tables
  ✅ Concurrent access by multiple users/applications

WHAT IS SQLite?
  - A lightweight, serverless database stored as a single .db file
  - No installation needed — Python has built-in support via sqlite3
  - Perfect for projects, prototypes, and small-to-medium datasets
  - Used in mobile apps, browsers (Firefox/Chrome use SQLite internally!)

ETL PIPELINE FLOW:
  ┌─────────────────────────────────────────────────────────┐
  │  EXTRACT        TRANSFORM           LOAD                │
  │  ─────────      ─────────────────   ──────────────────  │
  │  Read Excel  →  Clean + Enrich   →  Save to SQLite DB  │
  └─────────────────────────────────────────────────────────┘

TABLES WE'LL CREATE:
  1. netflix_titles     → Main cleaned dataset (all columns)
  2. netflix_movies     → Only Movies
  3. netflix_tvshows    → Only TV Shows
  4. summary_by_year    → Content count per year
  5. summary_by_country → Top countries
=============================================================
"""

import pandas as pd
import numpy as np
import sqlite3          # Built-in Python library for SQLite databases
import logging
import os
import sys
from datetime import datetime

# Re-import all cleaning functions from Step 2
# sys.path.insert ensures Python can find scripts in the same folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("output/pipeline.log", mode="a")
    ]
)
logger = logging.getLogger(__name__)

DATA_PATH = "data/netflix_titles.xlsx"
DB_PATH   = "output/netflix.db"
OUTPUT    = "output/"


# ══════════════════════════════════════════════════════════════════════════════
# RE-USE CLEANING FUNCTIONS (copied here for standalone execution)
# In a real project, these would be imported from step2_clean_transform.py
# ══════════════════════════════════════════════════════════════════════════════
def load_and_clean(file_path: str) -> pd.DataFrame:
    """
    Full pipeline: load + clean + enrich the Netflix dataset.
    This function chains all Step 2 transformations together.
    """
    logger.info("Running full load + clean pipeline...")

    df = pd.read_excel(file_path)

    # Rename columns to snake_case
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Replace 'Unknown' with NaN
    df.replace("Unknown", np.nan, inplace=True)

    # Fill NaN in text columns
    df["director"].fillna("Not Available", inplace=True)
    df["cast"].fillna("Not Available", inplace=True)
    df["country"].fillna("Not Available", inplace=True)
    df["rating"].fillna("Not Rated", inplace=True)

    # Drop duplicates
    df.drop_duplicates(subset=["show_id"], keep="first", inplace=True)

    # Fix dates
    df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce")

    # Calculated columns
    current_year = datetime.now().year
    df["added_year"]       = df["date_added"].dt.year
    df["added_month"]      = df["date_added"].dt.month
    df["added_month_name"] = df["date_added"].dt.month_name()
    df["content_age"]      = (current_year - df["release_year"]).clip(lower=0)

    def categorize_duration(row):
        try:
            val = int(str(row["duration"]).split()[0])
            if row["type"] == "Movie":
                if val < 60:   return "Short Film"
                elif val < 100: return "Standard"
                elif val < 150: return "Long Film"
                else:           return "Epic"
            elif row["type"] == "TV Show":
                if val == 1:   return "Mini-Series"
                elif val <= 3: return "Short Series"
                elif val <= 6: return "Medium Series"
                else:          return "Long-Running"
        except:
            return "Unknown"

    df["duration_category"] = df.apply(categorize_duration, axis=1)

    # Sort and reset index
    df.sort_values("date_added", ascending=True, na_position="first", inplace=True)
    df.reset_index(drop=True, inplace=True)

    logger.info(f"Cleaned data ready: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: create_db_connection()
# PURPOSE: Create (or connect to) a SQLite database file
#
# HOW SQLITE WORKS:
# - If the .db file EXISTS → connect to it (like opening an existing file)
# - If the .db file DOESN'T EXIST → creates a new one automatically
# - Returns a "connection" object — your gateway to run SQL commands
# ══════════════════════════════════════════════════════════════════════════════
def create_db_connection(db_path: str) -> sqlite3.Connection:
    """
    Create a SQLite database connection.

    Args:
        db_path (str): Path where the .db file will be created/opened
    Returns:
        sqlite3.Connection: Active database connection
    """
    logger.info(f"Connecting to SQLite database: {db_path}")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    try:
        # sqlite3.connect() creates or opens the .db file
        conn = sqlite3.connect(db_path)
        logger.info("Database connection established successfully.")
        return conn

    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: load_main_table()
# PURPOSE: Load the full cleaned DataFrame into a SQLite table
#
# df.to_sql() converts a pandas DataFrame directly into a SQL table.
# KEY PARAMETERS:
#   name        → table name in the database
#   con         → database connection
#   if_exists   → 'replace' (drop & recreate), 'append' (add rows), 'fail' (error)
#   index       → False (don't write row numbers as a column)
#   dtype       → Tell SQLite what data type each column is
# ══════════════════════════════════════════════════════════════════════════════
def load_main_table(df: pd.DataFrame, conn: sqlite3.Connection) -> None:
    """Load main cleaned dataset into SQLite as 'netflix_titles' table."""
    logger.info("Loading main table: netflix_titles...")

    # Convert datetime column to string for SQLite compatibility
    # SQLite doesn't have a native DATETIME type — store as ISO string "YYYY-MM-DD"
    df_copy = df.copy()
    df_copy["date_added"] = df_copy["date_added"].dt.strftime("%Y-%m-%d")

    df_copy.to_sql(
        name="netflix_titles",
        con=conn,
        if_exists="replace",    # Drop table if it exists, then recreate
        index=False             # Don't save the 0,1,2 index as a column
    )

    # Verify it loaded correctly
    count = pd.read_sql("SELECT COUNT(*) as cnt FROM netflix_titles", conn).iloc[0]["cnt"]
    logger.info(f"Loaded {count:,} rows into 'netflix_titles' table")


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: load_subset_tables()
# PURPOSE: Create specialized subset tables for faster querying
#
# ANALOGY: In a library, you have the main catalog (all books).
# But you also have separate sections: Fiction, Non-Fiction, Reference.
# Subset tables are like those sections — pre-filtered for speed.
# ══════════════════════════════════════════════════════════════════════════════
def load_subset_tables(df: pd.DataFrame, conn: sqlite3.Connection) -> None:
    """Create Movies and TV Shows subset tables."""

    # ── Movies Table ──────────────────────────────────────────────────────────
    df_movies = df[df["type"] == "Movie"].copy()
    df_movies["date_added"] = df_movies["date_added"].dt.strftime("%Y-%m-%d")
    df_movies.to_sql("netflix_movies", conn, if_exists="replace", index=False)
    logger.info(f"Loaded {len(df_movies):,} rows into 'netflix_movies' table")

    # ── TV Shows Table ────────────────────────────────────────────────────────
    df_tvshows = df[df["type"] == "TV Show"].copy()
    df_tvshows["date_added"] = df_tvshows["date_added"].dt.strftime("%Y-%m-%d")
    df_tvshows.to_sql("netflix_tvshows", conn, if_exists="replace", index=False)
    logger.info(f"Loaded {len(df_tvshows):,} rows into 'netflix_tvshows' table")


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: create_summary_tables()
# PURPOSE: Pre-aggregate data into summary tables for dashboards & reporting
#
# WHY PRE-AGGREGATE?
# Running GROUP BY on 8,800 rows every time a dashboard loads is wasteful.
# Pre-aggregated summary tables are tiny (10-20 rows) and load instantly.
# ══════════════════════════════════════════════════════════════════════════════
def create_summary_tables(df: pd.DataFrame, conn: sqlite3.Connection) -> None:
    """Create pre-aggregated summary tables."""
    logger.info("Creating summary tables...")

    # ── Summary: Content Added Per Year ──────────────────────────────────────
    # groupby("added_year") groups all rows with the same year together
    # .agg() applies multiple functions at once:
    #   "count" = total rows in group
    # reset_index() turns the group keys back into columns
    summary_year = (
        df.groupby("added_year", dropna=True)
        .agg(
            total_content=("show_id", "count"),
            movies=("type", lambda x: (x == "Movie").sum()),
            tv_shows=("type", lambda x: (x == "TV Show").sum())
        )
        .reset_index()
        .sort_values("added_year")
    )
    summary_year.to_sql("summary_by_year", conn, if_exists="replace", index=False)
    logger.info(f"Created 'summary_by_year' ({len(summary_year)} rows)")

    # ── Summary: Top Countries ────────────────────────────────────────────────
    # Some entries have multiple countries (e.g., "United States, UK")
    # We need to split by comma and count each country separately
    # explode() turns ["US", "UK"] → two separate rows
    country_series = (
        df["country"]
        .dropna()
        .apply(lambda x: [c.strip() for c in str(x).split(",")])  # Split by comma
    )
    # explode() flattens list-of-lists into individual rows
    country_flat = country_series.explode()
    # Filter out placeholder values
    country_flat = country_flat[~country_flat.isin(["Not Available", ""])]

    summary_country = (
        country_flat
        .value_counts()        # Count occurrences of each country
        .reset_index()
        .rename(columns={"index": "country", "country": "content_count"})
        .head(20)              # Top 20 countries
    )
    summary_country.columns = ["country", "content_count"]
    summary_country.to_sql("summary_by_country", conn, if_exists="replace", index=False)
    logger.info(f"Created 'summary_by_country' ({len(summary_country)} rows)")

    # ── Summary: Ratings Distribution ────────────────────────────────────────
    summary_rating = (
        df.groupby("rating", dropna=True)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    summary_rating.to_sql("summary_by_rating", conn, if_exists="replace", index=False)
    logger.info(f"Created 'summary_by_rating' ({len(summary_rating)} rows)")

    # ── Summary: Top Genres ───────────────────────────────────────────────────
    genre_series = (
        df["listed_in"]
        .dropna()
        .apply(lambda x: [g.strip() for g in str(x).split(",")])
    )
    genre_flat = genre_series.explode()
    summary_genre = (
        genre_flat
        .value_counts()
        .reset_index()
        .head(20)
    )
    summary_genre.columns = ["genre", "count"]
    summary_genre.to_sql("summary_by_genre", conn, if_exists="replace", index=False)
    logger.info(f"Created 'summary_by_genre' ({len(summary_genre)} rows)")

    # ── Summary: Top Directors ────────────────────────────────────────────────
    summary_directors = (
        df[df["director"] != "Not Available"]
        .groupby("director")
        .size()
        .reset_index(name="titles_directed")
        .sort_values("titles_directed", ascending=False)
        .head(20)
    )
    summary_directors.to_sql("summary_top_directors", conn, if_exists="replace", index=False)
    logger.info(f"Created 'summary_top_directors' ({len(summary_directors)} rows)")


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: verify_database()
# PURPOSE: List all tables and row counts to confirm load was successful
# ══════════════════════════════════════════════════════════════════════════════
def verify_database(conn: sqlite3.Connection) -> None:
    """Print all tables and their row counts."""
    logger.info("Verifying database contents...")

    # sqlite_master is a system table that stores the database schema
    tables_query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    tables = pd.read_sql(tables_query, conn)

    print("\n" + "="*50)
    print("       DATABASE VERIFICATION")
    print("="*50)
    print(f"{'Table Name':<30} {'Row Count':>10}")
    print("-"*42)

    for table_name in tables["name"]:
        count = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {table_name}", conn).iloc[0]["cnt"]
        print(f"   {table_name:<28} {count:>10,}")

    print("="*50)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    logger.info("===== STEP 3: ETL PIPELINE — LOAD TO DATABASE STARTED =====")

    # EXTRACT + TRANSFORM
    df_clean = load_and_clean(DATA_PATH)

    # LOAD
    conn = create_db_connection(DB_PATH)

    try:
        # Load main tables
        load_main_table(df_clean, conn)
        load_subset_tables(df_clean, conn)
        create_summary_tables(df_clean, conn)

        # Verify
        verify_database(conn)

        logger.info(f"Database saved to: {DB_PATH}")

    finally:
        # ALWAYS close the connection — even if errors occur
        # finally block runs no matter what (success or failure)
        conn.close()
        logger.info("Database connection closed.")

    logger.info("===== STEP 3 COMPLETED SUCCESSFULLY =====\n")
