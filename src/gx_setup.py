"""
gx_setup.py - Great Expectations context initialisation.
"""

from pathlib import Path
import great_expectations as gx
from src.utils import (
    get_gx_context_dir,
    get_data_raw_dir,
    get_data_bad_dir,
    ensure_directories,
    setup_logging,
)

logger = setup_logging(__name__)

DATASOURCE_CUSTOMERS = "customers_datasource"
DATASOURCE_ORDERS    = "orders_datasource"
DATASOURCE_PRODUCTS  = "products_datasource"
DATASOURCE_DIRTY     = "dirty_customers_datasource"

ASSET_CUSTOMERS = "customers_asset"
ASSET_ORDERS    = "orders_asset"
ASSET_PRODUCTS  = "products_asset"
ASSET_DIRTY     = "dirty_customers_asset"


def _bootstrap_gx_yml(gx_dir: Path) -> None:
    """Write a minimal great_expectations.yml if one does not exist."""
    yml_path = gx_dir / "great_expectations.yml"
    if yml_path.exists():
        return
    ensure_directories(
        gx_dir / "expectations",
        gx_dir / "checkpoints",
        gx_dir / "uncommitted" / "validations",
        gx_dir / "uncommitted" / "data_docs" / "local_site",
    )
    yml_content = """config_version: 3.0
datasources: {}
stores:
  expectations_store:
    class_name: ExpectationsStore
    store_backend:
      class_name: TupleFilesystemStoreBackend
      base_directory: expectations/
  validations_store:
    class_name: ValidationsStore
    store_backend:
      class_name: TupleFilesystemStoreBackend
      base_directory: uncommitted/validations/
  evaluation_parameter_store:
    class_name: EvaluationParameterStore
  checkpoint_store:
    class_name: CheckpointStore
    store_backend:
      class_name: TupleFilesystemStoreBackend
      suppress_store_backend_id: true
      base_directory: checkpoints/
  profiler_store:
    class_name: ProfilerStore
    store_backend:
      class_name: TupleFilesystemStoreBackend
      suppress_store_backend_id: true
      base_directory: profilers/
expectations_store_name: expectations_store
validations_store_name: validations_store
evaluation_parameter_store_name: evaluation_parameter_store
checkpoint_store_name: checkpoint_store
profiler_store_name: profiler_store
data_docs_sites:
  local_site:
    class_name: SiteBuilder
    show_how_to_buttons: true
    store_backend:
      class_name: TupleFilesystemStoreBackend
      base_directory: uncommitted/data_docs/local_site/
    site_index_builder:
      class_name: DefaultSiteIndexBuilder
anonymous_usage_statistics:
  enabled: false
"""
    yml_path.write_text(yml_content)
    logger.info("Created great_expectations.yml at %s", yml_path)


def get_context():
    """Initialise and return a GX context."""
    gx_dir = get_gx_context_dir()
    _bootstrap_gx_yml(gx_dir)
    logger.info("Loading GX context from %s", gx_dir)
    try:
        context = gx.get_context(context_root_dir=str(gx_dir))
        logger.info("GX context loaded successfully.")
        return context
    except Exception as exc:
        logger.error("Failed to load GX context: %s", exc, exc_info=True)
        raise


def _add_datasource_and_asset(context, ds_name, base_dir, csv_filename, asset_name):
    """Register one datasource + CSV asset using the correct GX 0.18 API."""

    # Step 1: get or create datasource
    try:
        ds = context.datasources[ds_name]
        logger.debug("Datasource '%s' already registered.", ds_name)
    except (KeyError, AttributeError):
        logger.info("Registering datasource '%s'", ds_name)
        ds = context.sources.add_pandas_filesystem(
            name=ds_name,
            base_directory=str(base_dir),
        )

    # Step 2: get or create asset
    # GX 0.18 PandasFilesystemDatasource uses batching_regex to match files
    try:
        asset = ds.get_asset(asset_name)
        logger.debug("Asset '%s' already registered.", asset_name)
    except (LookupError, Exception):
        import re
        # Escape the filename so it matches exactly one file
        escaped = re.escape(csv_filename)
        asset = ds.add_csv_asset(
            name=asset_name,
            batching_regex=escaped,
        )
        logger.info("Registered asset '%s' -> %s/%s", asset_name, base_dir, csv_filename)

    return asset


def register_datasources(context) -> dict:
    """Register all PandasFilesystem datasources and data assets."""
    raw_dir = get_data_raw_dir()
    bad_dir = get_data_bad_dir()

    assets = {}
    configs = [
        (DATASOURCE_CUSTOMERS, raw_dir, "customers.csv",       ASSET_CUSTOMERS),
        (DATASOURCE_ORDERS,    raw_dir, "orders.csv",          ASSET_ORDERS),
        (DATASOURCE_PRODUCTS,  raw_dir, "products.csv",        ASSET_PRODUCTS),
        (DATASOURCE_DIRTY,     bad_dir, "customers_dirty.csv", ASSET_DIRTY),
    ]
    for ds_name, base_dir, csv_file, asset_name in configs:
        assets[asset_name] = _add_datasource_and_asset(
            context, ds_name, base_dir, csv_file, asset_name
        )

    logger.info("All %d datasources/assets registered.", len(assets))
    return assets


def setup_gx() -> tuple:
    """Convenience wrapper: initialise context and register all datasources."""
    context = get_context()
    assets  = register_datasources(context)
    return context, assets
