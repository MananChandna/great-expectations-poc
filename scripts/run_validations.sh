#!/usr/bin/env bash
# =============================================================================
# run_validations.sh — Activate venv and run the full validation pipeline
# =============================================================================
# Usage: bash scripts/run_validations.sh [--skip-data-gen]
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Activate virtual environment
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    # shellcheck source=/dev/null
    source "$PROJECT_ROOT/venv/bin/activate"
    echo "🔄 Virtual environment activated: $(python --version)"
else
    echo "❌ venv not found. Run: bash scripts/setup_env.sh" >&2
    exit 1
fi

# Pass all arguments straight to main.py
echo "🚀 Starting GX validation pipeline …"
python main.py "$@"

echo ""
echo "✅ Validation pipeline completed."
echo "   Open Data Docs: xdg-open gx/uncommitted/data_docs/local_site/index.html"
