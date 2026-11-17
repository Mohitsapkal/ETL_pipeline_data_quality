"""
Transform stage: clean, deduplicate, type-cast.
Leaves referential and outlier issues for the DQ layer to detect.
"""
import logging

logger = logging.getLogger(__name__)


def _safe_int(v):
    try: return int(v)
    except (ValueError, TypeError): return None


def _safe_float(v):
    try: return float(v)
    except (ValueError, TypeError): return None


def _clean_str(v):
    if v is None: return None
    s = str(v).strip()
    return s if s else None


def transform_customers(rows):
    seen, cleaned = set(), []
    for r in rows:
        cid = _safe_int(r.get("customer_id"))
        if cid is None or cid in seen:
            continue
        seen.add(cid)
        email = _clean_str(r.get("email"))
        cleaned.append({
            "customer_id": cid,
            "name":        _clean_str(r.get("name")),
            "email":       email.lower() if email else None,
            "country":     _clean_str(r.get("country")),
            "signup_date": _clean_str(r.get("signup_date")),
        })
    logger.info(f"Transformed customers: {len(rows)} -> {len(cleaned)} (dedup by customer_id)")
    return cleaned


def transform_products(rows):
    cleaned = []
    for r in rows:
        pid = _safe_int(r.get("product_id"))
        if pid is None: continue
        cleaned.append({
            "product_id": pid,
            "name":       _clean_str(r.get("name")),
            "category":   _clean_str(r.get("category")),
            "price":      _safe_float(r.get("price")),
        })
    logger.info(f"Transformed products: {len(cleaned)} rows")
    return cleaned


def transform_orders(rows):
    cleaned = []
    for r in rows:
        oid = _safe_int(r.get("order_id"))
        if oid is None: continue
        status = _clean_str(r.get("status"))
        cleaned.append({
            "order_id":    oid,
            "customer_id": _safe_int(r.get("customer_id")),
            "order_date":  _clean_str(r.get("order_date")),
            "status":      status.lower() if status else None,
        })
    logger.info(f"Transformed orders: {len(cleaned)} rows")
    return cleaned


def transform_order_items(rows):
    cleaned = []
    for r in rows:
        iid = _safe_int(r.get("item_id"))
        if iid is None: continue
        cleaned.append({
            "item_id":    iid,
            "order_id":   _safe_int(r.get("order_id")),
            "product_id": _safe_int(r.get("product_id")),
            "quantity":   _safe_int(r.get("quantity")),
            "unit_price": _safe_float(r.get("unit_price")),
        })
    logger.info(f"Transformed order_items: {len(cleaned)} rows")
    return cleaned


def transform_all(raw):
    return {
        "customers":   transform_customers(raw["customers"]),
        "products":    transform_products(raw["products"]),
        "orders":      transform_orders(raw["orders"]),
        "order_items": transform_order_items(raw["order_items"]),
    }