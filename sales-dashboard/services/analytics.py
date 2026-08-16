from sqlalchemy import (
    func,
    case,
    distinct
)

from database import db
from models import Sale


# =========================================================
# HELPERS
# =========================================================

CANCELLED_STATUS = "Cancelled"


def is_cancelled():

    return func.lower(
        func.coalesce(
            Sale.status,
            ""
        )
    ) == CANCELLED_STATUS.lower()


# =========================================================
# KPI
# =========================================================

def get_kpis():

    # -----------------------------------------------------
    # Total distinct orders
    # -----------------------------------------------------

    total_orders = (

        db.session

        .query(
            func.count(
                distinct(
                    Sale.order_id
                )
            )
        )

        .scalar()
    )

    # -----------------------------------------------------
    # Cancelled orders
    # -----------------------------------------------------

    cancelled_orders = (

        db.session

        .query(
            func.count(
                distinct(
                    case(
                        (
                            is_cancelled(),
                            Sale.order_id
                        )
                    )
                )
            )
        )

        .scalar()
    )

    # -----------------------------------------------------
    # Net orders
    # -----------------------------------------------------

    net_orders = (
        total_orders or 0
    ) - (
        cancelled_orders or 0
    )

    # -----------------------------------------------------
    # Total units
    # -----------------------------------------------------

    total_units = (

        db.session

        .query(
            func.coalesce(
                func.sum(
                    Sale.quantity
                ),
                0
            )
        )

        .scalar()
    )

    # -----------------------------------------------------
    # Gross sales
    # -----------------------------------------------------

    gross_sales = (

        db.session

        .query(
            func.coalesce(
                func.sum(
                    Sale.amount
                ),
                0
            )
        )

        .scalar()
    )

    # -----------------------------------------------------
    # Net sales
    #
    # Cancelled transactions excluded
    # -----------------------------------------------------

    net_sales = (

        db.session

        .query(

            func.coalesce(

                func.sum(

                    case(

                        (
                            ~is_cancelled(),
                            Sale.amount
                        ),

                        else_=0
                    )
                ),

                0
            )
        )

        .scalar()
    )

    # -----------------------------------------------------
    # Cancelled sales value
    # -----------------------------------------------------

    cancelled_sales = (

        db.session

        .query(

            func.coalesce(

                func.sum(

                    case(

                        (
                            is_cancelled(),
                            Sale.amount
                        ),

                        else_=0
                    )
                ),

                0
            )
        )

        .scalar()
    )

    # -----------------------------------------------------
    # Average order value
    # -----------------------------------------------------

    average_order_value = 0

    if net_orders:

        average_order_value = (
            float(net_sales or 0)
            /
            net_orders
        )

    # -----------------------------------------------------
    # Cancellation rate
    # -----------------------------------------------------

    cancellation_rate = 0

    if total_orders:

        cancellation_rate = (

            (
                cancelled_orders or 0
            )
            /
            total_orders
        ) * 100

    return {

        "total_orders":
            int(
                total_orders or 0
            ),

        "cancelled_orders":
            int(
                cancelled_orders or 0
            ),

        "net_orders":
            int(
                net_orders
            ),

        "total_units":
            int(
                total_units or 0
            ),

        "gross_sales":
            round(
                float(
                    gross_sales or 0
                ),
                2
            ),

        "net_sales":
            round(
                float(
                    net_sales or 0
                ),
                2
            ),

        "cancelled_sales":
            round(
                float(
                    cancelled_sales or 0
                ),
                2
            ),

        "average_order_value":
            round(
                average_order_value,
                2
            ),

        "cancellation_rate":
            round(
                cancellation_rate,
                2
            )
    }


# =========================================================
# SALES TREND
# =========================================================

def get_sales_trend():

    net_revenue = func.sum(

        case(

            (
                ~is_cancelled(),
                Sale.amount
            ),

            else_=0
        )
    )

    results = (

        db.session

        .query(

            Sale.order_date.label(
                "date"
            ),

            func.count(
                distinct(
                    Sale.order_id
                )
            ).label(
                "orders"
            ),

            func.coalesce(
                func.sum(
                    Sale.quantity
                ),
                0
            ).label(
                "quantity"
            ),

            func.coalesce(
                net_revenue,
                0
            ).label(
                "revenue"
            )
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
                int(
                    row.orders or 0
                ),

            "quantity":
                int(
                    row.quantity or 0
                ),

            "revenue":
                float(
                    row.revenue or 0
                )
        }

        for row in results
    ]


# =========================================================
# CATEGORY
# =========================================================

def get_category_sales():

    revenue = func.sum(

        case(

            (
                ~is_cancelled(),
                Sale.amount
            ),

            else_=0
        )
    )

    results = (

        db.session

        .query(

            Sale.category,

            func.count(
                distinct(
                    Sale.order_id
                )
            ).label(
                "orders"
            ),

            func.coalesce(
                func.sum(
                    Sale.quantity
                ),
                0
            ).label(
                "quantity"
            ),

            func.coalesce(
                revenue,
                0
            ).label(
                "revenue"
            )
        )

        .group_by(
            Sale.category
        )

        .order_by(
            revenue.desc()
        )

        .all()
    )

    return [

        {

            "category":
                row.category or "Unknown",

            "orders":
                int(
                    row.orders or 0
                ),

            "quantity":
                int(
                    row.quantity or 0
                ),

            "revenue":
                float(
                    row.revenue or 0
                )
        }

        for row in results
    ]


# =========================================================
# STATE
# =========================================================

def get_state_sales():

    revenue = func.sum(

        case(

            (
                ~is_cancelled(),
                Sale.amount
            ),

            else_=0
        )
    )

    results = (

        db.session

        .query(

            Sale.ship_state.label(
                "state"
            ),

            func.count(
                distinct(
                    Sale.order_id
                )
            ).label(
                "orders"
            ),

            func.coalesce(
                func.sum(
                    Sale.quantity
                ),
                0
            ).label(
                "quantity"
            ),

            func.coalesce(
                revenue,
                0
            ).label(
                "revenue"
            )
        )

        .filter(
            Sale.ship_state.isnot(None)
        )

        .group_by(
            Sale.ship_state
        )

        .order_by(
            revenue.desc()
        )

        .all()
    )

    return [

        {

            "state":
                row.state or "Unknown",

            "orders":
                int(
                    row.orders or 0
                ),

            "quantity":
                int(
                    row.quantity or 0
                ),

            "revenue":
                float(
                    row.revenue or 0
                )
        }

        for row in results
    ]


# =========================================================
# FULFILMENT
# =========================================================

def get_fulfilment():

    revenue = func.sum(

        case(

            (
                ~is_cancelled(),
                Sale.amount
            ),

            else_=0
        )
    )

    results = (

        db.session

        .query(

            Sale.fulfilment,

            func.count(
                distinct(
                    Sale.order_id
                )
            ).label(
                "orders"
            ),

            func.coalesce(
                revenue,
                0
            ).label(
                "revenue"
            )
        )

        .group_by(
            Sale.fulfilment
        )

        .order_by(
            revenue.desc()
        )

        .all()
    )

    return [

        {

            "fulfilment":
                row.fulfilment or "Unknown",

            "orders":
                int(
                    row.orders or 0
                ),

            "revenue":
                float(
                    row.revenue or 0
                )
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
                distinct(
                    Sale.order_id
                )
            ).label(
                "orders"
            ),

            func.coalesce(
                func.sum(
                    Sale.amount
                ),
                0
            ).label(
                "sales_value"
            )
        )

        .group_by(
            Sale.status
        )

        .order_by(
            func.count(
                distinct(
                    Sale.order_id
                )
            ).desc()
        )

        .all()
    )

    return [

        {

            "status":
                row.status or "Unknown",

            "orders":
                int(
                    row.orders or 0
                ),

            "sales_value":
                float(
                    row.sales_value or 0
                )
        }

        for row in results
    ]


# =========================================================
# SALES CHANNEL
# =========================================================

def get_sales_channel():

    revenue = func.sum(

        case(

            (
                ~is_cancelled(),
                Sale.amount
            ),

            else_=0
        )
    )

    results = (

        db.session

        .query(

            Sale.sales_channel,

            func.count(
                distinct(
                    Sale.order_id
                )
            ).label(
                "orders"
            ),

            func.coalesce(
                revenue,
                0
            ).label(
                "revenue"
            )
        )

        .group_by(
            Sale.sales_channel
        )

        .order_by(
            revenue.desc()
        )

        .all()
    )

    return [

        {

            "channel":
                row.sales_channel or "Unknown",

            "orders":
                int(
                    row.orders or 0
                ),

            "revenue":
                float(
                    row.revenue or 0
                )
        }

        for row in results
    ]


# =========================================================
# TOP PRODUCTS
# =========================================================

def get_top_products(
    limit=10
):

    revenue = func.sum(

        case(

            (
                ~is_cancelled(),
                Sale.amount
            ),

            else_=0
        )
    )

    results = (

        db.session

        .query(

            Sale.sku,

            Sale.style,

            Sale.category,

            func.coalesce(
                func.sum(
                    Sale.quantity
                ),
                0
            ).label(
                "quantity"
            ),

            func.coalesce(
                revenue,
                0
            ).label(
                "revenue"
            )
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
            revenue.desc()
        )

        .limit(
            limit
        )

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
                int(
                    row.quantity or 0
                ),

            "revenue":
                float(
                    row.revenue or 0
                )
        }

        for row in results
    ]


# =========================================================
# COMPLETE DASHBOARD
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