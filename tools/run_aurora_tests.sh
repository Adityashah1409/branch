#!/usr/bin/env bash
# Install the Aurora theme modules in a fresh database and run their tests.
#
# Usage: tools/run_aurora_tests.sh <odoo-source-dir> [database] [python]
# The browser tour needs Chrome or Chromium on the PATH.
set -euo pipefail

ODOO_DIR=${1:?"path to an Odoo 20.0 checkout"}
DB=${2:-aurora_ci}
PYTHON=${3:-python3}
REPO_DIR=$(cd "$(dirname "$0")/.." && pwd)
MODULES=website_aurora20,theme_aurora20

dropdb --if-exists "$DB" 2>/dev/null || true

LOG=$(mktemp)
"$PYTHON" "$ODOO_DIR/odoo-bin" -d "$DB" \
    --addons-path="$ODOO_DIR/addons,$REPO_DIR" \
    -i "$MODULES" --test-tags /website_aurora20,/theme_aurora20 \
    --stop-after-init --log-level=test 2>&1 | tee "$LOG"

# Odoo exits 0 even when tests fail: inspect the log.
if grep -qE "(ERROR|CRITICAL) .*(odoo\.addons\.(website|theme)_aurora20|odoo\.tests\.result|odoo\.modules)" "$LOG" \
   || grep -qE "[1-9][0-9]* failed|[1-9][0-9]* error\(s\)" "$LOG"; then
    echo "::error::Aurora tests failed"
    grep -E "ERROR|FAIL|tests when" "$LOG" | head -100
    exit 1
fi
grep -E "tests when loading" "$LOG" || { echo "::error::no test summary found"; exit 1; }
