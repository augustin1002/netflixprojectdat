"""
=============================================================
STEP 1: DATA INGESTION & PROFILING
Netflix Data Engineering Project
=============================================================

CONCEPT:
--------
Data Ingestion = Reading/loading raw data into your Python environment.
Data Profiling = Examining the dataset to understand its structure,
                 data types, size, missing values, and basic statistics.

Think of it like opening a new book:
  - First you check the table of contents (columns)
  - Then you see how many pages it has (rows)
  - Then you skim a few pages (head/tail)
  - Then you look for any torn/blank pages (missing values)

WHY THIS MATTERS IN DATA ENGINEERING:
- You can't clean what you don't understand
- Profiling catches problems early before they corrupt your pipeline
- It creates documentation for your team

TOOLS USED:
- pandas  : Python library for data manipulation (like Excel, but in code)
- numpy   : Numerical computing library
- logging : Python's built-in logging system for tracking what happened
=============================================================
"""

# ── Imports ──────────────────────────────────────────────────────────────────
import pandas as pd          # Data manipulation
import numpy as np           # Numerical operations
import logging               # Track events & errors
import os                    # File path operations
import sys                   # System operations
from datetime import datetime

# ── Logging Setup ─────────────────────────────────────────────────────────────
# logging lets us record what our program is doing at every step.
# Instead of print(), we use logging — it timestamps everything automatically
# and can write to a file for future review.
logging.basicConfig(
    level=logging.INFO,                          # Show INFO and above
    format="%(asctime)s | %(levelname)s | %(message)s",  # Timestamp | Level | Message
    handlers=[
        logging.StreamHandler(sys.stdout),       # Print to console
        logging.FileHandler("output/pipeline.log", mode="a")  # Save to log file
    ]
)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
# Storing file paths as constants at the top makes your code easier to update.
# If the file moves, you only change ONE line instead of hunting through all code.
DATA_PATH   = "data/netflix_titles.xlsx"
OUTPUT_PATH = "output/"


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 1: load_data()
# PURPOSE: Read the Excel file into a pandas DataFrame
# A DataFrame is like a table in Excel — rows and columns — but in Python.
# ══════════════════════════════════════════════════════════════════════════════
def load_data(file_path: str) -> pd.DataFrame:
    """
    Load Netflix dataset from Excel file.

    Args:
        file_path (str): Path to the Excel file
    Returns:
        pd.DataFrame: Raw loaded dataset
    """
    logger.info(f"Loading data from: {file_path}")

    # Check if file exists BEFORE trying to open it
    # This is error handling — we tell the user exactly what went wrong
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Dataset not found at: {file_path}")

    try:
        # pd.read_excel() reads an Excel file into a DataFrame
        # Like clicking "Open" in Excel, but in Python
        df = pd.read_excel(file_path)
        logger.info(f"Data loaded successfully. Shape: {df.shape}")
        # df.shape returns (rows, columns) — e.g. (8801, 12)
        return df

    except Exception as e:
        # If ANYTHING goes wrong, log it and re-raise so we know what broke
        logger.error(f"Error loading data: {e}")
        raise


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 2: profile_data()
# PURPOSE: Examine every aspect of the dataset and print a full report
# ══════════════════════════════════════════════════════════════════════════════
def profile_data(df: pd.DataFrame) -> dict:
    """
    Perform comprehensive data profiling.

    Args:
        df (pd.DataFrame): Input DataFrame
    Returns:
        dict: Profile summary dictionary
    """
    logger.info("Starting data profiling...")

    print("\n" + "="*60)
    print("       NETFLIX DATASET — DATA PROFILE REPORT")
    print("="*60)

    # ── Basic Shape ───────────────────────────────────────────────────────────
    # df.shape[0] = number of rows  (records/titles)
    # df.shape[1] = number of columns (fields/attributes)
    print(f"\n📊 DATASET DIMENSIONS")
    print(f"   Total Rows    : {df.shape[0]:,}")   # :, adds comma formatting → 8,801
    print(f"   Total Columns : {df.shape[1]}")

    # ── Column Names & Data Types ─────────────────────────────────────────────
    # dtype = data type of each column
    # object  → text (strings)
    # int64   → whole numbers
    # float64 → decimal numbers
    # datetime64 → dates
    print(f"\n📋 COLUMN NAMES & DATA TYPES")
    print(f"{'Column':<20} {'Dtype':<15} {'Non-Null Count':<15}")
    print("-" * 50)
    for col in df.columns:
        non_null = df[col].notna().sum()
        print(f"   {col:<18} {str(df[col].dtype):<15} {non_null:,}")

    # ── Missing Values Analysis ───────────────────────────────────────────────
    # isnull() returns True/False for each cell — True means it's empty
    # .sum() counts all the Trues (= count of missing values)
    # / len(df) * 100 = percentage missing
    print(f"\n❗ MISSING VALUES ANALYSIS")
    missing = df.isnull().sum()
    # Also count "Unknown" strings — they act like missing values
    unknown_counts = (df == "Unknown").sum()

    for col in df.columns:
        null_count   = missing[col]
        unk_count    = unknown_counts.get(col, 0)
        total_pct    = (null_count / len(df)) * 100
        print(f"   {col:<20} NaN: {null_count:<6} | 'Unknown': {unk_count:<6} | NaN%: {total_pct:.1f}%")

    # ── Duplicate Rows ────────────────────────────────────────────────────────
    # duplicated() marks each row True if it's an exact copy of a previous row
    dupes = df.duplicated().sum()
    print(f"\n🔁 DUPLICATE ROWS: {dupes}")

    # ── Unique Value Counts ───────────────────────────────────────────────────
    # nunique() = count of unique distinct values per column
    # High nunique → likely an ID or free-text column
    # Low  nunique → likely a category column
    print(f"\n🔢 UNIQUE VALUE COUNTS PER COLUMN")
    for col in df.columns:
        print(f"   {col:<20}: {df[col].nunique():,} unique values")

    # ── Sample Data Preview ───────────────────────────────────────────────────
    print(f"\n👀 FIRST 3 ROWS PREVIEW")
    print(df.head(3).to_string())

    # ── Categorical Column Distributions ─────────────────────────────────────
    # value_counts() shows how many times each value appears
    print(f"\n📺 CONTENT TYPE DISTRIBUTION")
    print(df["type"].value_counts().to_string())

    print(f"\n⭐ RATING DISTRIBUTION")
    print(df["rating"].value_counts().to_string())

    print(f"\n📅 RELEASE YEAR RANGE")
    print(f"   Earliest: {df['release_year'].min()}")
    print(f"   Latest  : {df['release_year'].max()}")
    print(f"   Average : {df['release_year'].mean():.0f}")

    # ── Build Summary Dictionary ──────────────────────────────────────────────
    # Return a dictionary so other functions can use this info programmatically
    profile_summary = {
        "total_rows"      : df.shape[0],
        "total_columns"   : df.shape[1],
        "duplicate_rows"  : int(dupes),
        "columns"         : df.columns.tolist(),
        "dtypes"          : df.dtypes.astype(str).to_dict(),
        "null_counts"     : missing.to_dict(),
        "unknown_counts"  : unknown_counts.to_dict(),
        "movies_count"    : int((df["type"] == "Movie").sum()),
        "tvshows_count"   : int((df["type"] == "TV Show").sum()),
    }

    logger.info("Data profiling completed.")
    print("\n" + "="*60)
    print("       PROFILING COMPLETE")
    print("="*60)

    return profile_summary


# ══════════════════════════════════════════════════════════════════════════════
# MAIN: Entry point — runs when you execute this script directly
# if __name__ == "__main__": ensures this block only runs when YOU run this
# file — not when another script imports it
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    logger.info("===== STEP 1: DATA INGESTION & PROFILING STARTED =====")

    # Step A: Load data
    df_raw = load_data(DATA_PATH)

    # Step B: Profile data
    profile = profile_data(df_raw)

    logger.info(f"Summary → Movies: {profile['movies_count']} | TV Shows: {profile['tvshows_count']}")
    logger.info("===== STEP 1 COMPLETED SUCCESSFULLY =====\n")
