"""
=============================================================
STEP 4: SQL BUSINESS ANALYSIS — RUN QUERIES & EXPORT RESULTS
Netflix Data Engineering Project
=============================================================

CONCEPT:
--------
Now that data lives in SQLite, we use SQL to answer business questions.
SQL (Structured Query Language) is the universal language for databases.
It's used by EVERY major data tool: MySQL, PostgreSQL, BigQuery, Snowflake.

HOW WE RUN SQL IN PYTHON:
  pd.read_sql(query, connection)
  → Sends query to the database
  → Gets results back as a pandas DataFrame
  → You can then print, visualize, or save the results

BUSINESS QUESTIONS WE'LL ANSWER:
  1.  How many total titles?
  2.  Movies vs TV Shows split?
  3.  Which countries produce most content?
  4.  How has content grown over the years?
  5.  What are the most common ratings?
  6.  Who are the top directors?
  7.  What genres are most popular?
  8.  KPI summary for the executive team
=============================================================
"""

import pandas as pd
import sqlite3
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("output/pipeline.log", mode="a")
    ]
)
logger = logging.getLogger(__name__)

DB_PATH = "output/netflix.db"
OUTPUT  = "output/"


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: run_query()
# PURPOSE: Execute a SQL query and return results as a DataFrame
# This is a REUSABLE helper — every analysis function calls this
# ══════════════════════════════════════════════════════════════════════════════
def run_query(conn: sqlite3.Connection, query: str, description: str = "") -> pd.DataFrame:
    """
    Execute a SQL query and return results as a pandas DataFrame.

    Args:
        conn        : Active SQLite connection
        query       : SQL query string
        description : Human-readable label for logging
    Returns:
        pd.DataFrame: Query results
    """
    if description:
        logger.info(f"Running query: {description}")

    try:
        # pd.read_sql() → sends SQL to the database, returns a DataFrame
        df_result = pd.read_sql(query, conn)
        return df_result
    except Exception as e:
        logger.error(f"Query failed [{description}]: {e}")
        raise


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: analyze_kpis()
# ══════════════════════════════════════════════════════════════════════════════
def analyze_kpis(conn: sqlite3.Connection) -> pd.DataFrame:
    """Get high-level KPI metrics."""
    query = """
    SELECT
        COUNT(*)                                               AS total_titles,
        SUM(CASE WHEN type = 'Movie'   THEN 1 ELSE 0 END)    AS total_movies,
        SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END)    AS total_tv_shows,
        COUNT(DISTINCT country)                               AS unique_countries,
        COUNT(DISTINCT director)                              AS unique_directors,
        MIN(release_year)                                     AS oldest_year,
        MAX(release_year)                                     AS newest_year,
        ROUND(AVG(content_age), 1)                           AS avg_content_age_yrs
    FROM netflix_titles
    """
    return run_query(conn, query, "KPI Summary")


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: analyze_content_type()
# ══════════════════════════════════════════════════════════════════════════════
def analyze_content_type(conn: sqlite3.Connection) -> pd.DataFrame:
    """Movies vs TV Shows distribution."""
    query = """
    SELECT
        type                                                                        AS content_type,
        COUNT(*)                                                                    AS total,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2)         AS percentage
    FROM netflix_titles
    GROUP BY type
    ORDER BY total DESC
    """
    return run_query(conn, query, "Content Type Distribution")


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: analyze_top_countries()
# ══════════════════════════════════════════════════════════════════════════════
def analyze_top_countries(conn: sqlite3.Connection, limit: int = 10) -> pd.DataFrame:
    """Top producing countries."""
    query = f"""
    SELECT
        country,
        COUNT(*)                                                              AS total_titles,
        SUM(CASE WHEN type = 'Movie'   THEN 1 ELSE 0 END)                    AS movies,
        SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END)                    AS tv_shows
    FROM netflix_titles
    WHERE country NOT IN ('Not Available', '')
    GROUP BY country
    ORDER BY total_titles DESC
    LIMIT {limit}
    """
    return run_query(conn, query, f"Top {limit} Countries")


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: analyze_content_per_year()
# ══════════════════════════════════════════════════════════════════════════════
def analyze_content_per_year(conn: sqlite3.Connection) -> pd.DataFrame:
    """Content added to Netflix per year."""
    query = """
    SELECT
        added_year,
        COUNT(*)                                                             AS total_added,
        SUM(CASE WHEN type = 'Movie'   THEN 1 ELSE 0 END)                   AS movies_added,
        SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END)                   AS shows_added
    FROM netflix_titles
    WHERE added_year IS NOT NULL
      AND added_year >= 2008
    GROUP BY added_year
    ORDER BY added_year ASC
    """
    return run_query(conn, query, "Content Added Per Year")


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: analyze_ratings()
# ══════════════════════════════════════════════════════════════════════════════
def analyze_ratings(conn: sqlite3.Connection) -> pd.DataFrame:
    """Most common content ratings."""
    query = """
    SELECT
        rating,
        COUNT(*) AS count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS pct
    FROM netflix_titles
    GROUP BY rating
    ORDER BY count DESC
    """
    return run_query(conn, query, "Rating Distribution")


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: analyze_top_directors()
# ══════════════════════════════════════════════════════════════════════════════
def analyze_top_directors(conn: sqlite3.Connection, limit: int = 15) -> pd.DataFrame:
    """Top directors by number of titles."""
    query = f"""
    SELECT
        director,
        COUNT(*)                                  AS titles_count,
        GROUP_CONCAT(DISTINCT type)               AS content_types,
        MIN(release_year)                         AS first_title_year,
        MAX(release_year)                         AS latest_title_year
    FROM netflix_titles
    WHERE director NOT IN ('Not Available', '')
    GROUP BY director
    ORDER BY titles_count DESC
    LIMIT {limit}
    """
    return run_query(conn, query, f"Top {limit} Directors")


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: analyze_top_genres()
# ══════════════════════════════════════════════════════════════════════════════
def analyze_top_genres(conn: sqlite3.Connection) -> pd.DataFrame:
    """Top genres (pre-computed in summary table)."""
    query = """
    SELECT genre, count
    FROM summary_by_genre
    ORDER BY count DESC
    LIMIT 15
    """
    return run_query(conn, query, "Top Genres")


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: analyze_monthly_additions()
# ══════════════════════════════════════════════════════════════════════════════
def analyze_monthly_additions(conn: sqlite3.Connection) -> pd.DataFrame:
    """Which months see most content additions?"""
    query = """
    SELECT
        added_month,
        added_month_name,
        COUNT(*) AS total_added
    FROM netflix_titles
    WHERE added_month IS NOT NULL
    GROUP BY added_month, added_month_name
    ORDER BY added_month ASC
    """
    return run_query(conn, query, "Monthly Additions")


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: analyze_duration_categories()
# ══════════════════════════════════════════════════════════════════════════════
def analyze_duration_categories(conn: sqlite3.Connection) -> pd.DataFrame:
    """Duration category breakdown."""
    query = """
    SELECT
        type,
        duration_category,
        COUNT(*) AS count
    FROM netflix_titles
    GROUP BY type, duration_category
    ORDER BY type, count DESC
    """
    return run_query(conn, query, "Duration Categories")


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION: export_to_excel()
# PURPOSE: Save all analysis results to a single multi-sheet Excel file
# EACH QUERY RESULT → one Excel sheet
# ══════════════════════════════════════════════════════════════════════════════
def export_to_excel(results: dict, output_path: str) -> str:
    """
    Export all analysis DataFrames to a single Excel workbook.

    Args:
        results     : Dictionary of {sheet_name: DataFrame}
        output_path : Folder path for output
    Returns:
        str: Path to saved Excel file
    """
    os.makedirs(output_path, exist_ok=True)
    file_path = os.path.join(output_path, "netflix_analysis.xlsx")

    # pd.ExcelWriter manages writing multiple sheets to one Excel file
    # engine='openpyxl' is the modern Excel writer engine
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        for sheet_name, df_result in results.items():
            # Each DataFrame becomes a separate sheet
            df_result.to_excel(
                writer,
                sheet_name=sheet_name[:31],  # Excel limits sheet names to 31 chars
                index=False                   # Don't write row numbers
            )
            logger.info(f"  Written sheet: {sheet_name} ({len(df_result)} rows)")

    logger.info(f"Analysis exported to: {file_path}")
    return file_path


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    logger.info("===== STEP 4: SQL ANALYSIS & EXPORT STARTED =====")

    conn = sqlite3.connect(DB_PATH)

    try:
        # Run all analysis functions
        kpis            = analyze_kpis(conn)
        content_type    = analyze_content_type(conn)
        top_countries   = analyze_top_countries(conn)
        per_year        = analyze_content_per_year(conn)
        ratings         = analyze_ratings(conn)
        top_directors   = analyze_top_directors(conn)
        top_genres      = analyze_top_genres(conn)
        monthly         = analyze_monthly_additions(conn)
        duration_cats   = analyze_duration_categories(conn)

        # ── Print results to console ──────────────────────────────────────────
        print("\n" + "="*60)
        print("         NETFLIX BUSINESS ANALYSIS RESULTS")
        print("="*60)

        print("\n📊 KPIs:")
        print(kpis.to_string(index=False))

        print("\n🎬 MOVIES vs TV SHOWS:")
        print(content_type.to_string(index=False))

        print("\n🌍 TOP 10 COUNTRIES:")
        print(top_countries.to_string(index=False))

        print("\n📅 CONTENT ADDED PER YEAR:")
        print(per_year.to_string(index=False))

        print("\n⭐ RATINGS:")
        print(ratings.to_string(index=False))

        print("\n🎥 TOP 15 DIRECTORS:")
        print(top_directors.to_string(index=False))

        print("\n🎭 TOP 15 GENRES:")
        print(top_genres.to_string(index=False))

        print("\n📆 MONTHLY ADDITIONS:")
        print(monthly.to_string(index=False))

        # ── Export to Excel ───────────────────────────────────────────────────
        results_dict = {
            "KPI_Summary"        : kpis,
            "Content_Type"       : content_type,
            "Top_Countries"      : top_countries,
            "Content_Per_Year"   : per_year,
            "Ratings"            : ratings,
            "Top_Directors"      : top_directors,
            "Top_Genres"         : top_genres,
            "Monthly_Additions"  : monthly,
            "Duration_Categories": duration_cats,
        }

        excel_path = export_to_excel(results_dict, OUTPUT)
        print(f"\n✅ Analysis exported to: {excel_path}")

    finally:
        conn.close()
        logger.info("Database connection closed.")

    logger.info("===== STEP 4 COMPLETED SUCCESSFULLY =====\n")
