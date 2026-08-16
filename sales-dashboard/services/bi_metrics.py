"""
=========================================================
DASHBOARD SUMMARY KPIs
=========================================================

Thin aggregation layer over services/bi_definitions.py.

This module owns NO measure definitions of its own -- every
expression is imported from bi_definitions so that
analytics.py and bi_metrics.py can never drift apart.

Raw source values are never modified. BI measures decide
which records contribute to each KPI.
"""

from sqlalchemy import func

from database import db
from models import Sale

from services.bi_definitions import (

    total_rows_expr,
    total_orders_expr,
    valid_orders_expr,
    cancelled_orders_expr,

    gross_sales_expr,
    net_sales_expr,
    cancelled_value_expr,

    total_units_expr,
    gross_units_expr,

    average_order_value,
    average_selling_price
)

from services.query_filters import DashboardFilters


class SalesMetrics:
    """
    Dashboard summary metrics.

    Every method accepts an optional DashboardFilters. When
    omitted the complete dataset is measured.
    """

    # =====================================================
    # SUMMARY
    # =====================================================

    @staticmethod
    def dashboard_summary(filters=None):
        """
        All summary KPIs in a SINGLE aggregate query.

        The previous implementation issued nine separate
        queries (and recomputed net_sales twice for the
        averages). One round trip over ~129k rows is both
        faster and guarantees every KPI describes the same
        snapshot of the data.
        """

        if filters is None:
            filters = DashboardFilters()

        query = db.session.query(

            total_rows_expr().label("total_rows"),
            total_orders_expr().label("total_orders"),
            valid_orders_expr().label("valid_orders"),
            cancelled_orders_expr().label("cancelled_orders"),

            gross_sales_expr().label("gross_sales"),
            net_sales_expr().label("net_sales"),
            cancelled_value_expr().label("cancelled_value"),

            total_units_expr().label("total_units"),
            gross_units_expr().label("gross_units")
        )

        row = filters.apply(query).one()

        net_sales = float(row.net_sales or 0)
        valid_orders = int(row.valid_orders or 0)
        total_units = int(row.total_units or 0)

        return {

            # ---- counts ----

            "total_rows":
                int(row.total_rows or 0),

            "total_orders":
                int(row.total_orders or 0),

            "valid_orders":
                valid_orders,

            "cancelled_orders":
                int(row.cancelled_orders or 0),

            "total_units":
                total_units,

            "gross_units":
                int(row.gross_units or 0),

            # ---- money ----

            "gross_sales":
                round(float(row.gross_sales or 0), 2),

            "net_sales":
                round(net_sales, 2),

            "cancelled_value":
                round(float(row.cancelled_value or 0), 2),

            # ---- derived ----

            "average_order_value":
                round(
                    average_order_value(net_sales, valid_orders),
                    2
                ),

            "average_selling_price":
                round(
                    average_selling_price(net_sales, total_units),
                    2
                )
        }

    # =====================================================
    # INDIVIDUAL MEASURES
    # =====================================================
    #
    # Retained for scripts and tests. They delegate to the
    # same expressions used by dashboard_summary, so they
    # can never report a different number.
    # =====================================================

    @staticmethod
    def _scalar(expression, filters=None):

        if filters is None:
            filters = DashboardFilters()

        query = db.session.query(expression)

        return filters.apply(query).scalar()

    # ---- counts -----------------------------------------

    @staticmethod
    def total_rows(filters=None):
        return int(
            SalesMetrics._scalar(total_rows_expr(), filters) or 0
        )

    @staticmethod
    def total_orders(filters=None):
        return int(
            SalesMetrics._scalar(total_orders_expr(), filters) or 0
        )

    @staticmethod
    def valid_orders(filters=None):
        return int(
            SalesMetrics._scalar(valid_orders_expr(), filters) or 0
        )

    @staticmethod
    def cancelled_orders(filters=None):
        return int(
            SalesMetrics._scalar(cancelled_orders_expr(), filters) or 0
        )

    @staticmethod
    def total_units(filters=None):
        return int(
            SalesMetrics._scalar(total_units_expr(), filters) or 0
        )

    # ---- money ------------------------------------------

    @staticmethod
    def gross_sales(filters=None):
        return float(
            SalesMetrics._scalar(gross_sales_expr(), filters) or 0
        )

    @staticmethod
    def net_sales(filters=None):
        return float(
            SalesMetrics._scalar(net_sales_expr(), filters) or 0
        )

    @staticmethod
    def cancelled_value(filters=None):
        return float(
            SalesMetrics._scalar(cancelled_value_expr(), filters) or 0
        )

    # ---- derived ----------------------------------------

    @staticmethod
    def average_order_value(filters=None):

        return average_order_value(
            SalesMetrics.net_sales(filters),
            SalesMetrics.valid_orders(filters)
        )

    @staticmethod
    def average_selling_price(filters=None):

        return average_selling_price(
            SalesMetrics.net_sales(filters),
            SalesMetrics.total_units(filters)
        )

    # =====================================================
    # FILTER OPTIONS
    # =====================================================

    @staticmethod
    def filter_options():
        """
        Distinct values for the frontend filter controls,
        read from MySQL. Never hard-coded.
        """

        def distinct_values(column):

            rows = (
                db.session
                .query(column)
                .filter(column.isnot(None))
                .filter(func.trim(column) != "")
                .distinct()
                .order_by(column)
                .all()
            )

            return [row[0] for row in rows]

        return {
            "statuses": distinct_values(Sale.status),
            "categories": distinct_values(Sale.category),
            "states": distinct_values(Sale.ship_state),
            "fulfilments": distinct_values(Sale.fulfilment),
            "sales_channels": distinct_values(Sale.sales_channel)
        }
