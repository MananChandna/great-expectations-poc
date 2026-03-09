"""
expectations_builder.py - Programmatic expectation suite builder.
Builds three expectation suites using the GX 0.18 fluent API.
"""

import great_expectations as gx
from great_expectations.core import ExpectationSuite, ExpectationConfiguration
from src.utils import setup_logging

logger = setup_logging(__name__)

SUITE_CUSTOMERS = "customers_quality_suite"
SUITE_ORDERS    = "orders_quality_suite"
SUITE_PRODUCTS  = "products_quality_suite"

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


def _get_or_create_suite(context, suite_name: str) -> ExpectationSuite:
    """Retrieve an existing suite or create a new empty one."""
    try:
        suite = context.get_expectation_suite(expectation_suite_name=suite_name)
        logger.debug("Loaded existing suite '%s'.", suite_name)
    except Exception:
        suite = context.add_expectation_suite(expectation_suite_name=suite_name)
        logger.info("Created new suite '%s'.", suite_name)
    return suite


def build_customers_suite(context) -> ExpectationSuite:
    """Build and persist the customers quality expectation suite."""
    logger.info("Building suite '%s' ...", SUITE_CUSTOMERS)
    suite = _get_or_create_suite(context, SUITE_CUSTOMERS)
    suite.expectations = []

    # Not-null
    for col in ["customer_id", "email", "name"]:
        suite.add_expectation(ExpectationConfiguration(
            expectation_type="expect_column_values_to_not_be_null",
            kwargs={"column": col},
        ))

    # Uniqueness
    for col in ["customer_id", "email"]:
        suite.add_expectation(ExpectationConfiguration(
            expectation_type="expect_column_values_to_be_unique",
            kwargs={"column": col},
        ))

    # Age range
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_between",
        kwargs={"column": "age", "min_value": 18, "max_value": 80},
    ))

    # Email regex
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_match_regex",
        kwargs={"column": "email", "regex": EMAIL_REGEX},
    ))

    # Credit score range
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_between",
        kwargs={"column": "credit_score", "min_value": 300, "max_value": 850},
    ))

    # is_active value set
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_in_set",
        kwargs={"column": "is_active", "value_set": [True, False]},
    ))

    # signup_date parseable
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_dateutil_parseable",
        kwargs={"column": "signup_date"},
    ))

    # Row count
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_table_row_count_to_be_between",
        kwargs={"min_value": 800, "max_value": 1200},
    ))

    # Proportion of unique values
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_proportion_of_unique_values_to_be_between",
        kwargs={"column": "customer_id", "min_value": 0.99, "max_value": 1.0},
    ))

    context.save_expectation_suite(expectation_suite=suite)
    logger.info("Suite '%s' saved with %d expectations.", SUITE_CUSTOMERS, len(suite.expectations))
    return suite


def build_orders_suite(context) -> ExpectationSuite:
    """Build and persist the orders quality expectation suite."""
    logger.info("Building suite '%s' ...", SUITE_ORDERS)
    suite = _get_or_create_suite(context, SUITE_ORDERS)
    suite.expectations = []

    # Not-null
    for col in ["order_id", "customer_id", "order_date"]:
        suite.add_expectation(ExpectationConfiguration(
            expectation_type="expect_column_values_to_not_be_null",
            kwargs={"column": col},
        ))

    # Uniqueness
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_unique",
        kwargs={"column": "order_id"},
    ))

    # Quantity range
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_between",
        kwargs={"column": "quantity", "min_value": 1, "max_value": 50},
    ))

    # Unit price range
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_between",
        kwargs={"column": "unit_price", "min_value": 0.99, "max_value": 999.99},
    ))

    # Status value set
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_in_set",
        kwargs={"column": "status", "value_set": ["pending", "shipped", "delivered", "cancelled"]},
    ))

    # Discount range
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_between",
        kwargs={"column": "discount_pct", "min_value": 0, "max_value": 30},
    ))

    context.save_expectation_suite(expectation_suite=suite)
    logger.info("Suite '%s' saved with %d expectations.", SUITE_ORDERS, len(suite.expectations))
    return suite


def build_products_suite(context) -> ExpectationSuite:
    """Build and persist the products quality expectation suite."""
    logger.info("Building suite '%s' ...", SUITE_PRODUCTS)
    suite = _get_or_create_suite(context, SUITE_PRODUCTS)
    suite.expectations = []

    # Not-null
    for col in ["product_id", "product_name", "price"]:
        suite.add_expectation(ExpectationConfiguration(
            expectation_type="expect_column_values_to_not_be_null",
            kwargs={"column": col},
        ))

    # Uniqueness
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_unique",
        kwargs={"column": "product_id"},
    ))

    # Price range
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_between",
        kwargs={"column": "price", "min_value": 0.99, "max_value": 9999.99},
    ))

    # Stock quantity range
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_between",
        kwargs={"column": "stock_quantity", "min_value": 0, "max_value": 10000},
    ))

    # Category value set
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_in_set",
        kwargs={"column": "category", "value_set": ["Electronics", "Clothing", "Food", "Books", "Sports"]},
    ))

    context.save_expectation_suite(expectation_suite=suite)
    logger.info("Suite '%s' saved with %d expectations.", SUITE_PRODUCTS, len(suite.expectations))
    return suite


def build_all_suites(context) -> dict:
    """Build all three expectation suites and return them."""
    suites = {
        SUITE_CUSTOMERS: build_customers_suite(context),
        SUITE_ORDERS:    build_orders_suite(context),
        SUITE_PRODUCTS:  build_products_suite(context),
    }
    total = sum(len(s.expectations) for s in suites.values())
    logger.info("All suites built. Total expectations: %d", total)
    return suites
