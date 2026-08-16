from sqlalchemy import (
    func,
    case,
    distinct
)

from database import db
from models import Sale


# =========================================================
# KPI SUMMARY
# =========================================================

def get_kpis():

    total_orders = (
        db.session
        .query(
            func.count(
                distinct(Sale.order_id)
            )
        )
        .scalar()
    )

    total_items = (
        db.session
        .query(
            func.coalesce(
                func.sum(Sale.quantity),
                0
            )
        )
        .scalar()
    )

    total_revenue = (
        db.session
        .query(
            func.coalesce(
                func.sum(Sale.amount),
                0
            )
        )
        .scalar()
    )

    average_order_value = 0

    if total_orders:
        average_order_value = (
            float(total_revenue)
            / total_orders
        )

    return {

        "total_orders":
            int(total_orders or 0),

        "total_items":
            int(total_items or 0),

        "total_revenue":
            float(total_revenue or 0),

        "average_order_value":
            round(
                average_order_value,
                2
            )
    }


# =========================================================
# SALES BY DATE
# =========================================================

def get_sales_trend():

    results = (
        db.session
        .query(
            Sale.order_date.label("date"),

            func.count(
                distinct(Sale.order_id)
            ).label("orders"),

            func.coalesce(
                func.sum(Sale.quantity),
                0
            ).label("quantity"),

            func.coalesce(
                func.sum(Sale.amount),
                0
            ).label("revenue")
        )
        .filter(
            Sale.order_date.isnot(None)
        )
        .group_by(
            Sale.order_date
        )
        .order_by(
            Sale.order_date
        )
        .all()
    )

    return [

        {
            "date":
                row.date.isoformat(),

            "orders":
                int(row.orders or 0),

            "quantity":
                int(row.quantity or 0),

            "revenue":
                float(row.revenue or 0)
        }

        for row in results
    ]


# =========================================================
# SALES BY CATEGORY
# =========================================================

def get_category_sales():

    results = (
        db.session
        .query(
            Sale.category,

            func.count(
                distinct(Sale.order_id)
            ).label("orders"),

            func.coalesce(
                func.sum(Sale.quantity),
                0
            ).label("quantity"),

            func.coalesce(
                func.sum(Sale.amount),
                0
            ).label("revenue")
        )
        .group_by(
            Sale.category
        )
        .order_by(
            func.sum(
                Sale.amount
            ).desc()
        )
        .all()
    )

    return [

        {
            "category":
                row.category or "Unknown",

            "orders":
                int(row.orders or 0),

            "quantity":
                int(row.quantity or 0),

            "revenue":
                float(row.revenue or 0)
        }

        for row in results
    ]


# =========================================================
# SALES BY STATE
# =========================================================

def get_state_sales():

    results = (
        db.session
        .query(
            Sale.ship_state.label("state"),

            func.count(
                distinct(Sale.order_id)
            ).label("orders"),

            func.coalesce(
                func.sum(Sale.quantity),
                0
            ).label("quantity"),

            func.coalesce(
                func.sum(Sale.amount),
                0
            ).label("revenue")
        )
        .filter(
            Sale.ship_state.isnot(None)
        )
        .group_by(
            Sale.ship_state
        )
        .order_by(
            func.sum(
                Sale.amount
            ).desc()
        )
        .all()
    )

    return [

        {
            "state":
                row.state or "Unknown",

            "orders":
                int(row.orders or 0),

            "quantity":
                int(row.quantity or 0),

            "revenue":
                float(row.revenue or 0)
        }

        for row in results
    ]


# =========================================================
# FULFILMENT
# =========================================================

def get_fulfilment():

    results = (
        db.session
        .query(
            Sale.fulfilment,

            func.count(
                distinct(Sale.order_id)
            ).label("orders"),

            func.coalesce(
                func.sum(Sale.amount),
                0
            ).label("revenue")
        )
        .group_by(
            Sale.fulfilment
        )
        .order_by(
            func.sum(
                Sale.amount
            ).desc()
        )
        .all()
    )

    return [

        {
            "fulfilment":
                row.fulfilment or "Unknown",

            "orders":
                int(row.orders or 0),

            "revenue":
                float(row.revenue or 0)
        }

        for row in results
    ]


# =========================================================
# ORDER STATUS
# =========================================================

def get_order_status():

    results = (
        db.session
        .query(
            Sale.status,

            func.count(
                distinct(Sale.order_id)
            ).label("orders"),

            func.coalesce(
                func.sum(Sale.amount),
                0
            ).label("revenue")
        )
        .group_by(
            Sale.status
        )
        .order_by(
            func.count(
                distinct(Sale.order_id)
            ).desc()
        )
        .all()
    )

    return [

        {
            "status":
                row.status or "Unknown",

            "orders":
                int(row.orders or 0),

            "revenue":
                float(row.revenue or 0)
        }

        for row in results
    ]


# =========================================================
# SALES CHANNEL
# =========================================================

def get_sales_channel():

    results = (
        db.session
        .query(
            Sale.sales_channel,

            func.count(
                distinct(Sale.order_id)
            ).label("orders"),

            func.coalesce(
                func.sum(Sale.amount),
                0
            ).label("revenue")
        )
        .group_by(
            Sale.sales_channel
        )
        .order_by(
            func.sum(
                Sale.amount
            ).desc()
        )
        .all()
    )

    return [

        {
            "channel":
                row.sales_channel or "Unknown",

            "orders":
                int(row.orders or 0),

            "revenue":
                float(row.revenue or 0)
        }

        for row in results
    ]


# =========================================================
# TOP PRODUCTS
# =========================================================

def get_top_products(limit=10):

    results = (
        db.session
        .query(
            Sale.sku,

            Sale.style,

            Sale.category,

            func.coalesce(
                func.sum(Sale.quantity),
                0
            ).label("quantity"),

            func.coalesce(
                func.sum(Sale.amount),
                0
            ).label("revenue")
        )
        .filter(
            Sale.sku.isnot(None)
        )
        .group_by(
            Sale.sku,
            Sale.style,
            Sale.category
        )
        .order_by(
            func.sum(
                Sale.amount
            ).desc()
        )
        .limit(limit)
        .all()
    )

    return [

        {
            "sku":
                row.sku,

            "style":
                row.style,

            "category":
                row.category,

            "quantity":
                int(row.quantity or 0),

            "revenue":
                float(row.revenue or 0)
        }

        for row in results
    ]


# =========================================================
# COMPLETE DASHBOARD DATA
# =========================================================

def get_dashboard_data():

    return {

        "kpis":
            get_kpis(),

        "sales_trend":
            get_sales_trend(),

        "categories":
            get_category_sales(),

        "states":
            get_state_sales(),

        "fulfilment":
            get_fulfilment(),

        "order_status":
            get_order_status(),

        "sales_channel":
            get_sales_channel(),

        "top_products":
            get_top_products()
    }