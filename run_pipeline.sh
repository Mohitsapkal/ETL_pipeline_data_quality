#!/usr/bin/env bash
# Orchestrates the full pipeline: generate -> ETL -> DQ checks.
# Logs everything to logs/run_YYYYMMDD_HHMMSS.log

set -euo pipefail

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

mkdir -p logs
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="logs/run_${TIMESTAMP}.log"

# Activate venv (works for cron too — no shell needed)
# shellcheck disable=SC1091
source "${PROJECT_DIR}/venv/bin/activate"

{
    echo "=========================================================="
    echo "Pipeline run started at $(date -Iseconds)"
    echo "Project dir: ${PROJECT_DIR}"
    echo "=========================================================="

    echo ""
    echo "[1/3] Generating raw data..."
    python -m src.generate_data

    echo ""
    echo "[2/3] Running ETL pipeline..."
    python -m src.pipeline

    echo ""
    echo "[3/3] Running data quality checks..."
    set +e
    python -m src.data_quality
    DQ_EXIT=$?
    set -e

    echo ""
    echo "=========================================================="
    if [ "${DQ_EXIT}" -eq 0 ]; then
        echo "Run finished SUCCESS — all DQ checks passed"
    elif [ "${DQ_EXIT}" -eq 2 ]; then
        echo "Run finished with DQ FAILURES (pipeline OK, see dq_audit)"
    else
        echo "Run FAILED — see error above"
        exit "${DQ_EXIT}"
    fi
    echo "Finished at $(date -Iseconds)"
    echo "=========================================================="
} 2>&1 | tee "${LOG_FILE}"