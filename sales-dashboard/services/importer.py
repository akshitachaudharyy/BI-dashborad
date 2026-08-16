import hashlib
import os

import pandas as pd

from database import db
from models import Sale, ImportBatch


# =========================================================
# Required source columns
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
# Calculate file SHA256
# =========================================================

def calculate_file_hash(file_path):

    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb"
    ) as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# =========================================================
# Read CSV / Excel
# =========================================================

def read_source_file(file_path):

    extension = os.path.splitext(
        file_path
    )[1].lower()

    if extension == ".csv":

        return pd.read_csv(
            file_path,
            dtype={
                "Order ID": "string",
                "ship-postal-code": "string"
            },
            low_memory=False
        )

    if extension in [
        ".xlsx",
        ".xls"
    ]:

        return pd.read_excel(
            file_path,
            dtype={
                "Order ID": "string",
                "ship-postal-code": "string"
            }
        )

    raise ValueError(
        "Unsupported file format. "
        "Only CSV, XLSX and XLS are supported."
    )


# =========================================================
# Validate source columns
# =========================================================

def validate_columns(df):

    actual_columns = {
        column.strip()
        for column in df.columns
    }

    missing_columns = (
        REQUIRED_COLUMNS - actual_columns
    )

    if missing_columns:

        raise ValueError(
            "Missing required columns:\n"
            + "\n".join(
                sorted(missing_columns)
            )
        )


# =========================================================
# Clean dataframe
# =========================================================

def clean_dataframe(df):

    # -----------------------------------------------------
    # Normalize column names
    # -----------------------------------------------------

    df.columns = [
        column.strip()
        for column in df.columns
    ]

    # -----------------------------------------------------
    # Remove completely empty columns
    # -----------------------------------------------------

    df = df.dropna(
        axis=1,
        how="all"
    )

    # -----------------------------------------------------
    # Column mapping
    # -----------------------------------------------------

    column_mapping = {

        "index":
            "source_index",

        "Order ID":
            "order_id",

        "Date":
            "order_date",

        "Status":
            "status",

        "Fulfilment":
            "fulfilment",

        "fulfilled-by":
            "fulfilled_by",

        "Sales Channel":
            "sales_channel",

        "ship-service-level":
            "ship_service_level",

        "Style":
            "style",

        "SKU":
            "sku",

        "Category":
            "category",

        "Size":
            "size",

        "ASIN":
            "asin",

        "Courier Status":
            "courier_status",

        "Qty":
            "quantity",

        "currency":
            "currency",

        "Amount":
            "amount",

        "ship-city":
            "ship_city",

        "ship-state":
            "ship_state",

        "ship-postal-code":
            "ship_postal_code",

        "ship-country":
            "ship_country",

        "promotion-ids":
            "promotion_ids",

        "B2B":
            "b2b"
    }

    df = df.rename(
        columns=column_mapping
    )

    # -----------------------------------------------------
    # Remove unnamed columns
    # -----------------------------------------------------

    unnamed_columns = [
        column
        for column in df.columns
        if column.lower().startswith("unnamed:")
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

    # -----------------------------------------------------
    # Date
    #
    # Amazon dataset format:
    # MM-DD-YY
    # Example:
    # 04-30-22
    # -----------------------------------------------------

    df["order_date"] = pd.to_datetime(
        df["order_date"],
        format="%m-%d-%y",
        errors="coerce"
    ).dt.date

    # -----------------------------------------------------
    # Quantity
    # -----------------------------------------------------

    df["quantity"] = pd.to_numeric(
        df["quantity"],
        errors="coerce"
    )

    df["quantity"] = (
        df["quantity"]
        .round()
        .astype("Int64")
    )

    # -----------------------------------------------------
    # Amount
    # -----------------------------------------------------

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    # -----------------------------------------------------
    # Postal code
    # -----------------------------------------------------

    df["ship_postal_code"] = (
        df["ship_postal_code"]
        .astype("string")
        .str.strip()
        .str.replace(
            r"\.0$",
            "",
            regex=True
        )
    )

    # -----------------------------------------------------
    # B2B
    # -----------------------------------------------------

    def convert_boolean(value):

        if pd.isna(value):
            return None

        if isinstance(
            value,
            bool
        ):
            return value

        value = str(value).strip().lower()

        if value in [
            "true",
            "1",
            "yes"
        ]:
            return True

        if value in [
            "false",
            "0",
            "no"
        ]:
            return False

        return None

    df["b2b"] = (
        df["b2b"]
        .apply(convert_boolean)
    )

    # -----------------------------------------------------
    # String columns
    # -----------------------------------------------------

    string_columns = [

        "order_id",
        "status",
        "fulfilment",
        "fulfilled_by",

        "sales_channel",
        "ship_service_level",

        "style",
        "sku",
        "category",
        "size",
        "asin",

        "courier_status",

        "currency",

        "ship_city",
        "ship_state",
        "ship_postal_code",
        "ship_country",

        "promotion_ids"
    ]

    for column in string_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

    # -----------------------------------------------------
    # Convert pandas NA to None
    # -----------------------------------------------------

    df = df.astype(object)

    df = df.where(
        pd.notna(df),
        None
    )

    return df


# =========================================================
# Validate cleaned data
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

    if missing_order_ids > 0:

        errors.append(
            f"{missing_order_ids:,} rows have "
            "missing Order ID."
        )

    # -----------------------------------------------------
    # Dates
    # -----------------------------------------------------

    invalid_dates = (
        df["order_date"]
        .isna()
        .sum()
    )

    if invalid_dates > 0:

        errors.append(
            f"{invalid_dates:,} rows have "
            "invalid dates."
        )

    # -----------------------------------------------------
    # Quantity
    # -----------------------------------------------------

    invalid_quantity = (
        df["quantity"]
        .isna()
        .sum()
    )

    if invalid_quantity > 0:

        errors.append(
            f"{invalid_quantity:,} rows have "
            "invalid quantity."
        )

    # -----------------------------------------------------
    # Amount
    #
    # Amount can legitimately be NULL for some records,
    # so we do NOT treat missing amount as a validation error.
    # -----------------------------------------------------

    # -----------------------------------------------------
    # Stop if errors exist
    # -----------------------------------------------------

    if errors:

        raise ValueError(
            "Data validation failed:\n"
            + "\n".join(errors)
        )


# =========================================================
# Convert dataframe → database records
# =========================================================

def dataframe_to_records(df):

    records = []

    for row in df.to_dict(
        orient="records"
    ):

        record = {

            "source_index":
                row.get("source_index"),

            "order_id":
                row.get("order_id"),

            "order_date":
                row.get("order_date"),

            "status":
                row.get("status"),

            "fulfilment":
                row.get("fulfilment"),

            "fulfilled_by":
                row.get("fulfilled_by"),

            "sales_channel":
                row.get("sales_channel"),

            "ship_service_level":
                row.get("ship_service_level"),

            "style":
                row.get("style"),

            "sku":
                row.get("sku"),

            "category":
                row.get("category"),

            "size":
                row.get("size"),

            "asin":
                row.get("asin"),

            "courier_status":
                row.get("courier_status"),

            "ship_city":
                row.get("ship_city"),

            "ship_state":
                row.get("ship_state"),

            "ship_postal_code":
                row.get("ship_postal_code"),

            "ship_country":
                row.get("ship_country"),

            "quantity":
                row.get("quantity"),

            "currency":
                row.get("currency"),

            "amount":
                row.get("amount"),

            "promotion_ids":
                row.get("promotion_ids"),

            "b2b":
                row.get("b2b")
        }

        records.append(record)

    return records


# =========================================================
# Import file
# =========================================================

def import_file(file_path):

    file_name = os.path.basename(
        file_path
    )

    print(
        f"Reading: {file_name}"
    )

    # -----------------------------------------------------
    # Hash
    # -----------------------------------------------------

    file_hash = calculate_file_hash(
        file_path
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
            "This file has already been imported "
            f"as batch #{existing_batch.id}."
        )

    # -----------------------------------------------------
    # Read
    # -----------------------------------------------------

    df = read_source_file(
        file_path
    )

    print(
        f"Rows loaded: {len(df):,}"
    )

    # -----------------------------------------------------
    # Validate source structure
    # -----------------------------------------------------

    validate_columns(df)

    # -----------------------------------------------------
    # Clean
    # -----------------------------------------------------

    df = clean_dataframe(df)

    # -----------------------------------------------------
    # Validate data
    # -----------------------------------------------------

    validate_data(df)

    # -----------------------------------------------------
    # Create import batch
    # -----------------------------------------------------

    batch = ImportBatch(

        file_name=file_name,

        file_hash=file_hash,

        row_count=len(df),

        status="processing"
    )

    db.session.add(batch)

    db.session.flush()

    # -----------------------------------------------------
    # Convert records
    # -----------------------------------------------------

    records = dataframe_to_records(
        df
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