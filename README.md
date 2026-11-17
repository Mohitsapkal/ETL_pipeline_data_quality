# ETL Pipeline with Data Quality Framework

An automated, modular ETL pipeline written in Python that ingests raw e-commerce data,
transforms it into a normalized SQLite warehouse, and runs a SQL-based data quality
audit on every load. Orchestrated via Bash and schedulable through cron.

## Highlights

- **Modular ETL** — separate `extract`, `transform`, `load` stages with logging
- **SQL-based data quality framework** — declarative checks for nulls, duplicates,
  referential integrity, invalid ranges, and schema drift; results written to a
  persistent `dq_audit` table
- **Run observability** — every pipeline execution recorded in `pipeline_runs`
  with duration, row count, and status
- **Bash orchestration + cron** — single-command end-to-end execution with
  timestamped logs, ready for scheduled runs

## Architecture


    ┌─────────────┐    ┌─────────┐    ┌───────────┐    ┌──────┐    ┌────────────┐
    │ Raw CSVs    │───▶│ Extract │───▶│ Transform │───▶│ Load │───▶│ SQLite DW  │
    │ (data/raw)  │    │ (schema │    │ (clean,   │    │      │    │warehouse.db│
    │             │    │  check) │    │  dedup,   │    │      │    │            │
    └─────────────┘    └─────────┘    │  cast)    │    └──────┘    └─────┬──────┘
                                      └───────────┘                       │
                                                                          ▼
                                                                  ┌──────────────┐
                                                                  │ DQ checks    │
                                                                  │ (sql/dq_     │
                                                                  │  checks.sql) │
                                                                  └──────┬───────┘
                                                                         ▼
                                                                  ┌──────────────┐
                                                                  │ dq_audit +   │
                                                                  │ pipeline_runs│
                                                                  └──────────────┘


## Tech Stack

Python 3 · SQLite · Bash · cron · Faker (synthetic data generation only)

No external pipeline framework, no heavyweight dependencies — everything runs locally.

## Data Model

| Table         | Purpose                                       |
|---------------|-----------------------------------------------|
| customers     | Customer master records                       |
| products      | Product catalog                               |
| orders        | Orders (FK → customers)                       |
| order_items   | Order line items (FK → orders, products)      |
| pipeline_runs | Run history: status, duration, rows loaded    |
| dq_audit      | Result of every DQ check, every run           |

## Data Quality Checks

Declared in `sql/dq_checks.sql` and executed by `src/data_quality.py`:

- Missing/empty emails
- Duplicate emails
- Invalid product prices (null or ≤ 0)
- Non-positive order item quantities
- Orphan orders (customer_id with no matching customer)
- Orphan order items (order_id or product_id with no parent)
- Future-dated orders
- Invalid order status values

Each check is executed against the warehouse and recorded as PASS / FAIL / ERROR
in `dq_audit`, with violation counts.

## Getting Started

    git clone git@github.com:YOUR_USERNAME/etl-pipeline-data-quality.git
    cd etl-pipeline-data-quality
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

Run the full pipeline:

    ./run_pipeline.sh

Or stage-by-stage:

    python -m src.generate_data   # synthetic raw data
    python -m src.pipeline        # extract -> transform -> load
    python -m src.data_quality    # run DQ checks

## Inspect the Warehouse

    sqlite3 data/warehouse.db
    sqlite> SELECT * FROM pipeline_runs ORDER BY run_id DESC LIMIT 5;
    sqlite> SELECT check_name, result, failed_rows FROM dq_audit
            WHERE run_timestamp = (SELECT MAX(run_timestamp) FROM dq_audit);

## Scheduling

Schedule daily runs via cron:

    crontab -e
    # daily at 02:00
    0 2 * * * /absolute/path/to/run_pipeline.sh >> /absolute/path/to/logs/cron.log 2>&1

## Project Layout

    .
    ├── run_pipeline.sh        # Bash orchestrator
    ├── requirements.txt
    ├── sql/
    │   ├── schema.sql         # Warehouse DDL
    │   └── dq_checks.sql      # Declarative DQ checks
    ├── src/
    │   ├── generate_data.py   # Synthetic raw data
    │   ├── extract.py         # CSV read + schema validation
    │   ├── transform.py       # Cleaning, dedup, casting
    │   ├── load.py            # SQLite load
    │   ├── data_quality.py    # DQ runner
    │   └── pipeline.py        # E -> T -> L entrypoint
    ├── data/
    │   ├── raw/               # Generated CSV inputs
    │   └── warehouse.db       # SQLite warehouse (gitignored)
    └── logs/                  # Per-run logs (gitignored)

## License

MIT