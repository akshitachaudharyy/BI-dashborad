from sqlalchemy import func, case

from database import db
from models import Sale


class SalesMetrics:
    """
    Central BI calculation layer.

    IMPORTANT:
    Raw source values are not modified here.

    Instead, BI measures decide which records
    contribute to each KPI.
    """

    # =====================================================
    # BASIC COUNTS
    # =====================================================

    @staticmethod
    def total_rows():

        result = (
            db.session.query(
                func.count(Sale.id)
            )
            .scalar()
        )

        return int(result or 0)

    # -----------------------------------------------------

    @staticmethod
    def total_orders():

        result = (
            db.session.query(
                func.count(
                    func.distinct(
                        Sale.order_id
                    )
                )
            )
            .scalar()
        )

        return int(result or 0)

    # -----------------------------------------------------

    @staticmethod
    def cancelled_orders():

        result = (
            db.session.query(
                func.count(
                    func.distinct(
                        Sale.order_id
                    )
                )
            )
            .filter(
                func.lower(
                    Sale.status
                ) == "cancelled"
            )
            .scalar()
        )

        return int(result or 0)

    # =====================================================
    # UNITS
    # =====================================================

    @staticmethod
    def total_units():

        result = (
            db.session.query(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                func.lower(
                                    Sale.status
                                ) != "cancelled",

                                Sale.quantity
                            ),
                            else_=0
                        )
                    ),
                    0
                )
            )
            .scalar()
        )

        return int(result or 0)

    # =====================================================
    # SALES
    # =====================================================

    @staticmethod
    def gross_sales():

        """
        Raw sales amount.

        Includes cancelled records.

        This is intentionally NOT the main
        dashboard sales KPI.
        """

        result = (
            db.session.query(
                func.coalesce(
                    func.sum(
                        Sale.amount
                    ),
                    0
                )
            )
            .scalar()
        )

        return float(result or 0)

    # -----------------------------------------------------

    @staticmethod
    def net_sales():

        """
        BI sales value.

        Cancelled transactions are excluded.
        """

        result = (
            db.session.query(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                func.lower(
                                    Sale.status
                                ) != "cancelled",

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

        return float(result or 0)

    # -----------------------------------------------------

    @staticmethod
    def cancelled_value():

        result = (
            db.session.query(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                func.lower(
                                    Sale.status
                                ) == "cancelled",

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

        return float(result or 0)

    # =====================================================
    # AVERAGES
    # =====================================================

    @staticmethod
    def average_order_value():

        orders = (
            SalesMetrics.total_orders()
        )

        sales = (
            SalesMetrics.net_sales()
        )

        if orders <= 0:

            return 0.0

        return (
            sales / orders
        )

    # -----------------------------------------------------

    @staticmethod
    def average_selling_price():

        units = (
            SalesMetrics.total_units()
        )

        sales = (
            SalesMetrics.net_sales()
        )

        if units <= 0:

            return 0.0

        return (
            sales / units
        )

    # =====================================================
    # DASHBOARD SUMMARY
    # =====================================================

    @staticmethod
    def dashboard_summary():

        return {

            "total_rows":
                SalesMetrics.total_rows(),

            "total_orders":
                SalesMetrics.total_orders(),

            "total_units":
                SalesMetrics.total_units(),

            "gross_sales":
                SalesMetrics.gross_sales(),

            "net_sales":
                SalesMetrics.net_sales(),

            "cancelled_orders":
                SalesMetrics.cancelled_orders(),

            "cancelled_value":
                SalesMetrics.cancelled_value(),

            "average_order_value":
                SalesMetrics.average_order_value(),

            "average_selling_price":
                SalesMetrics.average_selling_price()
        }