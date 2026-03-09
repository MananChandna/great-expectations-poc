"""
data_generator.py — Synthetic dataset generator using Faker.

Generates three clean CSV datasets (customers, orders, products) and
one intentionally dirty dataset (customers_dirty) for testing the
Great Expectations validation pipeline.
"""

import random
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from faker import Faker

from src.utils import (
    get_data_bad_dir,
    get_data_raw_dir,
    ensure_directories,
    setup_logging,
)

logger = setup_logging(__name__)
fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# ─── Constants ────────────────────────────────────────────────────────────────

CUSTOMERS_COUNT = 1000
ORDERS_COUNT = 5000
PRODUCTS_COUNT = 200
DIRTY_CUSTOMERS_COUNT = 200

CATEGORIES = ["Electronics", "Clothing", "Food", "Books", "Sports"]
ORDER_STATUSES = ["pending", "shipped", "delivered", "cancelled"]


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _random_date(start: date, end: date) -> date:
    """Return a random date between start and end (inclusive).

    Args:
        start: Earliest possible date.
        end: Latest possible date.

    Returns:
        A randomly chosen date.
    """
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


# ─── Clean Datasets ───────────────────────────────────────────────────────────


def generate_customers(n: int = CUSTOMERS_COUNT) -> pd.DataFrame:
    """Generate a clean customers DataFrame.

    Args:
        n: Number of customer rows to generate.

    Returns:
        DataFrame with columns: customer_id, name, email, age, country,
        signup_date, is_active, credit_score.
    """
    logger.info("Generating %d clean customer records …", n)
    records = []
    for _ in range(n):
        records.append(
            {
                "customer_id": str(uuid.uuid4()),
                "name": fake.name(),
                "email": fake.unique.email(),
                "age": random.randint(18, 80),
                "country": fake.country(),
                "signup_date": str(
                    _random_date(date(2020, 1, 1), date(2024, 12, 31))
                ),
                "is_active": random.choice([True, False]),
                "credit_score": random.randint(300, 850),
            }
        )
    df = pd.DataFrame(records)
    logger.info("Customers dataset shape: %s", df.shape)
    return df


def generate_products(n: int = PRODUCTS_COUNT) -> pd.DataFrame:
    """Generate a clean products DataFrame.

    Args:
        n: Number of product rows to generate.

    Returns:
        DataFrame with columns: product_id, product_name, category, price,
        stock_quantity, supplier_id, is_available.
    """
    logger.info("Generating %d clean product records …", n)
    records = []
    for _ in range(n):
        records.append(
            {
                "product_id": str(uuid.uuid4()),
                "product_name": fake.catch_phrase(),
                "category": random.choice(CATEGORIES),
                "price": round(random.uniform(0.99, 9999.99), 2),
                "stock_quantity": random.randint(0, 10000),
                "supplier_id": str(uuid.uuid4()),
                "is_available": random.choice([True, False]),
            }
        )
    df = pd.DataFrame(records)
    logger.info("Products dataset shape: %s", df.shape)
    return df


def generate_orders(
    customer_ids: List[str], product_ids: List[str], n: int = ORDERS_COUNT
) -> pd.DataFrame:
    """Generate a clean orders DataFrame.

    Args:
        customer_ids: List of valid customer UUIDs to use as foreign keys.
        product_ids: List of valid product UUIDs to use as foreign keys.
        n: Number of order rows to generate.

    Returns:
        DataFrame with columns: order_id, customer_id, product_id,
        order_date, quantity, unit_price, status, discount_pct.
    """
    logger.info("Generating %d clean order records …", n)
    records = []
    for _ in range(n):
        records.append(
            {
                "order_id": str(uuid.uuid4()),
                "customer_id": random.choice(customer_ids),
                "product_id": random.choice(product_ids),
                "order_date": str(
                    _random_date(date(2020, 1, 1), date(2024, 12, 31))
                ),
                "quantity": random.randint(1, 50),
                "unit_price": round(random.uniform(0.99, 999.99), 2),
                "status": random.choice(ORDER_STATUSES),
                "discount_pct": round(random.uniform(0, 30), 2),
            }
        )
    df = pd.DataFrame(records)
    logger.info("Orders dataset shape: %s", df.shape)
    return df


# ─── Dirty Dataset ────────────────────────────────────────────────────────────


def generate_dirty_customers(n: int = DIRTY_CUSTOMERS_COUNT) -> pd.DataFrame:
    """Generate a dirty customers DataFrame with injected quality issues.

    Intentional issues injected:
    - 10 % null emails
    - 15 % ages out of range (negative or > 120)
    - 20 % duplicate customer_ids
    - 10 % malformed emails (missing @)
    - 5 % future signup_dates (after today)
    - credit_score values outside [300, 850]

    Args:
        n: Total number of rows (including dirty ones).

    Returns:
        DataFrame matching clean customers schema but with quality problems.
    """
    logger.info(
        "Generating %d dirty customer records (with intentional DQ issues) …", n
    )
    # Start with a clean base
    base = generate_customers(n)

    # Helper: randomly pick indices
    def _idx(frac: float) -> pd.Index:
        k = max(1, int(n * frac))
        return base.sample(n=k, random_state=random.randint(0, 9999)).index

    # 10 % null emails
    base.loc[_idx(0.10), "email"] = None

    # 10 % malformed emails (remove @)
    malformed_idx = _idx(0.10)
    base.loc[malformed_idx, "email"] = base.loc[malformed_idx, "email"].apply(
        lambda e: e.replace("@", "") if isinstance(e, str) else e
    )

    # 15 % ages out of range
    out_age_idx = _idx(0.15)
    base.loc[out_age_idx, "age"] = [
        random.choice([-5, -1, 0, 121, 150, 200])
        for _ in range(len(out_age_idx))
    ]

    # 20 % duplicate customer_ids
    dup_idx = _idx(0.20)
    existing_ids = base["customer_id"].dropna().tolist()
    base.loc[dup_idx, "customer_id"] = [
        random.choice(existing_ids) for _ in range(len(dup_idx))
    ]

    # 5 % future signup_dates
    future_idx = _idx(0.05)
    base.loc[future_idx, "signup_date"] = [
        str(_random_date(date(2025, 1, 1), date(2030, 12, 31)))
        for _ in range(len(future_idx))
    ]

    # credit_score outside 300-850
    bad_score_idx = _idx(0.10)
    base.loc[bad_score_idx, "credit_score"] = [
        random.choice([-100, 0, 100, 900, 1000, 1200])
        for _ in range(len(bad_score_idx))
    ]

    logger.info("Dirty customers dataset shape: %s", base.shape)
    return base


# ─── Orchestrator ─────────────────────────────────────────────────────────────


def generate_all_datasets(overwrite: bool = False) -> dict:
    """Generate and persist all datasets to disk.

    Skips generation for files that already exist unless overwrite=True.

    Args:
        overwrite: If True, regenerate all files even if they exist.

    Returns:
        Dictionary mapping dataset name → Path of saved CSV.
    """
    raw_dir = get_data_raw_dir()
    bad_dir = get_data_bad_dir()
    ensure_directories(raw_dir, bad_dir)

    paths = {
        "customers": raw_dir / "customers.csv",
        "orders": raw_dir / "orders.csv",
        "products": raw_dir / "products.csv",
        "customers_dirty": bad_dir / "customers_dirty.csv",
    }

    if not overwrite and all(p.exists() for p in paths.values()):
        logger.info("All datasets already exist — skipping generation.")
        return paths

    # Generate clean datasets
    customers_df = generate_customers()
    products_df = generate_products()
    orders_df = generate_orders(
        customer_ids=customers_df["customer_id"].tolist(),
        product_ids=products_df["product_id"].tolist(),
    )
    dirty_df = generate_dirty_customers()

    # Persist to disk
    customers_df.to_csv(paths["customers"], index=False)
    logger.info("Saved: %s", paths["customers"])

    products_df.to_csv(paths["products"], index=False)
    logger.info("Saved: %s", paths["products"])

    orders_df.to_csv(paths["orders"], index=False)
    logger.info("Saved: %s", paths["orders"])

    dirty_df.to_csv(paths["customers_dirty"], index=False)
    logger.info("Saved: %s", paths["customers_dirty"])

    return paths


if __name__ == "__main__":
    paths = generate_all_datasets(overwrite=True)
    print("\n✅ Datasets generated:")
    for name, path in paths.items():
        df = pd.read_csv(path)
        print(f"  {name:<25} → {path}  [{df.shape[0]} rows × {df.shape[1]} cols]")
