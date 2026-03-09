"""
checkpoint_runner.py - Checkpoint execution and result reporting.
"""

import json
from pathlib import Path
import great_expectations as gx
from src.expectations_builder import SUITE_CUSTOMERS, SUITE_ORDERS, SUITE_PRODUCTS
from src.gx_setup import (
    ASSET_CUSTOMERS, ASSET_DIRTY, ASSET_ORDERS, ASSET_PRODUCTS,
    DATASOURCE_CUSTOMERS, DATASOURCE_DIRTY, DATASOURCE_ORDERS, DATASOURCE_PRODUCTS,
)
from src.utils import get_gx_context_dir, ensure_directories, print_separator, setup_logging

logger = setup_logging(__name__)


def _run_validation(context, datasource_name: str, asset_name: str, suite_name: str) -> dict:
    """Run a single validation and return a result dict."""
    logger.info("Validating '%s' against suite '%s' ...", asset_name, suite_name)
    try:
        datasource   = context.datasources[datasource_name]
        asset        = datasource.get_asset(asset_name)
        batch_request = asset.build_batch_request()
        validator    = context.get_validator(
            batch_request=batch_request,
            expectation_suite_name=suite_name,
        )
        result = validator.validate()
        stats  = result["statistics"]
        return {
            "dataset":      asset_name,
            "suite":        suite_name,
            "success":      result["success"],
            "evaluated":    stats.get("evaluated_expectations", 0),
            "successful":   stats.get("successful_expectations", 0),
            "unsuccessful": stats.get("unsuccessful_expectations", 0),
            "success_pct":  round(stats.get("success_percent") or 0.0, 1),
            "raw_result":   result.to_json_dict(),
        }
    except Exception as exc:
        logger.error("Validation failed for '%s': %s", asset_name, exc, exc_info=True)
        return {
            "dataset": asset_name, "suite": suite_name, "success": False,
            "evaluated": 0, "successful": 0, "unsuccessful": 0,
            "success_pct": 0.0, "raw_result": {"error": str(exc)},
        }


def _save_result(result: dict, filename: str) -> Path:
    """Persist a validation result dict as JSON."""
    validations_dir = get_gx_context_dir() / "uncommitted" / "validations"
    ensure_directories(validations_dir)
    out_path = validations_dir / filename
    with out_path.open("w") as fh:
        json.dump(result, fh, indent=2, default=str)
    logger.info("Result saved -> %s", out_path)
    return out_path


def _print_summary(results: list) -> None:
    """Print a human-readable validation summary table."""
    print_separator()
    print("  GREAT EXPECTATIONS - VALIDATION SUMMARY")
    print_separator()
    print(f"  {'Dataset':<30} {'Suite':<35} {'Pass':>5} {'Fail':>5} {'Pct':>6}  Status")
    print_separator(char="-")
    for r in results:
        icon = "PASS" if r["success"] else "FAIL"
        print(
            f"  {r['dataset']:<30} {r['suite']:<35} "
            f"{r['successful']:>5} {r['unsuccessful']:>5} "
            f"{r['success_pct']:>5.1f}%  {icon}"
        )
    print_separator()


def build_data_docs(context) -> Path:
    """Build GX Data Docs HTML report."""
    logger.info("Building GX Data Docs ...")
    try:
        context.build_data_docs()
    except Exception as exc:
        logger.warning("Data Docs build warning: %s", exc)
    docs_path = (
        get_gx_context_dir() / "uncommitted" / "data_docs" / "local_site" / "index.html"
    )
    logger.info("Data Docs at: %s", docs_path)
    return docs_path


def run_all_validations(context) -> list:
    """Run all validations (clean + dirty) and return results."""
    configs = [
        (DATASOURCE_CUSTOMERS, ASSET_CUSTOMERS, SUITE_CUSTOMERS, "customers_clean.json"),
        (DATASOURCE_ORDERS,    ASSET_ORDERS,    SUITE_ORDERS,    "orders_clean.json"),
        (DATASOURCE_PRODUCTS,  ASSET_PRODUCTS,  SUITE_PRODUCTS,  "products_clean.json"),
        (DATASOURCE_DIRTY,     ASSET_DIRTY,     SUITE_CUSTOMERS, "customers_dirty.json"),
    ]
    results = []
    for ds_name, asset_name, suite_name, filename in configs:
        result = _run_validation(context, ds_name, asset_name, suite_name)
        _save_result(result, filename)
        results.append(result)
    _print_summary(results)
    return results


def run_clean_validations(context) -> list:
    """Run validations on clean datasets only."""
    configs = [
        (DATASOURCE_CUSTOMERS, ASSET_CUSTOMERS, SUITE_CUSTOMERS),
        (DATASOURCE_ORDERS,    ASSET_ORDERS,    SUITE_ORDERS),
        (DATASOURCE_PRODUCTS,  ASSET_PRODUCTS,  SUITE_PRODUCTS),
    ]
    return [_run_validation(context, ds, asset, suite) for ds, asset, suite in configs]


def run_dirty_validation(context) -> dict:
    """Run validation on the dirty customers dataset."""
    return _run_validation(context, DATASOURCE_DIRTY, ASSET_DIRTY, SUITE_CUSTOMERS)
