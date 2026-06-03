"""
=============================================================
STEP 2: DATA CLEANING & TRANSFORMATION
Netflix Data Engineering Project
=============================================================

CONCEPT:
--------
Raw data is almost never perfect. Data cleaning fixes:
  1. Missing / null values          → Replace or remove them
  2. 'Unknown' placeholder strings  → Treat as NaN, then fill or flag
  3. Duplicate rows                 → Remove exact copies
  4. Inconsistent column names      → Standardize to snake_case
  5. Wrong data types               → Convert dates, numbers, etc.
  6. New calculated columns         → Enrich data for analysis

THE ETL ACRONYM:
  E = Extract   → Step 1 (load raw file)
  T = Transform → THIS step (clean + enrich)
  L = Load      → Step 3 (save to SQLite database)

DATA CLEANING GOLDEN RULE:
Never modify the original file. Always work on a COPY.
This way you can always go back to the raw data.
=============================================================
"""

import pandas as pd
import numpy as np
import logging
import os
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("output/pipeline.log", mode="a")
    ]
)
logger = logging.getLogger(__name__)

DATA_PATH   = "data/netflix_titles.xlsx"
OUTPUT_PATH = "output/"


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 1: load_data()
# ══════════════════════════════════════════════════════════════════════════════
def load_data(file_path: str) -> pd.DataFrame:
    """Load raw Excel data."""
    logger.info(f"Loading data from: {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    df = pd.read_excel(file_path)
    logger.info(f"Loaded {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 2: standardize_column_names()
# PURPOSE: Rename columns to snake_case (all lowercase, spaces → underscores)
#
# WHY snake_case?
#   - Consistent naming prevents bugs ("DateAdded" vs "dateadded" vs "dateadded")
#   - SQL tables use snake_case by convention
#   - Python variables use snake_case by PEP-8 style guide
# ══════════════════════════════════════════════════════════════════════════════
def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename all columns to lowercase snake_case.
    Example: 'DateAdded' → 'date_added', 'listed_in' stays 'listed_in'
    """
    logger.info("Standardizing column names...")

    # Make a COPY so we don't modify the original DataFrame
    df = df.copy()

    # Build a rename mapping: {old_name: new_name}
    rename_map = {}
    for col in df.columns:
        # Step-by-step transformation:
        # 1. Strip whitespace: "  DateAdded  " → "DateAdded"
        # 2. Lowercase: "DateAdded" → "dateadded"
        # 3. Replace spaces with underscore: already done but just in case
        new_name = col.strip().lower().replace(" ", "_")
        rename_map[col] = new_name

    df.rename(columns=rename_map, inplace=True)  # inplace=True modifies df directly

    logger.info(f"Renamed columns: {list(rename_map.values())}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 3: handle_unknown_values()
# PURPOSE: Replace 'Unknown' strings with np.nan (proper missing value marker)
#
# WHY?
# - The dataset uses the string "Unknown" as a placeholder for missing data
# - But pandas treats "Unknown" as a valid string, not a missing value
# - By converting to NaN, pandas functions like .fillna() and .isnull() work correctly
# ══════════════════════════════════════════════════════════════════════════════
def handle_unknown_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace 'Unknown' placeholder strings with np.nan.
    Then fill NaN in key columns with 'Not Available'.
    """
    logger.info("Handling 'Unknown' placeholder values...")
    df = df.copy()

    # Count unknowns before replacement
    unknown_before = (df == "Unknown").sum().sum()  # Total across all columns

    # Replace "Unknown" with np.nan across entire DataFrame
    # np.nan is Python's standard representation of "no value"
    df.replace("Unknown", np.nan, inplace=True)

    unknown_after = df.isnull().sum().sum()
    logger.info(f"Replaced {unknown_before:,} 'Unknown' values with NaN")
    logger.info(f"Total NaN cells now: {unknown_after:,}")

    # For text columns, fill NaN with a descriptive label
    # This is better than leaving NaN in columns used for grouping/counting
    fill_map = {
        "director"  : "Not Available",
        "cast"      : "Not Available",
        "country"   : "Not Available",
        "rating"    : "Not Rated",
    }

    for col, fill_value in fill_map.items():
        if col in df.columns:
            filled = df[col].isnull().sum()
            df[col].fillna(fill_value, inplace=True)
            logger.info(f"  Filled {filled:,} NaN in '{col}' with '{fill_value}'")

    return df


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 4: remove_duplicates()
# PURPOSE: Drop exact duplicate rows (same values in ALL columns)
#
# WHY?
# Duplicates inflate counts and skew analysis.
# Example: If "Stranger Things" appears twice, it'd count as 2 shows.
# ══════════════════════════════════════════════════════════════════════════════
def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows based on show_id."""
    logger.info("Checking for duplicate rows...")
    df = df.copy()

    before = len(df)

    # drop_duplicates() removes rows where ALL columns have identical values
    # subset=['show_id'] → remove rows with the same show_id (more targeted)
    # keep='first' → keep the FIRST occurrence, drop the rest
    df.drop_duplicates(subset=["show_id"], keep="first", inplace=True)

    removed = before - len(df)
    logger.info(f"Removed {removed} duplicate rows. Remaining: {len(df):,}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 5: fix_date_columns()
# PURPOSE: Convert date column from Excel serial number / mixed formats to datetime
#
# IMPORTANT CONTEXT:
# Excel stores dates as numbers (e.g., 44464 = September 25, 2021).
# When pandas reads this, it may come as datetime objects or as serial integers.
# We need proper datetime objects so we can extract year, month, etc.
# ══════════════════════════════════════════════════════════════════════════════
def fix_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert 'date_added' to proper datetime format.
    Handle both datetime objects and Excel serial numbers.
    """
    logger.info("Fixing date column formats...")
    df = df.copy()

    # pd.to_datetime() intelligently converts strings/numbers to datetime
    # errors='coerce' → if conversion fails, set to NaT (Not a Time) instead of crashing
    df["dateadded"] = pd.to_datetime(df["dateadded"], errors="coerce")

    # How many dates failed to parse?
    failed = df["dateadded"].isnull().sum()
    logger.info(f"date_added converted. Failed conversions (NaT): {failed}")

    return df


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 6: create_calculated_columns()
# PURPOSE: Add new columns derived from existing data
#
# WHY CREATE CALCULATED COLUMNS?
# Raw data has "dateadded" = 2021-09-25
# But analysts ask: "How many titles were added in 2021?" or "What month peaks?"
# We need to EXTRACT those components as separate columns.
#
# CALCULATED COLUMNS WE'LL ADD:
# 1. added_year         → Year the title was added to Netflix
# 2. added_month        → Month number (1-12)
# 3. added_month_name   → Month name (January, February...)
# 4. content_age        → How many years old is this content?
# 5. duration_category  → Short / Medium / Long / Multi-Season
# ══════════════════════════════════════════════════════════════════════════════
def create_calculated_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add enriched calculated columns for analysis.
    """
    logger.info("Creating calculated columns...")
    df = df.copy()

    current_year = datetime.now().year  # e.g., 2025

    # ── 1. Added Year ─────────────────────────────────────────────────────────
    # .dt accessor lets us work with datetime components
    # .dt.year extracts just the year as an integer
    df["added_year"] = df["dateadded"].dt.year

    # ── 2. Added Month (number) ───────────────────────────────────────────────
    # .dt.month → 1 for January, 2 for February, ..., 12 for December
    df["added_month"] = df["dateadded"].dt.month

    # ── 3. Added Month Name ───────────────────────────────────────────────────
    # .dt.month_name() → "January", "February", etc.
    df["added_month_name"] = df["dateadded"].dt.month_name()

    # ── 4. Content Age ────────────────────────────────────────────────────────
    # How old is this content? Current year minus release year.
    # clip(lower=0) ensures we never get negative ages (data errors)
    df["content_age"] = (current_year - df["release_year"]).clip(lower=0)

    # ── 5. Duration Category ─────────────────────────────────────────────────
    # Movies are measured in minutes. TV Shows in seasons.
    # We create a human-readable category from the raw "duration" column.
    # np.where() works like Excel's IF() function: if condition, value_if_true, value_if_false

    def categorize_duration(row):
        """Categorize content by duration."""
        duration = str(row["duration"])
        content_type = row["type"]

        if content_type == "Movie":
            try:
                # Extract the number from "90 min" → int(90)
                # .split()[0] gets the first word before the space
                minutes = int(duration.split()[0])
                if minutes < 60:
                    return "Short Film"        # Under 1 hour
                elif minutes < 100:
                    return "Standard"          # 1h to 1h40m
                elif minutes < 150:
                    return "Long Film"         # 1h40m to 2h30m
                else:
                    return "Epic"              # Over 2h30m
            except (ValueError, IndexError):
                return "Unknown"
        elif content_type == "TV Show":
            try:
                seasons = int(duration.split()[0])
                if seasons == 1:
                    return "Mini-Series"       # 1 season
                elif seasons <= 3:
                    return "Short Series"      # 2-3 seasons
                elif seasons <= 6:
                    return "Medium Series"     # 4-6 seasons
                else:
                    return "Long-Running"      # 7+ seasons
            except (ValueError, IndexError):
                return "Unknown"
        return "Unknown"

    # apply() runs the function on every row (axis=1 = row-wise)
    df["duration_category"] = df.apply(categorize_duration, axis=1)

    # Log the new columns
    logger.info("Created columns: added_year, added_month, added_month_name, content_age, duration_category")
    logger.info(f"Duration category distribution:\n{df['duration_category'].value_counts().to_string()}")

    return df


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 7: final_cleanup()
# PURPOSE: Sort, reset index, verify data quality before loading
# ══════════════════════════════════════════════════════════════════════════════
def final_cleanup(df: pd.DataFrame) -> pd.DataFrame:
    """Sort by date_added and reset the DataFrame index."""
    logger.info("Running final cleanup...")
    df = df.copy()

    # Sort by date_added so newest content is at the bottom
    # na_position='first' puts NaT dates at the top
    df.sort_values("dateadded", ascending=True, na_position="first", inplace=True)

    # reset_index() gives the DataFrame clean 0,1,2,3... row numbers
    # drop=True prevents the old index from becoming a column
    df.reset_index(drop=True, inplace=True)

    logger.info(f"Final cleaned shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    logger.info(f"Columns: {df.columns.tolist()}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 8: save_cleaned_data()
# PURPOSE: Save the cleaned DataFrame to CSV and Excel
# ══════════════════════════════════════════════════════════════════════════════
def save_cleaned_data(df: pd.DataFrame, output_path: str) -> None:
    """Save cleaned data to CSV and Excel."""
    os.makedirs(output_path, exist_ok=True)

    # Save as CSV — lightweight, universally readable
    csv_path = os.path.join(output_path, "netflix_cleaned.csv")
    df.to_csv(csv_path, index=False)  # index=False → don't write row numbers as a column
    logger.info(f"Saved cleaned CSV → {csv_path}")

    # Save as Excel — for business users and reporting
    excel_path = os.path.join(output_path, "netflix_cleaned.xlsx")
    df.to_excel(excel_path, index=False, sheet_name="Cleaned_Data")
    logger.info(f"Saved cleaned Excel → {excel_path}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    logger.info("===== STEP 2: DATA CLEANING & TRANSFORMATION STARTED =====")

    # 1. Load raw data
    df = load_data(DATA_PATH)
    logger.info(f"[1/6] Raw data loaded: {df.shape}")

    # 2. Standardize column names
    df = standardize_column_names(df)
    logger.info(f"[2/6] Column names standardized")

    # 3. Handle unknown/missing values
    df = handle_unknown_values(df)
    logger.info(f"[3/6] Missing values handled")

    # 4. Remove duplicates
    df = remove_duplicates(df)
    logger.info(f"[4/6] Duplicates removed")

    # 5. Fix date formats
    df = fix_date_columns(df)
    logger.info(f"[5/6] Date columns fixed")

    # 6. Create calculated columns
    df = create_calculated_columns(df)
    logger.info(f"[6/6] Calculated columns created")

    # 7. Final sort and reset
    df = final_cleanup(df)

    # 8. Save outputs
    save_cleaned_data(df, OUTPUT_PATH)

    # 9. Print final summary
    print("\n" + "="*60)
    print("       CLEANING COMPLETE — FINAL SUMMARY")
    print("="*60)
    print(f"   Total Records   : {len(df):,}")
    print(f"   Total Columns   : {len(df.columns)}")
    print(f"   Movies          : {(df['type']=='Movie').sum():,}")
    print(f"   TV Shows        : {(df['type']=='TV Show').sum():,}")
    print(f"   Date Range      : {df['date_added'].min().date()} → {df['date_added'].max().date()}")
    print("="*60)

    logger.info("===== STEP 2 COMPLETED SUCCESSFULLY =====\n")
