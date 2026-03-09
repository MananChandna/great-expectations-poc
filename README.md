# 🏗️ Great Expectations POC — Production-Grade Data Quality Framework

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Great Expectations 0.18](https://img.shields.io/badge/great--expectations-0.18-orange.svg)](https://greatexpectations.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production-ready Proof of Concept demonstrating a full **Data Quality Framework** using
[Great Expectations 0.18](https://greatexpectations.io/) on Ubuntu 22.04 LTS.  
Covers synthetic data generation, programmatic expectation suites, checkpoint validation,
Data Docs reporting, and automated GitHub deployment.

---

## 🏛️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                       Data Quality Pipeline                          │
│                                                                      │
│  ┌──────────────┐   ┌──────────────────┐   ┌──────────────────────┐ │
│  │  data/raw/   │   │  src/            │   │  gx/                 │ │
│  │              │   │                  │   │                      │ │
│  │ customers.csv│──▶│ data_generator   │   │ great_expectations   │ │
│  │ orders.csv   │   │ gx_setup         │──▶│   .yml               │ │
│  │ products.csv │   │ expectations_    │   │ expectations/        │ │
│  │              │   │   builder        │   │ checkpoints/         │ │
│  └──────────────┘   │ checkpoint_      │   │ uncommitted/         │ │
│                     │   runner         │   │   validations/       │ │
│  ┌──────────────┐   │ utils            │   │   data_docs/         │ │
│  │ data/bad_    │   └──────────────────┘   └──────────────────────┘ │
│  │   data/      │            │                        │             │
│  │ customers_   │            ▼                        ▼             │
│  │   dirty.csv  │   ┌──────────────────┐   ┌──────────────────────┐ │
│  └──────────────┘   │  Checkpoints     │   │  HTML Data Docs      │ │
│                     │  (PASS/FAIL)     │   │  (local_site/)       │ │
│                     └──────────────────┘   └──────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## ✅ Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Ubuntu | 22.04 LTS | Host OS (bare metal or VMware VM) |
| Python | 3.10+ | Runtime |
| pip | 23+ | Package manager |
| git | 2.x | Version control |
| curl | 7.x | GitHub API calls |

> **VMware note:** Allocate at least **8 GB RAM** to the VM for smooth GX operations.

---

## ⚡ Quick Start (5 commands)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USER/great-expectations-poc.git
cd great-expectations-poc

# 2. Set up the environment (installs packages, creates venv)
bash scripts/setup_env.sh

# 3. Activate the virtual environment
source venv/bin/activate

# 4. Run the full pipeline
python main.py

# 5. Open Data Docs in browser
xdg-open gx/uncommitted/data_docs/local_site/index.html
```

---

## 🔧 Full Setup Instructions

### 1. System Setup

```bash
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3-pip git curl
```

### 2. Clone & Enter Project

```bash
git clone https://github.com/YOUR_USER/great-expectations-poc.git
cd great-expectations-poc
```

### 3. Create & Activate Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment

```bash
cp .env.example .env
# Edit .env if you need to customise paths
```

---

## 📁 Project Structure

```
great-expectations-poc/
├── data/
│   ├── raw/
│   │   ├── customers.csv          # 1,000 clean customer records
│   │   ├── orders.csv             # 5,000 clean order records
│   │   └── products.csv           # 200 clean product records
│   └── bad_data/
│       └── customers_dirty.csv    # 200 records with injected DQ issues
│
├── gx/                            # Great Expectations project root
│   ├── great_expectations.yml     # GX configuration
│   ├── expectations/              # Expectation suite JSON files
│   ├── checkpoints/               # Checkpoint YAML configurations
│   └── uncommitted/               # ⚠️  git-ignored (contains local paths)
│       ├── validations/           # Validation result JSON files
│       └── data_docs/local_site/  # HTML Data Docs report
│
├── src/
│   ├── __init__.py
│   ├── data_generator.py          # Synthetic data via Faker
│   ├── gx_setup.py                # GX context & datasource registration
│   ├── expectations_builder.py    # Programmatic expectation suite builder
│   ├── checkpoint_runner.py       # Checkpoint execution & result reporting
│   └── utils.py                   # Logging, path helpers, shared utilities
│
├── notebooks/
│   └── explore_data_quality.ipynb # Interactive data quality exploration
│
├── scripts/
│   ├── setup_env.sh               # Full environment bootstrap
│   ├── run_validations.sh         # Convenience wrapper for main.py
│   └── push_to_github.sh          # GitHub repo creation & push
│
├── tests/
│   └── test_expectations.py       # 6 pytest tests
│
├── main.py                        # Single entry point
├── requirements.txt               # Pinned dependencies
├── .env.example                   # Environment variable template
├── .gitignore                     # Excludes venv, uncommitted, secrets
└── README.md                      # This file
```

---

## 🔬 How Great Expectations Works Here

### 1. FileSystemDataContext
GX 0.18's **fluent API** is used exclusively.  No legacy `datasource.yaml` patterns.

```python
import great_expectations as gx
context = gx.get_context(context_root_dir="gx/")
```

### 2. Datasources & Data Assets
Each CSV is registered as a `PandasFilesystemDatasource` with a named `CsvDataAsset`:

```python
datasource = context.sources.add_pandas_filesystem(
    name="customers_datasource",
    base_directory="data/raw/",
)
asset = datasource.add_csv_asset(
    name="customers_asset",
    filepath_or_buffer="customers.csv",
)
```

### 3. Expectation Suites
Suites are built programmatically using `ExpectationConfiguration` objects:

```python
suite.add_expectation(
    gx.core.ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_between",
        kwargs={"column": "age", "min_value": 18, "max_value": 80},
    )
)
```

### 4. Validations
Validations run via the fluent `Validator` API, not legacy `run_checkpoint()`:

```python
validator = context.get_validator(
    batch_request=asset.build_batch_request(),
    expectation_suite_name="customers_quality_suite",
)
result = validator.validate()
```

---

## 🎯 Expectation Suites

### `customers_quality_suite` (9 expectations)
| Expectation | Column(s) | Constraint |
|-------------|-----------|------------|
| not_be_null | customer_id, email, name | — |
| be_unique | customer_id, email | — |
| be_between | age | 18 – 80 |
| match_regex | email | standard email regex |
| be_between | credit_score | 300 – 850 |
| be_in_set | is_active | [True, False] |
| be_dateutil_parseable | signup_date | — |
| row_count_between | — | 800 – 1,200 |
| proportion_unique | customer_id | ≥ 0.99 |

### `orders_quality_suite` (6 expectations)
| Expectation | Column(s) | Constraint |
|-------------|-----------|------------|
| not_be_null | order_id, customer_id, order_date | — |
| be_unique | order_id | — |
| be_between | quantity | 1 – 50 |
| be_between | unit_price | 0.99 – 999.99 |
| be_in_set | status | pending/shipped/delivered/cancelled |
| be_between | discount_pct | 0 – 30 |

### `products_quality_suite` (5 expectations)
| Expectation | Column(s) | Constraint |
|-------------|-----------|------------|
| not_be_null | product_id, product_name, price | — |
| be_unique | product_id | — |
| be_between | price | 0.99 – 9,999.99 |
| be_between | stock_quantity | 0 – 10,000 |
| be_in_set | category | Electronics/Clothing/Food/Books/Sports |

---

## ▶️ How to Run Validations

### Full pipeline (recommended)
```bash
source venv/bin/activate
python main.py
```

### Skip data regeneration
```bash
python main.py --skip-data-gen
```

### Shell convenience wrapper
```bash
bash scripts/run_validations.sh
bash scripts/run_validations.sh --skip-data-gen
```

### Expected output
```
══════════════════════════════════════════════════════════════════════
  GREAT EXPECTATIONS — VALIDATION SUMMARY
══════════════════════════════════════════════════════════════════════
  Dataset                        Suite                               Pass  Fail    Pct  Status
──────────────────────────────────────────────────────────────────────────────────────────
  customers_asset                customers_quality_suite                9     0  100.0%  ✅ PASS
  orders_asset                   orders_quality_suite                   6     0  100.0%  ✅ PASS
  products_asset                 products_quality_suite                 5     0  100.0%  ✅ PASS
  dirty_customers_asset          customers_quality_suite                3     6   33.3%  ❌ FAIL
══════════════════════════════════════════════════════════════════════
```

---

## 📊 How to View Data Docs

After running validations, an HTML report is generated at:

```
gx/uncommitted/data_docs/local_site/index.html
```

**Open in browser:**
```bash
# Linux / Ubuntu
xdg-open gx/uncommitted/data_docs/local_site/index.html

# If xdg-open doesn't work in VMware
python3 -m http.server 8080 --directory gx/uncommitted/data_docs/local_site/
# Then open http://localhost:8080 in Firefox
```

---

## 🧪 How to Run Tests

```bash
source venv/bin/activate
pytest tests/ -v
```

**Expected output:**
```
tests/test_expectations.py::TestCleanCustomers::test_customers_clean_data_passes  PASSED
tests/test_expectations.py::TestCleanCustomers::test_customers_has_no_failures    PASSED
tests/test_expectations.py::TestDirtyCustomers::test_customers_dirty_data_fails   PASSED
tests/test_expectations.py::TestDirtyCustomers::test_dirty_data_has_failures      PASSED
tests/test_expectations.py::TestOrdersSuite::test_orders_suite_passes             PASSED
tests/test_expectations.py::TestProductsSuite::test_products_suite_passes         PASSED
tests/test_expectations.py::TestExpectationCounts::test_expectation_count         PASSED
tests/test_expectations.py::TestRowCountExpectation::test_row_count_expectation   PASSED

8 passed in X.XXs
```

---

## 🚀 Push to GitHub

```bash
bash scripts/push_to_github.sh YOUR_GITHUB_USERNAME great-expectations-poc ghp_YOUR_PAT_TOKEN
```

**Generating a PAT token:**
1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Click **Generate new token (classic)**
3. Select scopes: `repo`, `workflow`
4. Copy the token and pass it to the script

---

## 🔍 Troubleshooting

### `xdg-open` does nothing in VMware
The VM may not have a desktop environment configured for default apps.

**Solution:**
```bash
# Install xdg-utils
sudo apt-get install xdg-utils

# Or open via Python's HTTP server and host browser
python3 -m http.server 8080 --directory gx/uncommitted/data_docs/local_site/
# Open http://localhost:8080 in Firefox/Chrome on the VM
```

### `great_expectations` import errors
GX 0.18 requires Python 3.8–3.11. Verify your Python version:
```bash
python --version
# Should output: Python 3.10.x
```

If multiple Python versions are installed:
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Low memory / swap exhaustion in VMware
GX builds can be memory-intensive. Recommendations:
- Allocate ≥ 8 GB RAM to the VM in VMware settings
- Add swap space: `sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`

### `faker` import fails
```bash
pip install faker==22.7.0
```

### `FileNotFoundError` for CSV files
Run data generation first:
```bash
python -c "from src.data_generator import generate_all_datasets; generate_all_datasets(overwrite=True)"
```

### Permission denied on scripts
```bash
chmod +x scripts/*.sh
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-new-expectation`
3. Make your changes and add tests
4. Run the test suite: `pytest tests/ -v`
5. Commit with conventional commits: `git commit -m "feat: add cross-table FK validation"`
6. Push and open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**.  
See [LICENSE](LICENSE) for details.

---

## 📚 Resources

- [Great Expectations Documentation](https://docs.greatexpectations.io/docs/)
- [GX 0.18 Fluent API Migration Guide](https://docs.greatexpectations.io/docs/guides/miscellaneous/migration_guide)
- [Faker Documentation](https://faker.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
