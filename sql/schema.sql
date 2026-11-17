DROP TABLE IF EXISTS dq_audit;
DROP TABLE IF EXISTS pipeline_runs;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT,
    email       TEXT,
    country     TEXT,
    signup_date TEXT
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name       TEXT,
    category   TEXT,
    price      REAL
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date  TEXT,
    status      TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    item_id    INTEGER PRIMARY KEY,
    order_id   INTEGER,
    product_id INTEGER,
    quantity   INTEGER,
    unit_price REAL,
    FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE pipeline_runs (
    run_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp    TEXT NOT NULL,
    status           TEXT NOT NULL,
    rows_loaded      INTEGER,
    duration_seconds REAL,
    notes            TEXT
);

CREATE TABLE dq_audit (
    audit_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp TEXT NOT NULL,
    check_name    TEXT NOT NULL,
    table_name    TEXT,
    result        TEXT NOT NULL,
    failed_rows   INTEGER,
    details       TEXT
);

CREATE INDEX idx_orders_customer     ON orders(customer_id);
CREATE INDEX idx_order_items_order   ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);