-- =============================================================
-- NETFLIX DATA ENGINEERING PROJECT
-- SQL BUSINESS ANALYSIS QUERIES
-- =============================================================
-- HOW TO USE:
--   1. Run the ETL pipeline first (step3_etl_load.py)
--   2. Open the database: sqlite3 output/netflix.db
--   3. Run these queries one by one, or use step4_sql_analysis.py
-- =============================================================


-- ─────────────────────────────────────────────────────────────
-- QUERY 1: TOTAL CONTENT COUNT
-- Count how many titles exist in total
-- COUNT(*) counts ALL rows — asterisk means "all columns"
-- ─────────────────────────────────────────────────────────────
SELECT COUNT(*) AS total_titles
FROM netflix_titles;


-- ─────────────────────────────────────────────────────────────
-- QUERY 2: TOTAL MOVIES vs TV SHOWS
-- GROUP BY type → groups all Movies together, all TV Shows together
-- COUNT(*) then counts within each group
-- ORDER BY total DESC → highest count first
-- ─────────────────────────────────────────────────────────────
SELECT
    type                AS content_type,
    COUNT(*)            AS total,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 1) AS percentage
FROM netflix_titles
GROUP BY type
ORDER BY total DESC;


-- ─────────────────────────────────────────────────────────────
-- QUERY 3: TOP 10 COUNTRIES BY CONTENT
-- LIKE '%,%' → filter to rows that have multiple countries
-- We'll handle multi-country via Python; here we count primary
-- ─────────────────────────────────────────────────────────────
SELECT
    country,
    COUNT(*) AS total_titles,
    SUM(CASE WHEN type = 'Movie'   THEN 1 ELSE 0 END) AS movies,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows
FROM netflix_titles
WHERE country NOT IN ('Not Available', '')
GROUP BY country
ORDER BY total_titles DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────
-- QUERY 4: CONTENT ADDED PER YEAR
-- Shows the growth of Netflix library over time
-- COALESCE returns first non-null value — handles NaN added_year
-- ─────────────────────────────────────────────────────────────
SELECT
    added_year,
    COUNT(*)  AS total_added,
    SUM(CASE WHEN type = 'Movie'   THEN 1 ELSE 0 END) AS movies_added,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS shows_added
FROM netflix_titles
WHERE added_year IS NOT NULL
GROUP BY added_year
ORDER BY added_year ASC;


-- ─────────────────────────────────────────────────────────────
-- QUERY 5: MOST COMMON RATINGS
-- Which content ratings are most prevalent?
-- ─────────────────────────────────────────────────────────────
SELECT
    rating,
    COUNT(*) AS total,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 1) AS pct
FROM netflix_titles
GROUP BY rating
ORDER BY total DESC;


-- ─────────────────────────────────────────────────────────────
-- QUERY 6: TOP 15 DIRECTORS
-- Who directed the most Netflix content?
-- WHERE director NOT IN → exclude placeholder values
-- ─────────────────────────────────────────────────────────────
SELECT
    director,
    COUNT(*) AS titles_directed,
    GROUP_CONCAT(DISTINCT type) AS content_types
FROM netflix_titles
WHERE director NOT IN ('Not Available', '')
GROUP BY director
ORDER BY titles_directed DESC
LIMIT 15;


-- ─────────────────────────────────────────────────────────────
-- QUERY 7: CONTENT ADDED BY MONTH (ALL YEARS COMBINED)
-- Which month does Netflix add most content?
-- ─────────────────────────────────────────────────────────────
SELECT
    added_month,
    added_month_name,
    COUNT(*) AS total_added
FROM netflix_titles
WHERE added_month IS NOT NULL
GROUP BY added_month, added_month_name
ORDER BY added_month ASC;


-- ─────────────────────────────────────────────────────────────
-- QUERY 8: DURATION CATEGORY DISTRIBUTION
-- How long is Netflix's typical content?
-- ─────────────────────────────────────────────────────────────
SELECT
    type,
    duration_category,
    COUNT(*) AS count
FROM netflix_titles
GROUP BY type, duration_category
ORDER BY type, count DESC;


-- ─────────────────────────────────────────────────────────────
-- QUERY 9: AVERAGE CONTENT AGE BY TYPE
-- ROUND(x, 1) → round to 1 decimal place
-- ─────────────────────────────────────────────────────────────
SELECT
    type,
    ROUND(AVG(content_age), 1) AS avg_age_years,
    MIN(content_age)           AS newest_content_age,
    MAX(content_age)           AS oldest_content_age
FROM netflix_titles
GROUP BY type;


-- ─────────────────────────────────────────────────────────────
-- QUERY 10: TOP 10 RELEASE YEARS (most content released)
-- ─────────────────────────────────────────────────────────────
SELECT
    release_year,
    COUNT(*) AS titles_released
FROM netflix_titles
GROUP BY release_year
ORDER BY titles_released DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────
-- QUERY 11: KPI SUMMARY (Single-row executive dashboard)
-- Combines multiple metrics into one row
-- ─────────────────────────────────────────────────────────────
SELECT
    COUNT(*)                                                    AS total_titles,
    SUM(CASE WHEN type = 'Movie'   THEN 1 ELSE 0 END)          AS total_movies,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END)          AS total_tv_shows,
    COUNT(DISTINCT country)                                     AS unique_countries,
    COUNT(DISTINCT director)                                    AS unique_directors,
    COUNT(DISTINCT rating)                                      AS unique_ratings,
    MIN(release_year)                                          AS oldest_release_year,
    MAX(release_year)                                          AS newest_release_year,
    ROUND(AVG(content_age), 1)                                 AS avg_content_age
FROM netflix_titles;


-- ─────────────────────────────────────────────────────────────
-- QUERY 12: YEAR-OVER-YEAR GROWTH
-- LAG() is a window function — gets value from previous row
-- This shows how much the library grew each year
-- ─────────────────────────────────────────────────────────────
SELECT
    added_year,
    total_added,
    LAG(total_added) OVER (ORDER BY added_year) AS prev_year,
    total_added - LAG(total_added) OVER (ORDER BY added_year) AS yoy_growth
FROM summary_by_year
WHERE added_year IS NOT NULL
ORDER BY added_year;
