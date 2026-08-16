"""
=========================================================
CHART AGGREGATIONS
=========================================================

Grouped aggregations behind the analytics endpoints.

Measure used by each function -- all imported from
services/bi_definitions.py, never redefined here:

    get_kpis            delegates to SalesMetrics
    get_sales_trend     net sales, by order_date
    get_category_sales  net sales, by category
    get_state_sales     net sales, by ship_state
    get_fulfilment      net sales, by fulfilment
    get_order_status    distinct orders + gross value,
                        by status
    get_sales_channel   net sales, by sales_channel
    get_top_products    net sales, by sku/style/category

Order status is the one panel that intentionally reports
GROSS value: its whole purpose is to show the cancelled
bucket, which net sales excludes by definition. Every other
revenue chart uses NET sales, matching the headline KPI.

Order counts everywhere use COUNT(DISTINCT order_id).

Every function accepts an optional DashboardFilters and
aggregates in MySQL -- no raw rows are pulled into Python
or Pandas for dashboard requests.
"""

from database import db
from models import Sale

from services.bi_definitions import (

    net_sales_expr,
    gross_sales_expr,
    total_units_expr,
    total_orders_expr
)

from services.bi_metrics import SalesMetrics
from services.query_filters import DashboardFilters


# =========================================================
# HELPERS
# =========================================================

def _filters(filters):

    return filters if filters is not None else DashboardFilters()


# =========================================================
# KPI
# =========================================================

def get_kpis(filters=None):
    """
    Summary KPIs.

    Delegates entirely to SalesMetrics so this endpoint can
    never report different numbers from /summary. Previously
    this function re-implemented every KPI with subtly
    different definitions (units included cancellations,
    average order value used a different denominator).
    """

    return SalesMetrics.dashboard_summary(filters)


# =========================================================
# SALES TREND  -- net sales by date
# =========================================================

def get_sales_trend(filters=None):

    # Ordered chronologically rather than by size.
    query = db.session.query(

        Sale.order_date.label("date"),

        total_orders_expr().label("orders"),

        total_units_expr().label("quantity"),

        net_sales_expr().label("revenue")
    )

    query = _filters(filters).apply(query)

    rows = (
        query
        .filter(Sale.order_date.isnot(None))
        .group_by(Sale.order_date)
        .order_by(Sale.order_date)
        .all()
    )

    return [
        {
            "date": row.date.isoformat(),
            "orders": int(row.orders or 0),
            "quantity": int(row.quantity or 0),
            "revenue": float(row.revenue or 0)
        }
        for row in rows
    ]


# =========================================================
# CATEGORY  -- net sales by category
# =========================================================

def get_category_sales(filters=None):

    revenue = net_sales_expr()

    query = db.session.query(

        Sale.category,

        total_orders_expr().label("orders"),

        total_units_expr().label("quantity"),

        revenue.label("revenue")
    )

    rows = (
        _filters(filters).apply(query)
        .group_by(Sale.category)
        .order_by(revenue.desc())
        .all()
    )

    return [
        {
            "category": row.category or "Unknown",
            "orders": int(row.orders or 0),
            "quantity": int(row.quantity or 0),
            "revenue": float(row.revenue or 0)
        }
        for row in rows
    ]


# =========================================================
# STATE  -- net sales by shipping state
# =========================================================
#
# Rows with a NULL ship_state are excluded: an unknown
# state cannot be plotted. In the current dataset that is
# 33 rows carrying 16,641.00 of net sales, so this endpoint
# sums slightly BELOW summary.net_sales by design. Every
# other revenue chart reconciles exactly.
# =========================================================

def get_state_sales(filters=None):

    revenue = net_sales_expr()

    query = db.session.query(

        Sale.ship_state.label("state"),

        total_orders_expr().label("orders"),

        total_units_expr().label("quantity"),

        revenue.label("revenue")
    )

    rows = (
        _filters(filters).apply(query)
        .filter(Sale.ship_state.isnot(None))
        .group_by(Sale.ship_state)
        .order_by(revenue.desc())
        .all()
    )

    return [
        {
            "state": row.state or "Unknown",
            "orders": int(row.orders or 0),
            "quantity": int(row.quantity or 0),
            "revenue": float(row.revenue or 0)
        }
        for row in rows
    ]


# =========================================================
# FULFILMENT  -- net sales by fulfilment channel
# =========================================================

def get_fulfilment(filters=None):

    revenue = net_sales_expr()

    query = db.session.query(

        Sale.fulfilment,

        total_orders_expr().label("orders"),

        revenue.label("revenue")
    )

    rows = (
        _filters(filters).apply(query)
        .group_by(Sale.fulfilment)
        .order_by(revenue.desc())
        .all()
    )

    return [
        {
            "fulfilment": row.fulfilment or "Unknown",
            "orders": int(row.orders or 0),
            "revenue": float(row.revenue or 0)
        }
        for row in rows
    ]


# =========================================================
# ORDER STATUS  -- distinct orders + GROSS value
# =========================================================
#
# Uses gross value deliberately: this panel exists to show
# the cancelled bucket, and net sales defines cancelled
# value as zero.
# =========================================================

def get_order_status(filters=None):

    orders = total_orders_expr()

    query = db.session.query(

        Sale.status,

        orders.label("orders"),

        gross_sales_expr().label("sales_value")
    )

    rows = (
        _filters(filters).apply(query)
        .group_by(Sale.status)
        .order_by(orders.desc())
        .all()
    )

    return [
        {
            "status": row.status or "Unknown",
            "orders": int(row.orders or 0),
            "sales_value": float(row.sales_value or 0)
        }
        for row in rows
    ]


# =========================================================
# SALES CHANNEL  -- net sales by channel
# =========================================================

def get_sales_channel(filters=None):

    revenue = net_sales_expr()

    query = db.session.query(

        Sale.sales_channel,

        total_orders_expr().label("orders"),

        revenue.label("revenue")
    )

    rows = (
        _filters(filters).apply(query)
        .group_by(Sale.sales_channel)
        .order_by(revenue.desc())
        .all()
    )

    return [
        {
            "channel": row.sales_channel or "Unknown",
            "orders": int(row.orders or 0),
            "revenue": float(row.revenue or 0)
        }
        for row in rows
    ]


# =========================================================
# TOP PRODUCTS  -- net sales by SKU
# =========================================================

def get_top_products(filters=None, limit=10):

    revenue = net_sales_expr()

    query = db.session.query(

        Sale.sku,
        Sale.style,
        Sale.category,

        total_units_expr().label("quantity"),

        revenue.label("revenue")
    )

    rows = (
        _filters(filters).apply(query)
        .filter(Sale.sku.isnot(None))
        .group_by(Sale.sku, Sale.style, Sale.category)
        .order_by(revenue.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "sku": row.sku,
            "style": row.style,
            "category": row.category,
            "quantity": int(row.quantity or 0),
            "revenue": float(row.revenue or 0)
        }
        for row in rows
    ]


# =========================================================
# COMPLETE DASHBOARD
# =========================================================

def get_dashboard_data(filters=None):
    """Every dataset in one payload, sharing one filter set."""

    return {
        "kpis": get_kpis(filters),
        "sales_trend": get_sales_trend(filters),
        "categories": get_category_sales(filters),
        "states": get_state_sales(filters),
        "fulfilment": get_fulfilment(filters),
        "order_status": get_order_status(filters),
        "sales_channel": get_sales_channel(filters),
        "top_products": get_top_products(filters)
    }
