"""
test_expectations.py — Pytest test suite for GX validations.

Tests cover:
- Clean customers data → all expectations pass
- Dirty customers data → failures detected
- Orders and products suites pass on clean data
- Each suite has the expected number of expectations
- Row count expectation fires correctly
"""

import pytest

from src.data_generator import generate_all_datasets
from src.expectations_builder import (
    SUITE_CUSTOMERS,
    SUITE_ORDERS,
    SUITE_PRODUCTS,
    build_all_suites,
)
from src.gx_setup import setup_gx
from src.checkpoint_runner import (
    run_clean_validations,
    run_dirty_validation,
    _run_validation,
    DATASOURCE_CUSTOMERS,
    ASSET_CUSTOMERS,
    DATASOURCE_DIRTY,
    ASSET_DIRTY,
    DATASOURCE_ORDERS,
    ASSET_ORDERS,
    DATASOURCE_PRODUCTS,
    ASSET_PRODUCTS,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def gx_context():
    """Provide a fully configured GX context for the test session."""
    generate_all_datasets(overwrite=False)
    context, _ = setup_gx()
    build_all_suites(context)
    return context


@pytest.fixture(scope="session")
def clean_results(gx_context):
    """Run clean-data validations once and cache results."""
    return run_clean_validations(gx_context)


@pytest.fixture(scope="session")
def dirty_result(gx_context):
    """Run dirty-data validation once and cache result."""
    return run_dirty_validation(gx_context)


# ─── Tests ────────────────────────────────────────────────────────────────────


class TestCleanCustomers:
    """Validations against clean customers.csv must all pass."""

    def test_customers_clean_data_passes(self, clean_results):
        """Clean customers data should satisfy all expectations."""
        customers = next(r for r in clean_results if r["dataset"] == ASSET_CUSTOMERS)
        assert customers["success"] is True, (
            f"Expected PASS but got {customers['unsuccessful']} failures."
        )

    def test_customers_has_no_failures(self, clean_results):
        """Zero unsuccessful expectations for clean customers."""
        customers = next(r for r in clean_results if r["dataset"] == ASSET_CUSTOMERS)
        assert customers["unsuccessful"] == 0


class TestDirtyCustomers:
    """Validations against customers_dirty.csv must detect failures."""

    def test_customers_dirty_data_fails(self, dirty_result):
        """Dirty customers data should NOT pass overall validation."""
        assert dirty_result["success"] is False, (
            "Expected dirty data to FAIL but it passed."
        )

    def test_dirty_data_has_failures(self, dirty_result):
        """At least one expectation must fail on dirty data."""
        assert dirty_result["unsuccessful"] > 0, (
            "Expected at least one failed expectation on dirty data."
        )


class TestOrdersSuite:
    """Validations against clean orders.csv must all pass."""

    def test_orders_suite_passes(self, clean_results):
        """Clean orders data should satisfy all expectations."""
        orders = next(r for r in clean_results if r["dataset"] == ASSET_ORDERS)
        assert orders["success"] is True, (
            f"Expected PASS but got {orders['unsuccessful']} failures."
        )


class TestProductsSuite:
    """Validations against clean products.csv must all pass."""

    def test_products_suite_passes(self, clean_results):
        """Clean products data should satisfy all expectations."""
        products = next(r for r in clean_results if r["dataset"] == ASSET_PRODUCTS)
        assert products["success"] is True, (
            f"Expected PASS but got {products['unsuccessful']} failures."
        )


class TestExpectationCounts:
    """Each suite must contain the expected number of expectations."""

    # Expected counts per suite
    EXPECTED_COUNTS = {
        SUITE_CUSTOMERS: 9,   # not-null×3, unique×2, between×2, regex, in_set, parseable, row_count, proportion
        SUITE_ORDERS: 6,      # not-null×3, unique, between×3, in_set
        SUITE_PRODUCTS: 5,    # not-null×3, unique, between×2, in_set
    }

    def test_expectation_count(self, gx_context):
        """All suites must have at least the minimum expected expectation count."""
        for suite_name, min_count in self.EXPECTED_COUNTS.items():
            suite = gx_context.get_expectation_suite(
                expectation_suite_name=suite_name
            )
            actual = len(suite.expectations)
            assert actual >= min_count, (
                f"Suite '{suite_name}': expected >= {min_count} "
                f"expectations, got {actual}."
            )


class TestRowCountExpectation:
    """Row count expectation must behave correctly."""

    def test_row_count_expectation(self, gx_context):
        """Customers dataset row count must fall within [800, 1200]."""
        result = _run_validation(
            gx_context,
            DATASOURCE_CUSTOMERS,
            ASSET_CUSTOMERS,
            SUITE_CUSTOMERS,
        )
        # Find the row count expectation result
        row_count_results = [
            r
            for r in result["raw_result"].get("results", [])
            if r.get("expectation_config", {}).get("expectation_type")
            == "expect_table_row_count_to_be_between"
        ]
        assert len(row_count_results) > 0, "Row count expectation not found in results."
        assert row_count_results[0]["success"] is True, (
            "Row count expectation should PASS for 1000-row customers dataset."
        )
