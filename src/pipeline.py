"""
Pipeline entrypoint: Extract -> Transform -> Load, with run logging.
"""
import logging
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.extract import extract_all
from src.transform import transform_all
from src.load import load_all, DB_PATH

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "pipeline.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger("pipeline")


def record_run(status, rows_loaded, duration, notes=""):
    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO pipeline_runs (run_timestamp, status, rows_loaded, duration_seconds, notes) "
            "VALUES (?, ?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), status, rows_loaded, round(duration, 3), notes),
        )
        conn.commit()
    finally:
        conn.close()


def main():
    start = time.time()
    logger.info("=" * 60)
    logger.info("ETL pipeline run starting")
    try:
        raw = extract_all()
        cleaned = transform_all(raw)
        total = load_all(cleaned)
        duration = time.time() - start
        record_run("SUCCESS", total, duration)
        logger.info(f"Pipeline finished OK. {total} rows in {duration:.2f}s")
        return 0
    except Exception as e:
        duration = time.time() - start
        logger.exception("Pipeline FAILED")
        record_run("FAILED", 0, duration, notes=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())