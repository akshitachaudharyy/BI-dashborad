import hashlib
import os

import pandas as pd

from database import db
from models import Sale, ImportBatch


# =========================================================
# REQUIRED SOURCE COLUMNS
# =========================================================

REQUIRED_COLUMNS = {
    "Order ID",
    "Date",
    "Status",
    "Fulfilment",
    "Sales Channel",
    "ship-service-level",
    "Style",
    "SKU",
    "Category",
    "Size",
    "ASIN",
    "Courier Status",
    "Qty",
    "currency",
    "Amount",
    "ship-city",
    "ship-state",
    "ship-postal-code",
    "ship-country",
    "promotion-ids",
    "B2B",
    "fulfilled-by"
}


# =========================================================
# COLUMN MAPPING
# =========================================================

COLUMN_MAPPING = {
    "index": "source_index",

    "Order ID": "order_id",
    "Date": "order_date",
    "Status": "status",

    "Fulfilment": "fulfilment",
    "fulfilled-by": "fulfilled_by",
    "Courier Status": "courier_status",

    "Sales Channel": "sales_channel",
    "ship-service-level": "ship_service_level",

    "Style": "style",
    "SKU": "sku",
    "Category": "category",
    "Size": "size",
    "ASIN": "asin",

    "Qty": "quantity",
    "currency": "currency",
    "Amount": "amount",

    "ship-city": "ship_city",
    "ship-state": "ship_state",
    "ship-postal-code": "ship_postal_code",
    "ship-country": "ship_country",

    "promotion-ids": "promotion_ids",

    "B2B": "b2b"
}


# =========================================================
# FILE HASH
# =========================================================

def calculate_file_hash(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while True:

            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# =========================================================
# READ SOURCE FILE
# =========================================================

def read_source_file(file_path):

    extension = (
        os.path.splitext(file_path)[1]
        .lower()
    )

    if extension == ".csv":

        return pd.read_csv(
            file_path,
            dtype={
                "Order ID": "string",
                "ship-postal-code": "string"
            },
            low_memory=False
        )

    if extension in [".xlsx", ".xls"]:

        return pd.read_excel(
            file_path,
            dtype={
                "Order ID": "string",
                "ship-postal-code": "string"
            }
        )

    raise ValueError(
        "Unsupported file format. "
        "Use CSV, XLSX or XLS."
    )


# =========================================================
# NORMALIZE COLUMN NAMES
# =========================================================

def normalize_columns(df):

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    return df


# =========================================================
# VALIDATE SOURCE COLUMNS
# =========================================================

def validate_columns(df):

    actual_columns = set(df.columns)

    missing = (
        REQUIRED_COLUMNS - actual_columns
    )

    if missing:

        raise ValueError(
            "Missing required columns:\n"
            + "\n".join(sorted(missing))
        )


# =========================================================
# GENERIC STRING CLEANER
# =========================================================

def clean_string(value):

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except (TypeError, ValueError):

        pass

    value = str(value).strip()

    if not value:
        return None

    return value


# =========================================================
# UPPERCASE STRING
# =========================================================

def clean_upper(value):

    value = clean_string(value)

    if value is None:
        return None

    return value.upper()


# =========================================================
# TITLE CASE STRING
# =========================================================

def clean_title(value):

    value = clean_string(value)

    if value is None:
        return None

    return value.title()


# =========================================================
# POSTAL CODE
# =========================================================

def clean_postal_code(value):

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except (TypeError, ValueError):

        pass

    # -----------------------------------------------------
    # Float
    # -----------------------------------------------------

    if isinstance(value, float):

        if value.is_integer():

            return str(int(value))

        return str(value).strip()

    # -----------------------------------------------------
    # Integer
    # -----------------------------------------------------

    if isinstance(value, int):

        return str(value)

    # -----------------------------------------------------
    # Everything else → string
    # -----------------------------------------------------

    value = str(value).strip()

    if not value:
        return None

    # -----------------------------------------------------
    # Remove Excel-style ".0"
    # -----------------------------------------------------

    if value.endswith(".0"):

        numeric_part = value[:-2]

        if numeric_part.isdigit():

            return numeric_part

    return value


# =========================================================
# BOOLEAN
# =========================================================

def clean_boolean(value):

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except (TypeError, ValueError):

        pass

    if isinstance(value, bool):
        return value

    value = str(value).strip().lower()

    if value in ["true", "1", "yes", "y"]:
        return True

    if value in ["false", "0", "no", "n"]:
        return False

    return None


# =========================================================
# CLEAN DATAFRAME
# =========================================================

def clean_dataframe(df):

    # -----------------------------------------------------
    # Normalize columns
    # -----------------------------------------------------

    df = normalize_columns(df)

    # -----------------------------------------------------
    # Remove completely empty columns
    # -----------------------------------------------------

    df = df.dropna(
        axis=1,
        how="all"
    )

    # -----------------------------------------------------
    # Rename columns
    # -----------------------------------------------------

    df = df.rename(
        columns=COLUMN_MAPPING
    )

    # -----------------------------------------------------
    # Remove unnamed columns
    # -----------------------------------------------------

    unnamed_columns = [

        column

        for column in df.columns

        if str(column).lower().startswith(
            "unnamed:"
        )
    ]

    if unnamed_columns:

        df = df.drop(
            columns=unnamed_columns
        )

    # -----------------------------------------------------
    # Source index
    # -----------------------------------------------------

    if "source_index" not in df.columns:

        df["source_index"] = range(
            len(df)
        )

    # =====================================================
    # DATE
    # =====================================================

    df["order_date"] = pd.to_datetime(
        df["order_date"],
        format="%m-%d-%y",
        errors="coerce"
    ).dt.date

    # =====================================================
    # QUANTITY
    # =====================================================

    df["quantity"] = pd.to_numeric(
        df["quantity"],
        errors="coerce"
    )

    df["quantity"] = (
        df["quantity"]
        .round()
        .astype("Int64")
    )

    # =====================================================
    # AMOUNT
    # =====================================================

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    # =====================================================
    # POSTAL CODE
    # =====================================================

    df["ship_postal_code"] = (
        df["ship_postal_code"]
        .apply(clean_postal_code)
    )

    # =====================================================
    # B2B
    # =====================================================

    df["b2b"] = (
        df["b2b"]
        .apply(clean_boolean)
    )

    # =====================================================
    # STANDARD STRING FIELDS
    # =====================================================

    string_columns = [
        "order_id",
        "status",
        "fulfilment",
        "fulfilled_by",
        "courier_status",
        "sales_channel",
        "ship_service_level",
        "style",
        "sku",
        "size",
        "asin",
        "promotion_ids"
    ]

    for column in string_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(clean_string)
            )

    # =====================================================
    # CATEGORY
    # =====================================================

    if "category" in df.columns:

        df["category"] = (
            df["category"]
            .apply(clean_title)
        )

    # =====================================================
    # CITY
    # =====================================================

    if "ship_city" in df.columns:

        df["ship_city"] = (
            df["ship_city"]
            .apply(clean_upper)
        )

    # =====================================================
    # STATE
    # =====================================================

    if "ship_state" in df.columns:

        df["ship_state"] = (
            df["ship_state"]
            .apply(clean_upper)
        )

    # =====================================================
    # COUNTRY
    # =====================================================

    if "ship_country" in df.columns:

        df["ship_country"] = (
            df["ship_country"]
            .apply(clean_upper)
        )

    # =====================================================
    # CURRENCY
    # =====================================================

    if "currency" in df.columns:

        df["currency"] = (
            df["currency"]
            .apply(clean_upper)
        )

    # =====================================================
    # CONVERT PANDAS NA / NAN → NONE
    # =====================================================

    df = df.astype(object)

    df = df.where(
        pd.notna(df),
        None
    )

    return df


# =========================================================
# DATA VALIDATION
# =========================================================

def validate_data(df):

    errors = []

    # -----------------------------------------------------
    # Order ID
    # -----------------------------------------------------

    missing_order_ids = (
        df["order_id"]
        .isna()
        .sum()
    )

    if missing_order_ids:

        errors.append(
            f"{missing_order_ids:,} rows "
            "have missing Order ID."
        )

    # -----------------------------------------------------
    # Dates
    # -----------------------------------------------------

    invalid_dates = (
        df["order_date"]
        .isna()
        .sum()
    )

    if invalid_dates:

        errors.append(
            f"{invalid_dates:,} rows "
            "have invalid dates."
        )

    # -----------------------------------------------------
    # Quantity
    # -----------------------------------------------------

    invalid_quantity = (
        df["quantity"]
        .isna()
        .sum()
    )

    if invalid_quantity:

        errors.append(
            f"{invalid_quantity:,} rows "
            "have invalid quantity."
        )

    # -----------------------------------------------------
    # Negative quantity
    # -----------------------------------------------------

    negative_quantity = (
        df["quantity"].notna()
        &
        (df["quantity"] < 0)
    ).sum()

    if negative_quantity:

        errors.append(
            f"{negative_quantity:,} rows "
            "have negative quantity."
        )

    # -----------------------------------------------------
    # Missing amount
    # -----------------------------------------------------

    missing_amount = (
        df["amount"]
        .isna()
        .sum()
    )

    if missing_amount:

        print(
            "Warning: "
            f"{missing_amount:,} rows "
            "have missing amount."
        )

    # -----------------------------------------------------
    # Duplicate source indexes
    # -----------------------------------------------------

    duplicate_indexes = (
        df["source_index"]
        .duplicated()
        .sum()
    )

    if duplicate_indexes:

        errors.append(
            f"{duplicate_indexes:,} "
            "duplicate source indexes found."
        )

    # -----------------------------------------------------
    # Raise validation errors
    # -----------------------------------------------------

    if errors:

        raise ValueError(
            "Data validation failed:\n"
            + "\n".join(errors)
        )


# =========================================================
# DATA PROFILE
# =========================================================

def profile_data(df):

    print()
    print("=" * 60)
    print("DATA PROFILE")
    print("=" * 60)

    # -----------------------------------------------------
    # Basic information
    # -----------------------------------------------------

    print(
        f"Rows: {len(df):,}"
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    # -----------------------------------------------------
    # Date range
    # -----------------------------------------------------

    dates = (
        df["order_date"]
        .dropna()
    )

    if not dates.empty:

        print(
            f"Date range: "
            f"{dates.min()} → "
            f"{dates.max()}"
        )

    # -----------------------------------------------------
    # Status
    # -----------------------------------------------------

    print()
    print("ORDER STATUS")

    print(
        df["status"]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    # -----------------------------------------------------
    # Courier status
    # -----------------------------------------------------

    print()
    print("COURIER STATUS")

    print(
        df["courier_status"]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    # -----------------------------------------------------
    # Fulfilment
    # -----------------------------------------------------

    print()
    print("FULFILMENT")

    print(
        df["fulfilment"]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    # -----------------------------------------------------
    # Sales channel
    # -----------------------------------------------------

    print()
    print("SALES CHANNEL")

    print(
        df["sales_channel"]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    # -----------------------------------------------------
    # Category
    # -----------------------------------------------------

    print()
    print("CATEGORY")

    print(
        df["category"]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    # -----------------------------------------------------
    # Missing values
    # -----------------------------------------------------

    print()
    print("MISSING VALUES")

    missing = (
        df
        .isna()
        .sum()
        .sort_values(
            ascending=False
        )
    )

    missing = missing[
        missing > 0
    ]

    if missing.empty:

        print(
            "No missing values."
        )

    else:

        print(
            missing.to_string()
        )

    # -----------------------------------------------------
    # Duplicate order IDs
    # -----------------------------------------------------

    duplicate_orders = (
        df["order_id"]
        .duplicated(
            keep=False
        )
        .sum()
    )

    print()

    print(
        "Rows belonging to "
        "duplicate Order IDs: "
        f"{duplicate_orders:,}"
    )

    # -----------------------------------------------------
    # Cancelled analysis
    # -----------------------------------------------------

    cancelled = (
        df["status"]
        .fillna("")
        .astype(str)
        .str.lower()
        .eq("cancelled")
    )

    cancelled_count = int(
        cancelled.sum()
    )

    cancelled_with_amount = int(
        (
            cancelled
            &
            (
                df["amount"]
                .fillna(0)
                > 0
            )
        ).sum()
    )

    cancelled_with_zero_quantity = int(
        (
            cancelled
            &
            (
                df["quantity"]
                .fillna(0)
                == 0
            )
        ).sum()
    )

    print()

    print(
        "Cancelled rows: "
        f"{cancelled_count:,}"
    )

    print(
        "Cancelled rows with "
        "amount > 0: "
        f"{cancelled_with_amount:,}"
    )

    print(
        "Cancelled rows with "
        "quantity = 0: "
        f"{cancelled_with_zero_quantity:,}"
    )

    # -----------------------------------------------------
    # Quantity zero + amount positive
    # -----------------------------------------------------

    quantity_zero_amount_positive = int(
        (
            (
                df["quantity"]
                .fillna(0)
                == 0
            )
            &
            (
                df["amount"]
                .fillna(0)
                > 0
            )
        ).sum()
    )

    print()

    print(
        "Rows with quantity = 0 "
        "and amount > 0: "
        f"{quantity_zero_amount_positive:,}"
    )

    # -----------------------------------------------------
    # Quantity positive + amount missing
    # -----------------------------------------------------

    quantity_positive_amount_missing = int(
        (
            (
                df["quantity"]
                .fillna(0)
                > 0
            )
            &
            df["amount"].isna()
        ).sum()
    )

    print(
        "Rows with quantity > 0 "
        "and missing amount: "
        f"{quantity_positive_amount_missing:,}"
    )

    print("=" * 60)
    print()


# =========================================================
# IMPORT FILE
# =========================================================

def import_file(
    file_path,
    profile=True
):

    file_name = os.path.basename(
        file_path
    )

    print(
        f"Reading: {file_name}"
    )

    # -----------------------------------------------------
    # File hash
    # -----------------------------------------------------

    file_hash = (
        calculate_file_hash(
            file_path
        )
    )

    # -----------------------------------------------------
    # Duplicate file check
    # -----------------------------------------------------

    existing_batch = (
        ImportBatch.query
        .filter_by(
            file_hash=file_hash
        )
        .first()
    )

    if existing_batch:

        raise ValueError(
            "This file has already been "
            f"imported as batch "
            f"#{existing_batch.id}."
        )

    # -----------------------------------------------------
    # Read file
    # -----------------------------------------------------

    df = read_source_file(
        file_path
    )

    print(
        f"Rows loaded: "
        f"{len(df):,}"
    )

    # -----------------------------------------------------
    # Normalize columns
    # -----------------------------------------------------

    df = normalize_columns(
        df
    )

    # -----------------------------------------------------
    # Validate columns
    # -----------------------------------------------------

    validate_columns(
        df
    )

    # -----------------------------------------------------
    # Clean
    # -----------------------------------------------------

    df = clean_dataframe(
        df
    )

    # -----------------------------------------------------
    # Profile
    # -----------------------------------------------------

    if profile:

        profile_data(
            df
        )

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    validate_data(
        df
    )

    # -----------------------------------------------------
    # Create batch
    # -----------------------------------------------------

    batch = ImportBatch(

        file_name=file_name,

        file_hash=file_hash,

        row_count=len(df),

        status="processing"
    )

    db.session.add(
        batch
    )

    db.session.flush()

    # -----------------------------------------------------
    # Convert DataFrame to records
    # -----------------------------------------------------

    records = df.to_dict(
        orient="records"
    )

    # -----------------------------------------------------
    # Insert
    # -----------------------------------------------------

    chunk_size = 5000

    try:

        for start in range(
            0,
            len(records),
            chunk_size
        ):

            chunk = records[
                start:start + chunk_size
            ]

            db.session.bulk_insert_mappings(
                Sale,
                chunk
            )

            inserted = min(
                start + chunk_size,
                len(records)
            )

            print(
                f"Inserted "
                f"{inserted:,}/"
                f"{len(records):,}"
            )

        # -------------------------------------------------
        # Complete batch
        # -------------------------------------------------

        batch.status = "completed"

        db.session.commit()

        print()
        print(
            f"Import completed: "
            f"{len(records):,} rows"
        )

        return {

            "success": True,

            "batch_id":
                batch.id,

            "file_name":
                file_name,

            "rows_imported":
                len(records)
        }

    except Exception:

        db.session.rollback()

        raise