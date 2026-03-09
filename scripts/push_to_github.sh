#!/usr/bin/env bash
# =============================================================================
# push_to_github.sh — Create GitHub repo via REST API and push project
# =============================================================================
# Usage: ./scripts/push_to_github.sh <github-username> <repo-name> <PAT-token>
#
# Example:
#   ./scripts/push_to_github.sh johndoe great-expectations-poc ghp_xxxxx
#
# The script:
#  1. Creates the GitHub repo via the REST API (curl + PAT)
#  2. Initialises local git if needed
#  3. Writes a production .gitignore
#  4. Makes the initial commit
#  5. Pushes to origin/main over HTTPS (PAT embedded in URL)
# =============================================================================

set -euo pipefail

# ── Colour helpers ─────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
err()  { echo -e "${RED}❌ $*${NC}" >&2; exit 1; }

# ── Arg validation ─────────────────────────────────────────────────────────────
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <github-username> <repo-name> <PAT-token>"
    echo ""
    echo "  github-username : your GitHub username"
    echo "  repo-name       : new repository name (e.g. great-expectations-poc)"
    echo "  PAT-token       : GitHub Personal Access Token with repo scope"
    exit 1
fi

GITHUB_USER="$1"
REPO_NAME="$2"
TOKEN="$3"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "========================================================"
echo "  Pushing Great Expectations POC to GitHub"
echo "  User : $GITHUB_USER"
echo "  Repo : $REPO_NAME"
echo "========================================================"

# ── Step 1: Create GitHub repository via REST API ─────────────────────────────
echo ""
echo "📡 Step 1/5 — Creating GitHub repository via REST API …"
HTTP_RESPONSE=$(curl -s -o /tmp/gh_create_response.json -w "%{http_code}" \
    -X POST \
    -H "Authorization: token $TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/user/repos \
    -d "{
      \"name\": \"$REPO_NAME\",
      \"description\": \"Production-grade Data Quality Framework POC using Great Expectations 0.18\",
      \"private\": false,
      \"auto_init\": false
    }")

if [ "$HTTP_RESPONSE" = "201" ]; then
    ok "Repository '$REPO_NAME' created on GitHub."
elif [ "$HTTP_RESPONSE" = "422" ]; then
    warn "Repository '$REPO_NAME' already exists — continuing with push."
else
    err "Failed to create repository (HTTP $HTTP_RESPONSE). Check your PAT token and username."
fi

# ── Step 2: Initialise git ────────────────────────────────────────────────────
echo ""
echo "🔧 Step 2/5 — Initialising local git repository …"
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    git init
    ok "Git initialised."
else
    warn ".git already exists — skipping init."
fi

git config user.email "${GIT_EMAIL:-devops@example.com}"
git config user.name "${GIT_NAME:-GX POC Bot}"

# ── Step 3: Write .gitignore ──────────────────────────────────────────────────
echo ""
echo "📝 Step 3/5 — Writing .gitignore …"
cat > "$PROJECT_ROOT/.gitignore" << 'GITIGNORE'
# Virtual environment
venv/
.venv/
env/

# Great Expectations — uncommitted (credentials, local data docs, validations)
gx/uncommitted/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/

# Jupyter checkpoints
.ipynb_checkpoints/

# Environment secrets
.env
*.env

# OS artefacts
.DS_Store
Thumbs.db
*.swp
*.swo

# IDE
.idea/
.vscode/

# Logs
*.log

# Pytest
.pytest_cache/
.coverage
htmlcov/

# Optional: dirty data (comment out to include in repo)
# data/bad_data/
GITIGNORE
ok ".gitignore written."

# ── Step 4: Commit ────────────────────────────────────────────────────────────
echo ""
echo "💾 Step 4/5 — Staging files and making initial commit …"
git add --all
git commit -m "feat: initial production-grade GX POC

- Synthetic data generation (customers/orders/products + dirty dataset)
- GX 0.18 FileSystemDataContext with PandasFilesystem datasources
- 3 expectation suites with 20+ total expectations
- Checkpoint runner with human-readable summary table
- Data Docs HTML report generation
- Pytest test suite (6 tests)
- Jupyter exploration notebook
- Full environment setup script
- GitHub push automation script
" || warn "Nothing to commit — repository already up to date."

# ── Step 5: Push to GitHub ────────────────────────────────────────────────────
echo ""
echo "🚀 Step 5/5 — Pushing to GitHub …"
REMOTE_URL="https://${TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"

# Set or update remote
if git remote get-url origin &>/dev/null; then
    git remote set-url origin "$REMOTE_URL"
    warn "Updated existing 'origin' remote."
else
    git remote add origin "$REMOTE_URL"
    ok "Remote 'origin' added."
fi

# Ensure we're on main
git branch -M main
git push -u origin main --force

echo ""
echo "========================================================"
ok "Pushed to https://github.com/$GITHUB_USER/$REPO_NAME"
echo "========================================================"
echo ""
echo "  🔗 View your repo: https://github.com/$GITHUB_USER/$REPO_NAME"
