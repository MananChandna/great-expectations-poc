#!/usr/bin/env bash
# =============================================================================
# setup_env.sh — Full environment bootstrap for Great Expectations POC
# =============================================================================
# Usage: bash scripts/setup_env.sh
# Tested on: Ubuntu 22.04 LTS (bare metal and VMware guest)
# =============================================================================

set -euo pipefail

# ── Colour helpers ─────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
err()  { echo -e "${RED}❌ $*${NC}" >&2; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "========================================================"
echo "  Great Expectations POC — Environment Setup"
echo "  Project root: $PROJECT_ROOT"
echo "========================================================"

# ── Step 1: System packages ────────────────────────────────────────────────────
echo ""
echo "📦 Step 1/6 — Installing system packages …"
sudo apt-get update -qq
sudo apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    python3.10-distutils \
    git \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev \
    --no-install-recommends
ok "System packages installed."

# ── Step 2: Virtual environment ────────────────────────────────────────────────
echo ""
echo "🐍 Step 2/6 — Creating Python virtual environment …"
if [ -d "$PROJECT_ROOT/venv" ]; then
    warn "venv/ already exists — skipping creation."
else
    python3.10 -m venv "$PROJECT_ROOT/venv"
    ok "Virtual environment created at $PROJECT_ROOT/venv"
fi

# ── Step 3: Activate venv ──────────────────────────────────────────────────────
echo ""
echo "🔄 Step 3/6 — Activating virtual environment …"
# shellcheck source=/dev/null
source "$PROJECT_ROOT/venv/bin/activate"
ok "Virtual environment activated: $(python --version)"

# ── Step 4: Install pip packages ──────────────────────────────────────────────
echo ""
echo "📥 Step 4/6 — Installing pip packages from requirements.txt …"
pip install --upgrade pip setuptools wheel --quiet
pip install -r "$PROJECT_ROOT/requirements.txt" --quiet
ok "All pip packages installed."

# ── Step 5: Verify Great Expectations ─────────────────────────────────────────
echo ""
echo "🔍 Step 5/6 — Verifying Great Expectations installation …"
python -c "import great_expectations; print(f'GX version: {great_expectations.__version__}')"
ok "Great Expectations is ready."

# ── Step 6: Create .env from template ────────────────────────────────────────
echo ""
echo "⚙️  Step 6/6 — Setting up .env file …"
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    ok ".env created from .env.example"
else
    warn ".env already exists — skipping copy."
fi

# ── Done ───────────────────────────────────────────────────────────────────────
echo ""
echo "========================================================"
ok "Environment setup complete!"
echo "========================================================"
echo ""
echo "  To activate the venv in a new shell:"
echo "    source venv/bin/activate"
echo ""
echo "  To run the full pipeline:"
echo "    python main.py"
echo ""
echo "  To run tests:"
echo "    pytest tests/ -v"
echo ""
