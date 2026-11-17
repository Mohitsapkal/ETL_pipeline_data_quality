"""
Extract stage: read raw CSV files and validate their schemas.
"""
import csv
import logging
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

EXPECTED_SCHEMAS = {
    "customers":   ["customer_id", "name", "email", "country", "signup_date"],
    "products":    ["product_id", "name", "category", "price"],
    "orders":      ["order_id", "customer_id", "order_date", "status"],
    "order_items": ["item_id", "order_id", "product_id", "quantity", "unit_price"],
}

logger = logging.getLogger(__name__)


def read_csv(name):
    path = RAW_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Raw file not found: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        expected = EXPECTED_SCHEMAS[name]
        actual = reader.fieldnames or []
        if actual != expected:
            raise ValueError(f"Schema drift in {name}.csv. Expected: {expected}, got: {actual}")
        rows = list(reader)
    logger.info(f"Extracted {len(rows)} rows from {name}.csv")
    return rows


def extract_all():
    return {name: read_csv(name) for name in EXPECTED_SCHEMAS}