"""
=========================================================
DASHBOARD API / BI TEST SUITE
=========================================================

Self-contained runner -- no pytest dependency required.

Run from the sales-dashboard directory:

    python -m scripts.test_dashboard

Exits non-zero if any check fails, so it can be used in CI.

Covers the Phase 3 checklist:

     1. unfiltered dashboard
     2. date filter
     3. status filter
     4. category filter
     5. state filter
     6. fulfilment filter
     7. sales channel filter
     8. multiple filters simultaneously
     9. invalid dates
    10. empty filter result
    11. cancelled orders
    12. duplicate order IDs

plus the BI invariants:

    gross_sales >= net_sales
    gross_sales == net_sales + cancelled_value
    total_orders uses COUNT(DISTINCT order_id)
    every chart endpoint honours the same filters
"""

import sys

from sqlalchemy import text

from app import app
from database import db


# =========================================================
# TINY TEST HARNESS
# =========================================================

class Results:

    def __init__(self):
        self.passed = 0
        self.failed = []

    def check(self, label, condition, detail=""):

        if condition:
            self.passed += 1
            print(f"  PASS  {label}")
        else:
            self.failed.append(label)
            print(f"  FAIL  {label}  {detail}")

    def section(self, title):
        print()
        print(f"--- {title} ---")

    def report(self):

        print()
        print("=" * 58)
        total = self.passed + len(self.failed)
        print(f"  {self.passed}/{total} checks passed")

        if self.failed:
            print()
            for label in self.failed:
                print(f"  FAILED: {label}")

        print("=" * 58)

        return 0 if not self.failed else 1


results = Results()


# =========================================================
# HELPERS
# =========================================================

def get(client, path):
    """GET a JSON endpoint, returning (status, payload)."""

    response = client.get(path)

    return response.status_code, response.get_json()


def summary(client, query=""):

    status, payload = get(
        client,
        "/api/dashboard/summary" + query
    )

    return payload.get("data", {})


def scalar(sql):

    return db.session.execute(text(sql)).scalar()


# =========================================================
# TESTS
# =========================================================

def run():

    client = app.test_client()

    # -----------------------------------------------------
    # 1. Unfiltered dashboard
    # -----------------------------------------------------

    results.section("1. Unfiltered dashboard")

    status, payload = get(client, "/api/dashboard/summary")

    results.check("summary responds 200", status == 200, status)
    results.check("envelope has success=true", payload.get("success") is True)
    results.check("envelope echoes filters", "filters" in payload)

    base = payload["data"]

    expected_keys = {
        "total_rows", "total_orders", "valid_orders",
        "cancelled_orders", "total_units", "gross_sales",
        "net_sales", "cancelled_value", "average_order_value",
        "average_selling_price"
    }

    results.check(
        "summary exposes every required field",
        expected_keys.issubset(base.keys()),
        expected_keys - set(base.keys())
    )

    # -----------------------------------------------------
    # BI invariants
    # -----------------------------------------------------

    results.section("BI invariants")

    results.check(
        "gross_sales >= net_sales",
        base["gross_sales"] >= base["net_sales"],
        f"{base['gross_sales']} vs {base['net_sales']}"
    )

    results.check(
        "gross_sales == net_sales + cancelled_value",
        abs(
            (base["net_sales"] + base["cancelled_value"])
            - base["gross_sales"]
        ) < 0.01,
        f"{base['net_sales']} + {base['cancelled_value']} "
        f"!= {base['gross_sales']}"
    )

    results.check(
        "valid_orders + cancelled_orders == total_orders",
        base["valid_orders"] + base["cancelled_orders"]
        == base["total_orders"]
    )

    # -----------------------------------------------------
    # 12. Duplicate order IDs
    # -----------------------------------------------------

    results.section("12. Duplicate Order IDs")

    row_count = scalar("SELECT COUNT(*) FROM sales")
    distinct_orders = scalar(
        "SELECT COUNT(DISTINCT order_id) FROM sales"
    )

    results.check(
        "dataset actually contains duplicate order_ids",
        row_count > distinct_orders,
        f"rows={row_count} distinct={distinct_orders}"
    )

    results.check(
        "total_rows == COUNT(*)",
        base["total_rows"] == row_count,
        f"{base['total_rows']} vs {row_count}"
    )

    results.check(
        "total_orders == COUNT(DISTINCT order_id)",
        base["total_orders"] == distinct_orders,
        f"{base['total_orders']} vs {distinct_orders}"
    )

    results.check(
        "total_orders is NOT row count",
        base["total_orders"] != base["total_rows"]
    )

    # -----------------------------------------------------
    # 11. Cancelled orders
    # -----------------------------------------------------

    results.section("11. Cancelled transactions")

    cancelled_rows = scalar(
        "SELECT COUNT(*) FROM sales "
        "WHERE LOWER(TRIM(COALESCE(status,''))) = 'cancelled'"
    )

    cancelled_amount = float(scalar(
        "SELECT COALESCE(SUM(amount),0) FROM sales "
        "WHERE LOWER(TRIM(COALESCE(status,''))) = 'cancelled'"
    ))

    cancelled_distinct = scalar(
        "SELECT COUNT(DISTINCT order_id) FROM sales "
        "WHERE LOWER(TRIM(COALESCE(status,''))) = 'cancelled'"
    )

    results.check(
        "cancelled rows still present in MySQL (auditable)",
        cancelled_rows > 0,
        cancelled_rows
    )

    results.check(
        "cancelled_value matches SUM(amount) of cancelled rows",
        abs(base["cancelled_value"] - cancelled_amount) < 0.01,
        f"{base['cancelled_value']} vs {cancelled_amount}"
    )

    results.check(
        "cancelled_orders uses DISTINCT order_id",
        base["cancelled_orders"] == cancelled_distinct,
        f"{base['cancelled_orders']} vs {cancelled_distinct}"
    )

    net_check = float(scalar(
        "SELECT COALESCE(SUM(amount),0) FROM sales "
        "WHERE LOWER(TRIM(COALESCE(status,''))) <> 'cancelled'"
    ))

    results.check(
        "net_sales excludes cancelled amounts",
        abs(base["net_sales"] - net_check) < 0.01,
        f"{base['net_sales']} vs {net_check}"
    )

    # -----------------------------------------------------
    # 2-7. Single filters
    # -----------------------------------------------------

    results.section("2-7. Individual filters")

    single_filters = [
        ("2. date range", "?date_from=2022-04-01&date_to=2022-04-30"),
        ("3. status", "?status=Shipped"),
        ("4. category", "?category=Set"),
        ("5. state", "?state=MAHARASHTRA"),
        ("6. fulfilment", "?fulfilment=Amazon"),
        ("7. sales channel", "?sales_channel=Amazon.in"),
    ]

    for label, query in single_filters:

        data = summary(client, query)

        results.check(
            f"{label} narrows the dataset",
            0 < data["total_rows"] < base["total_rows"],
            f"{data['total_rows']} vs {base['total_rows']}"
        )

        results.check(
            f"{label} keeps gross >= net",
            data["gross_sales"] >= data["net_sales"]
        )

    # Case-insensitivity (ci collation)
    lower = summary(client, "?state=maharashtra")
    upper = summary(client, "?state=MAHARASHTRA")

    results.check(
        "state filter is case-insensitive",
        lower["total_rows"] == upper["total_rows"],
        f"{lower['total_rows']} vs {upper['total_rows']}"
    )

    # Date bounds are inclusive
    single_day = summary(
        client,
        "?date_from=2022-04-01&date_to=2022-04-01"
    )

    day_rows = scalar(
        "SELECT COUNT(*) FROM sales WHERE order_date = '2022-04-01'"
    )

    results.check(
        "date bounds are inclusive",
        single_day["total_rows"] == day_rows,
        f"{single_day['total_rows']} vs {day_rows}"
    )

    # -----------------------------------------------------
    # 8. Multiple filters
    # -----------------------------------------------------

    results.section("8. Combined filters")

    combined_query = (
        "?date_from=2022-04-01&date_to=2022-04-30"
        "&category=Set&state=MAHARASHTRA"
    )

    combined = summary(client, combined_query)

    expected_rows = scalar(
        "SELECT COUNT(*) FROM sales "
        "WHERE order_date BETWEEN '2022-04-01' AND '2022-04-30' "
        "AND category = 'Set' AND ship_state = 'MAHARASHTRA'"
    )

    results.check(
        "combined filters match direct SQL",
        combined["total_rows"] == expected_rows,
        f"{combined['total_rows']} vs {expected_rows}"
    )

    results.check(
        "combined result is smaller than any single filter",
        combined["total_rows"] < summary(client, "?category=Set")["total_rows"]
    )

    # -----------------------------------------------------
    # 9. Invalid dates
    # -----------------------------------------------------

    results.section("9. Invalid input -> HTTP 400")

    invalid_cases = [
        "?date_from=2022-13-01",
        "?date_from=01/04/2022",
        "?date_to=notadate",
        "?date_from=2022-06-01&date_to=2022-04-01",
    ]

    for query in invalid_cases:

        status, payload = get(client, "/api/dashboard/summary" + query)

        results.check(
            f"400 for {query}",
            status == 400,
            status
        )

        results.check(
            f"useful error message for {query}",
            bool(payload.get("error")),
            payload
        )

    # -----------------------------------------------------
    # 10. Empty filter result
    # -----------------------------------------------------

    results.section("10. Empty result")

    empty = summary(client, "?state=NOWHERE")

    results.check("empty result returns 200, not an error", empty is not None)
    results.check("empty result has zero rows", empty["total_rows"] == 0)
    results.check("empty result has zero net sales", empty["net_sales"] == 0)

    results.check(
        "empty result does not divide by zero",
        empty["average_order_value"] == 0
        and empty["average_selling_price"] == 0
    )

    # -----------------------------------------------------
    # Filters reach every endpoint
    # -----------------------------------------------------

    results.section("Filters applied consistently across endpoints")

    endpoints = [
        "/api/dashboard/trend",
        "/api/dashboard/categories",
        "/api/dashboard/states",
        "/api/dashboard/status",
        "/api/dashboard/fulfilment",
        "/api/dashboard/channels",
        "/api/dashboard/top-products",
        "/api/dashboard/kpis",
    ]

    april = "?date_from=2022-04-01&date_to=2022-04-30"

    for endpoint in endpoints:

        status, unfiltered = get(client, endpoint)
        _, filtered = get(client, endpoint + april)

        results.check(
            f"{endpoint} responds 200",
            status == 200,
            status
        )

        results.check(
            f"{endpoint} honours the date filter",
            unfiltered["data"] != filtered["data"]
        )

        status_bad, _ = get(client, endpoint + "?date_from=bogus")

        results.check(
            f"{endpoint} rejects an invalid date",
            status_bad == 400,
            status_bad
        )

    # -----------------------------------------------------
    # Chart totals reconcile with the summary
    # -----------------------------------------------------

    results.section("Charts reconcile with summary KPIs")

    for query_label, query in [("unfiltered", ""), ("April", april)]:

        head = summary(client, query)

        for endpoint, key in [
            ("/api/dashboard/categories", "revenue"),
            ("/api/dashboard/trend", "revenue"),
            ("/api/dashboard/channels", "revenue"),
            ("/api/dashboard/fulfilment", "revenue"),
        ]:

            _, payload = get(client, endpoint + query)

            total = sum(row[key] for row in payload["data"])

            results.check(
                f"{endpoint} sums to net_sales ({query_label})",
                abs(total - head["net_sales"]) < 0.01,
                f"{total} vs {head['net_sales']}"
            )

        # Order status intentionally reports GROSS value so
        # the cancelled bucket is visible.
        _, payload = get(client, "/api/dashboard/status" + query)

        total = sum(row["sales_value"] for row in payload["data"])

        results.check(
            f"/status sums to gross_sales ({query_label})",
            abs(total - head["gross_sales"]) < 0.01,
            f"{total} vs {head['gross_sales']}"
        )

    # -----------------------------------------------------
    # Filter options
    # -----------------------------------------------------

    results.section("Filter options endpoint")

    status, payload = get(client, "/api/dashboard/filter-options")

    results.check("filter-options responds 200", status == 200, status)

    options = payload.get("data", {})

    for key in (
        "statuses", "categories", "states",
        "fulfilments", "sales_channels"
    ):

        values = options.get(key)

        results.check(
            f"filter-options returns {key}",
            isinstance(values, list) and len(values) > 0,
            values
        )

        results.check(
            f"{key} contains no duplicates",
            values is not None and len(values) == len(set(values))
        )

    # -----------------------------------------------------
    # Regression: importer untouched
    # -----------------------------------------------------

    results.section("Regression checks")

    import services.importer as importer

    results.check(
        "importer still exposes import_file",
        hasattr(importer, "import_file")
    )

    results.check(
        "importer still maps Amount -> amount",
        importer.clean_dataframe is not None
    )

    status, _ = get(client, "/")

    results.check("dashboard page still renders", status == 200, status)


# =========================================================
# ENTRY POINT
# =========================================================

def main():

    print("=" * 58)
    print("  DASHBOARD API / BI TEST SUITE")
    print("=" * 58)

    with app.app_context():
        run()

    sys.exit(results.report())


if __name__ == "__main__":
    main()
