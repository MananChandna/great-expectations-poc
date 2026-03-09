"""
main.py — Orchestrator entry point for the Great Expectations POC.

Usage:
    python main.py              # Run everything (including data generation)
    python main.py --skip-data-gen  # Skip CSV generation if files already exist
"""

import argparse
import sys
from pathlib import Path

from src.utils import setup_logging, print_separator, get_gx_context_dir
from src.data_generator import generate_all_datasets
from src.gx_setup import setup_gx
from src.expectations_builder import build_all_suites
from src.checkpoint_runner import run_all_validations, build_data_docs

logger = setup_logging("main")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Great Expectations POC — Data Quality Framework"
    )
    parser.add_argument(
        "--skip-data-gen",
        action="store_true",
        default=False,
        help="Skip synthetic data generation if CSV files already exist.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the full GX POC pipeline.

    Pipeline steps:
    1. Generate synthetic datasets (unless --skip-data-gen)
    2. Initialise GX context and register datasources
    3. Build all expectation suites
    4. Run all validations (clean + dirty)
    5. Build Data Docs
    6. Print final summary

    Returns:
        Exit code: 0 for success, 1 for any failure.
    """
    args = parse_args()

    print_separator("═")
    print("  🚀 GREAT EXPECTATIONS POC — DATA QUALITY FRAMEWORK")
    print_separator("═")

    # ── Step 1: Data generation ───────────────────────────────────────────────
    if not args.skip_data_gen:
        logger.info("Step 1/5 — Generating synthetic datasets …")
        try:
            paths = generate_all_datasets(overwrite=False)
            print("\n✅ Step 1 complete: Datasets ready")
            for name, path in paths.items():
                print(f"   {name:<25} → {path}")
        except Exception as exc:
            logger.error("Data generation failed: %s", exc, exc_info=True)
            return 1
    else:
        print("\n⏭  Step 1 skipped: --skip-data-gen flag set")

    # ── Step 2: GX context setup ──────────────────────────────────────────────
    logger.info("Step 2/5 — Initialising GX context …")
    try:
        context, assets = setup_gx()
        print(f"\n✅ Step 2 complete: GX context loaded from {get_gx_context_dir()}")
    except Exception as exc:
        logger.error("GX context setup failed: %s", exc, exc_info=True)
        return 1

    # ── Step 3: Build expectation suites ─────────────────────────────────────
    logger.info("Step 3/5 — Building expectation suites …")
    try:
        suites = build_all_suites(context)
        total_expectations = sum(len(s.expectations) for s in suites.values())
        print(f"\n✅ Step 3 complete: {len(suites)} suites built, {total_expectations} total expectations")
        for name, suite in suites.items():
            print(f"   {name:<40} → {len(suite.expectations):2d} expectations")
    except Exception as exc:
        logger.error("Suite building failed: %s", exc, exc_info=True)
        return 1

    # ── Step 4: Run validations ───────────────────────────────────────────────
    logger.info("Step 4/5 — Running all checkpoints …")
    try:
        results = run_all_validations(context)
        clean_results = [r for r in results if r["dataset"] != "dirty_customers_asset"]
        dirty_results = [r for r in results if r["dataset"] == "dirty_customers_asset"]

        all_clean_pass = all(r["success"] for r in clean_results)
        dirty_fails = not dirty_results[0]["success"] if dirty_results else False

        print(f"\n✅ Step 4 complete: Validations run")
        print(f"   Clean datasets all PASS : {'✅' if all_clean_pass else '❌'}")
        print(f"   Dirty data detected FAIL: {'✅' if dirty_fails else '❌'}")
    except Exception as exc:
        logger.error("Validation run failed: %s", exc, exc_info=True)
        return 1

    # ── Step 5: Build Data Docs ───────────────────────────────────────────────
    logger.info("Step 5/5 — Building GX Data Docs …")
    try:
        docs_path = build_data_docs(context)
        print(f"\n✅ Step 5 complete: Data Docs generated")
    except Exception as exc:
        logger.warning("Data Docs build failed (non-fatal): %s", exc)
        docs_path = (
            get_gx_context_dir()
            / "uncommitted"
            / "data_docs"
            / "local_site"
            / "index.html"
        )

    # ── Final summary ─────────────────────────────────────────────────────────
    print_separator("═")
    print("  🎉 POC COMPLETE — ALL STEPS FINISHED")
    print_separator("═")
    print(f"\n  📊 View Data Docs in your browser:")
    print(f"     xdg-open '{docs_path}'")
    print(f"     — or navigate to: file://{docs_path.resolve()}\n")
    print_separator("─")
    print("  Next steps:")
    print("  • Run tests      : pytest tests/ -v")
    print("  • Explore data   : jupyter notebook notebooks/explore_data_quality.ipynb")
    print("  • Push to GitHub : bash scripts/push_to_github.sh <user> <repo> <token>")
    print_separator("═")

    return 0


if __name__ == "__main__":
    sys.exit(main())
