# Production-Grade ETL Pipeline with Automated Data Quality Framework

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite-003B57.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Author](https://img.shields.io/badge/Author-Mohit%20Sapkal-brightgreen.svg)](https://github.com/Mohitsapkal)
[![Repo](https://img.shields.io/badge/Repository-ETL__pipeline__data__quality-orange.svg)](https://github.com/Mohitsapkal/ETL_pipeline_data_quality)

A robust, modular, and observable ETL (Extract, Transform, Load) pipeline in Python and SQL. It ingests multi-source raw e-commerce transaction feeds, performs rigorous validation and normalization, loads data into an indexed SQLite warehouse, and executes an automated declarative data quality audit on every execution.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Data Warehouse Model](#data-warehouse-model)
- [Data Quality Framework](#data-quality-framework)
- [Pipeline Observability & Logging](#pipeline-observability--logging)
- [Project Layout](#project-layout)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Execution](#execution)
- [Database Inspection](#database-inspection)
- [Production Scheduling](#production-scheduling)
- [Author & Copyright](#author--copyright)
- [License](#license)

---

## Overview

In modern data architectures, silent data corruption—missing foreign keys, duplicate entities, out-of-range financial figures, and format anomalies—frequently propagates downstream into analytics dashboards and machine learning models.

This project delivers an end-to-end data pipeline engineered with defensive design patterns:
1. **Source Schema Enforcement** during extraction.
2. **Defensive Transformation & Deduplication** during intermediate processing.
3. **Transactional Relational Loading** into a normalized dimensional schema.
4. **Declarative SQL Data Quality Audits** recording full PASS/FAIL metrics into dedicated operational tables.
5. **Run History Telemetry** capturing performance durations, record counts, and run health.

---

## Key Features

- **Decoupled Architecture**: Clean separation of concerns between `extract`, `transform`, `load`, and `data_quality` stages.
- **Declarative Quality Auditing**: SQL-based assertion definitions stored in `sql/dq_checks.sql` evaluated dynamically against loaded warehouse tables.
- **Automated Anomaly Detection**:
  - Completeness validation (unpopulated email addresses).
  - Uniqueness constraints (duplicate email detection).
  - Domain constraints (non-positive pricing, negative order item quantities).
  - Referential integrity validation (orphaned orders, missing product references).
  - Temporal sanity checks (future-dated orders).
  - Enumeration validation (illegal order statuses).
- **Audit & Observability**: Every execution logs fine-grained telemetry to `pipeline_runs` and `dq_audit` tables for full lineage and historical observability.
- **Zero Heavyweight Dependencies**: Lightweight implementation requiring only Python standard libraries, SQLite, and `Faker` (for synthetic seed data).
- **Bash Automation & Cron-Ready**: Orchestrated with shell automation and timestamped execution logs.

---

## System Architecture

```text
  ┌─────────────────┐
  │   Raw CSV Feeds │ (customers, products, orders, order_items)
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  src.extract    │ ───► Verifies file presence & column schemas
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  src.transform  │ ───► Deduplication, type coercion, string sanitation
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │    src.load     │ ───► DDL initialization, indexed relational load
  └────────┬────────┘
           │
           ▼
  ┌────────────────────────────────────────────────────────┐
  │               SQLite Analytical Warehouse              │
  │                     data/warehouse.db                  │
  │  (customers, products, orders, order_items, runs, audit)│
  └────────┬───────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────┐
  │ src.data_quality│ ◄─── Evaluates sql/dq_checks.sql declarative rules
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ dq_audit Table  │ ───► Persists audit results (PASS/FAIL, violation counts)
  └─────────────────┘
```

---

## Data Warehouse Model

The analytical warehouse schema is defined in [`sql/schema.sql`](file:///c:/Users/mohit/Downloads/etl-pipeline-data-quality/sql/schema.sql) and normalized into 3NF:

| Table | Entity Type | Primary Key | Foreign Keys | Key Attributes |
| :--- | :--- | :--- | :--- | :--- |
| `customers` | Dimension | `customer_id` | - | `name`, `email`, `country`, `signup_date` |
| `products` | Dimension | `product_id` | - | `name`, `category`, `price` |
| `orders` | Fact | `order_id` | `customer_id` → `customers` | `order_date`, `status` |
| `order_items` | Fact (Line Items) | `item_id` | `order_id` → `orders`<br>`product_id` → `products` | `quantity`, `unit_price` |
| `pipeline_runs` | Metadata | `run_id` | - | `run_timestamp`, `status`, `rows_loaded`, `duration_seconds` |
| `dq_audit` | Metadata | `audit_id` | - | `run_timestamp`, `check_name`, `table_name`, `result`, `failed_rows` |

---

## Data Quality Framework

Quality rules are maintained as declarative SQL checks in [`sql/dq_checks.sql`](file:///c:/Users/mohit/Downloads/etl-pipeline-data-quality/sql/dq_checks.sql). The test suite executes after each warehouse load:

| Check Name | Target Table | Rule Description | Quality Dimension |
| :--- | :--- | :--- | :--- |
| `customers_missing_email` | `customers` | `email IS NULL OR email = ''` | Completeness |
| `customers_duplicate_email`| `customers` | Duplicate customer emails | Uniqueness |
| `products_invalid_price` | `products` | `price IS NULL OR price <= 0` | Validity / Domain |
| `order_items_negative_quantity` | `order_items` | `quantity IS NULL OR quantity <= 0` | Validity / Domain |
| `orders_orphan_customer` | `orders` | Customer ID not in `customers` | Referential Integrity |
| `order_items_orphan_order` | `order_items` | Order ID not in `orders` | Referential Integrity |
| `order_items_orphan_product` | `order_items` | Product ID not in `products` | Referential Integrity |
| `orders_future_date` | `orders` | `order_date > datetime('now')` | Timeliness / Sanity |
| `orders_invalid_status` | `orders` | Status not in approved enum values | Conformity |

---

## Pipeline Observability & Logging

- **Run Audit Table (`pipeline_runs`)**: Tracks start timestamps, execution status (`SUCCESS` / `FAILED`), record counts, runtime latency, and error notes.
- **Quality Audit Table (`dq_audit`)**: Stores an immutable historical record of every test run, including assertion names, outcome (`PASS` / `FAIL`), and offending record counts.
- **Structured File Logs**: Detailed execution logs are stored with timestamps in the `logs/` directory:
  - `logs/pipeline.log`: High-level operational events and stage durations.
  - `logs/data_quality.log`: Assertion-by-assertion results and summary statistics.

---

## Project Layout

```text
etl-pipeline-data-quality/
├── .gitignore               # Ignored environments, databases, and logs
├── README.md                # Comprehensive documentation
├── requirements.txt         # Project dependencies (Faker)
├── run_pipeline.sh          # End-to-end shell orchestrator
├── data/
│   ├── raw/                 # Input CSV datasets
│   │   ├── customers.csv
│   │   ├── orders.csv
│   │   ├── order_items.csv
│   │   └── products.csv
│   └── warehouse.db         # SQLite warehouse database (local)
├── logs/                    # Timestamped runtime logs
│   └── .gitkeep
├── sql/
│   ├── schema.sql           # Warehouse DDL and index definitions
│   └── dq_checks.sql        # Declarative SQL data quality assertions
└── src/
    ├── __init__.py
    ├── extract.py           # Ingestion and schema validation
    ├── transform.py         # Data cleansing and normalization
    ├── load.py              # Warehouse schema creation and insertion
    ├── data_quality.py      # Data quality test runner
    ├── generate_data.py     # Synthetic data generator with anomalies
    └── pipeline.py          # E-T-L pipeline coordinator
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- SQLite 3
- Bash / Unix-like shell environment (or Git Bash / WSL on Windows)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Mohitsapkal/ETL_pipeline_data_quality.git
   cd ETL_pipeline_data_quality
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv

   # On Linux/macOS:
   source venv/bin/activate

   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Execution

#### Option 1: Automated End-to-End Orchestration
Run the full orchestration workflow (data generation, ETL, quality checks, and log archiving) in a single command:
```bash
chmod +x run_pipeline.sh
./run_pipeline.sh
```

#### Option 2: Step-by-Step Execution
Execute individual pipeline stages sequentially:

```bash
# 1. Generate synthetic raw data with controlled anomalies
python -m src.generate_data

# 2. Execute Extract -> Transform -> Load stages
python -m src.pipeline

# 3. Execute the Data Quality framework
python -m src.data_quality
```

---

## Database Inspection

Inspect data warehouse tables and review data quality audit logs using the SQLite CLI:

```bash
sqlite3 data/warehouse.db
```

```sql
-- View the latest pipeline execution records
SELECT run_id, run_timestamp, status, rows_loaded, duration_seconds 
FROM pipeline_runs 
ORDER BY run_id DESC 
LIMIT 5;

-- Inspect failed data quality assertions from the most recent run
SELECT check_name, table_name, result, failed_rows, details 
FROM dq_audit 
WHERE run_timestamp = (SELECT MAX(run_timestamp) FROM dq_audit)
ORDER BY failed_rows DESC;

-- Verify customer records loaded into the warehouse
SELECT customer_id, name, email, country, signup_date 
FROM customers 
LIMIT 10;
```

---

## Production Scheduling

To execute the pipeline automatically on a scheduled cadence, configure a system `cron` job:

```bash
crontab -e
```

Add a scheduled trigger (e.g., daily at 02:00 UTC):
```bash
0 2 * * * cd /path/to/ETL_pipeline_data_quality && ./run_pipeline.sh >> logs/cron.log 2>&1
```

---

## Author & Copyright

- **Author / Project Owner**: Mohit Sapkal
- **GitHub Profile**: [@Mohitsapkal](https://github.com/Mohitsapkal)
- **Repository**: [Mohitsapkal/ETL_pipeline_data_quality](https://github.com/Mohitsapkal/ETL_pipeline_data_quality)

---

## License

This project is licensed under the MIT License.

Copyright (c) 2026 Mohit Sapkal. All rights reserved.
