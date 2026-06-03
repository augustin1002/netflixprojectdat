"""
=============================================================
MASTER PIPELINE — RUN ALL STEPS END-TO-END
Netflix Data Engineering Project
=============================================================

HOW TO RUN:
    cd Netflix_Data_Engineering_Project
    python scripts/run_pipeline.py

This script runs all 5 steps in sequence and times each one.
If any step fails, it logs the error and stops.
=============================================================
"""

import subprocess
import sys
import time
import logging
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

STEPS = [
    ("Step 1: Data Ingestion & Profiling",   "scripts/step1_ingest_and_profile.py"),
    ("Step 2: Data Cleaning & Transformation", "scripts/step2_clean_transform.py"),
    ("Step 3: ETL — Load to SQLite",           "scripts/step3_etl_load.py"),
    ("Step 4: SQL Business Analysis",           "scripts/step4_sql_analysis.py"),
    ("Step 5: Excel Dashboard Builder",         "scripts/step5_dashboard.py"),
]


def run_step(name: str, script_path: str) -> bool:
    """Run a single pipeline step and return success/failure."""
    logger.info(f"▶  Starting: {name}")
    start = time.time()

    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=False,
        text=True
    )

    elapsed = time.time() - start

    if result.returncode == 0:
        logger.info(f"✅ Completed: {name} ({elapsed:.1f}s)\n")
        return True
    else:
        logger.error(f"❌ FAILED: {name} (exit code {result.returncode})")
        return False


if __name__ == "__main__":
    print("\n" + "="*65)
    print("     NETFLIX DATA ENGINEERING PIPELINE — FULL RUN")
    print("="*65)
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*65 + "\n")

    os.makedirs("output",    exist_ok=True)
    os.makedirs("dashboard", exist_ok=True)

    total_start = time.time()
    results = []

    for step_name, script in STEPS:
        success = run_step(step_name, script)
        results.append((step_name, success))
        if not success:
            logger.error("Pipeline stopped due to failure.")
            break

    total_time = time.time() - total_start

    print("\n" + "="*65)
    print("     PIPELINE SUMMARY")
    print("="*65)
    for step_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}  {step_name}")
    print(f"\n   Total Runtime: {total_time:.1f} seconds")
    print("="*65)

    if all(s for _, s in results):
        print("\n🎉 ALL STEPS COMPLETED SUCCESSFULLY!")
        print(f"   📁 Outputs:   output/")
        print(f"   📊 Dashboard: dashboard/Netflix_Dashboard.xlsx")
        print(f"   🗄️  Database:  output/netflix.db")
        print(f"   📋 Log:       output/pipeline.log\n")
