"""
=========================================================
BI DEFINITIONS -- SINGLE SOURCE OF TRUTH
=========================================================

Every KPI in this application is defined exactly once, here.

`services/bi_metrics.py` (summary KPIs) and
`services/analytics.py` (chart aggregations) both import
these expressions. Neither module may re-implement a
measure locally, and the frontend never calculates a
business metric -- JavaScript only formats values.

---------------------------------------------------------
THE CANCELLED TRANSACTION RULE
---------------------------------------------------------

Cancelled rows are NEVER deleted from MySQL. The raw import
stays fully auditable. Instead, each BI measure decides
whether a cancelled row contributes to it.

A row is cancelled when:

    LOWER(TRIM(COALESCE(status, ''))) = 'cancelled'

COALESCE matters: `LOWER(NULL) <> 'cancelled'` evaluates to
NULL, not TRUE, so a NULL status would silently drop out of
"not cancelled" aggregates without it.

---------------------------------------------------------
ROWS vs ORDERS vs UNITS
---------------------------------------------------------

These three are NOT interchangeable in this dataset:

    transaction rows : 128,975
    distinct orders  : 120,378   (8,597 rows share an order)
    units            : SUM(quantity)

One Order ID can span several rows (multiple SKUs / sizes).
Therefore any measure that represents ORDERS must use
COUNT(DISTINCT order_id) -- never COUNT(*).

---------------------------------------------------------
MEASURE DEFINITIONS
---------------------------------------------------------

total_rows            COUNT(*) -- raw transaction rows,
                      cancellations included. Audit figure.

total_orders          COUNT(DISTINCT order_id), all statuses.

cancelled_orders      COUNT(DISTINCT order_id) restricted to
                      cancelled rows.

valid_orders          COUNT(DISTINCT order_id) restricted to
                      non-cancelled rows.

                      NOTE: verified against the dataset --
                      no order_id contains both cancelled and
                      non-cancelled rows, so
                      valid + cancelled = total. valid_orders
                      is still queried directly rather than
                      derived by subtraction, so the measure
                      stays correct if that ever changes.

gross_sales           SUM(amount) over every row regardless
                      of status.

net_sales             SUM(amount) over non-cancelled rows.

cancelled_value       SUM(amount) over cancelled rows.

                      Invariant: gross_sales
                               = net_sales + cancelled_value

total_units           SUM(quantity) over non-cancelled rows.
                      Units actually sold.

gross_units           SUM(quantity) over every row. Exposed
                      for auditing; not shown on the
                      dashboard.

average_order_value   net_sales / valid_orders

                      Numerator and denominator both exclude
                      cancellations. Dividing net_sales by
                      total_orders would mix a cancelled-
                      exclusive numerator with a cancelled-
                      inclusive denominator and understate
                      the figure.

average_selling_price net_sales / total_units

                      Both sides exclude cancellations.

No refund or return logic is implemented. The dataset
carries "Shipped - Returned to Seller" statuses but no
refund amounts, so inventing that logic is not supported by
the source data.
"""

from sqlalchemy import func, case

from models import Sale


# =========================================================
# CANCELLATION PREDICATES
# =========================================================

CANCELLED_STATUS = "cancelled"


def _normalised_status():
    """Status lowered/trimmed and NULL-safe."""

    return func.lower(
        func.trim(
            func.coalesce(Sale.status, "")
        )
    )


def is_cancelled():

    return _normalised_status() == CANCELLED_STATUS


def is_not_cancelled():

    return _normalised_status() != CANCELLED_STATUS


# =========================================================
# ROW / ORDER COUNTS
# =========================================================

def total_rows_expr():
    """Raw transaction rows -- NOT orders."""

    return func.count(Sale.id)


def total_orders_expr():
    """Distinct orders across every status."""

    return func.count(func.distinct(Sale.order_id))


def cancelled_orders_expr():
    """Distinct orders having cancelled rows."""

    return func.count(
        func.distinct(
            case(
                (is_cancelled(), Sale.order_id)
            )
        )
    )


def valid_orders_expr():
    """Distinct orders having non-cancelled rows."""

    return func.count(
        func.distinct(
            case(
                (is_not_cancelled(), Sale.order_id)
            )
        )
    )


# =========================================================
# SALES MEASURES
# =========================================================

def gross_sales_expr():
    """SUM(amount), cancellations included."""

    return func.coalesce(
        func.sum(Sale.amount),
        0
    )


def net_sales_expr():
    """SUM(amount) excluding cancelled rows."""

    return func.coalesce(
        func.sum(
            case(
                (is_not_cancelled(), Sale.amount),
                else_=0
            )
        ),
        0
    )


def cancelled_value_expr():
    """SUM(amount) over cancelled rows only."""

    return func.coalesce(
        func.sum(
            case(
                (is_cancelled(), Sale.amount),
                else_=0
            )
        ),
        0
    )


# =========================================================
# UNIT MEASURES
# =========================================================

def total_units_expr():
    """SUM(quantity) excluding cancelled rows."""

    return func.coalesce(
        func.sum(
            case(
                (is_not_cancelled(), Sale.quantity),
                else_=0
            )
        ),
        0
    )


def gross_units_expr():
    """SUM(quantity), cancellations included."""

    return func.coalesce(
        func.sum(Sale.quantity),
        0
    )


# =========================================================
# DERIVED RATIOS
# =========================================================
#
# Computed in Python from the aggregates above so the
# zero-denominator guard lives in exactly one place.
# =========================================================

def safe_divide(numerator, denominator):

    if not denominator:
        return 0.0

    return float(numerator) / float(denominator)


def average_order_value(net_sales, valid_orders):
    """net_sales / valid_orders"""

    return safe_divide(net_sales, valid_orders)


def average_selling_price(net_sales, total_units):
    """net_sales / total_units"""

    return safe_divide(net_sales, total_units)
