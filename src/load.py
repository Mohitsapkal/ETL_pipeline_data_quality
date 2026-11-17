"""
Load stage: write transformed records into the SQLite warehouse.
"""
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "warehouse.db"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"

COLUMNS = {
    "customers":   ["customer_id", "name", "email", "country", "signup_date"],
    "products":    ["product_id", "name", "category", "price"],
    "orders":      ["order_id", "customer_id", "order_date", "status"],
    "order_items": ["item_id", "order_id", "product_id", "quantity", "unit_price"],
}


def init_db(conn):
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    logger.info("Schema initialized")


def _insert_many(conn, table, rows):
    if not rows:
        return 0
    cols = COLUMNS[table]
    placeholders = ", ".join(["?"] * len(cols))
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
    tuples = [tuple(r.get(c) for c in cols) for r in rows]
    conn.executemany(sql, tuples)
    return len(tuples)


def load_all(data):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
        total = sum(_insert_many(conn, t, data[t]) for t in COLUMNS)
        conn.commit()
        logger.info(f"Loaded {total} total rows into {DB_PATH}")
        return total
    finally:
        conn.close()