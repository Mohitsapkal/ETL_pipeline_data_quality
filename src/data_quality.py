"""
Data Quality runner: parses dq_checks.sql, executes each check,
writes PASS/FAIL results to the dq_audit table, and prints a summary.
"""
import logging
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "warehouse.db"
CHECKS_PATH = ROOT / "sql" / "dq_checks.sql"

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s dq | %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "data_quality.log"), logging.StreamHandler()],
)
logger = logging.getLogger("dq")

HEADER_RE = re.compile(r"--\s*name:\s*(\S+)\s*\|\s*table:\s*(\S+)")


def parse_checks(text):
    checks, current = [], None
    for line in text.splitlines():
        m = HEADER_RE.match(line.strip())
        if m:
            if current:
                checks.append(current)
            current = {"name": m.group(1), "table": m.group(2), "sql": ""}
        elif current is not None and line.strip() and not line.strip().startswith("--"):
            current["sql"] += line + "\n"
    if current:
        checks.append(current)
    return checks


def run_checks():
    if not DB_PATH.exists():
        logger.error("Warehouse not found. Run the pipeline first.")
        return 1

    text = CHECKS_PATH.read_text()
    checks = parse_checks(text)
    ts = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(DB_PATH)
    passed = failed = 0
    try:
        for chk in checks:
            sql = chk["sql"].strip().rstrip(";")
            try:
                row = conn.execute(sql).fetchone()
                failed_rows = int(row[0]) if row and row[0] is not None else 0
            except sqlite3.Error as e:
                conn.execute(
                    "INSERT INTO dq_audit (run_timestamp, check_name, table_name, result, failed_rows, details) "
                    "VALUES (?, ?, ?, 'ERROR', NULL, ?)",
                    (ts, chk["name"], chk["table"], str(e)),
                )
                logger.error(f"[ERROR] {chk['name']}: {e}")
                failed += 1
                continue

            result = "PASS" if failed_rows == 0 else "FAIL"
            details = "0 violations" if failed_rows == 0 else f"{failed_rows} violations"
            conn.execute(
                "INSERT INTO dq_audit (run_timestamp, check_name, table_name, result, failed_rows, details) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (ts, chk["name"], chk["table"], result, failed_rows, details),
            )
            marker = "✓" if result == "PASS" else "✗"
            logger.info(f"[{marker} {result}] {chk['name']:40s} {details}")
            if result == "PASS":
                passed += 1
            else:
                failed += 1
        conn.commit()
    finally:
        conn.close()

    total = passed + failed
    logger.info("-" * 60)
    logger.info(f"DQ summary: {passed}/{total} checks passed, {failed} failed")
    return 0 if failed == 0 else 2  # exit 2 = DQ failures (not pipeline crash)


if __name__ == "__main__":
    sys.exit(run_checks())