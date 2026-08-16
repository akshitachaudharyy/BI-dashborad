"""
=========================================================
DASHBOARD JSON API
=========================================================

Two blueprints share the /api/dashboard prefix:

    dashboard_bp   /summary, /filter-options
    dashboard_api  /, /kpis, /trend, /categories, /states,
                   /fulfilment, /status, /channels,
                   /top-products

Every endpoint accepts the same optional filters, parsed
and validated by services/query_filters.DashboardFilters:

    date_from, date_to, status, category, state,
    fulfilment, sales_channel

Invalid input returns HTTP 400 with a useful message.
Filtering and aggregation happen in MySQL.
"""

from flask import (
    Blueprint,
    jsonify,
    request
)

from services.analytics import (

    get_dashboard_data,

    get_kpis,

    get_sales_trend,

    get_category_sales,

    get_state_sales,

    get_fulfilment,

    get_order_status,

    get_sales_channel,

    get_top_products
)

from services.bi_metrics import SalesMetrics

from services.query_filters import (
    DashboardFilters,
    FilterError
)


# =========================================================
# SHARED RESPONSE HANDLING
# =========================================================

def _respond(builder):
    """
    Parse filters, run `builder(filters)`, wrap the result.

    Success:  {"success": true, "filters": {...}, "data": ...}
    Bad input: HTTP 400
    Failure:   HTTP 500

    Echoing the applied filters lets the frontend confirm
    the numbers on screen describe the filters it asked
    for, rather than a stale request.
    """

    try:
        filters = DashboardFilters.from_request(request.args)

    except FilterError as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    try:
        data = builder(filters)

    except Exception as error:  # noqa: BLE001

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

    return jsonify({
        "success": True,
        "filters": filters.as_dict(),
        "data": data
    })


# =========================================================
# SUMMARY BLUEPRINT
# =========================================================

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/dashboard"
)


@dashboard_bp.route(
    "/summary",
    methods=["GET"]
)
def dashboard_summary():
    """Headline KPIs. See services/bi_definitions.py."""

    return _respond(SalesMetrics.dashboard_summary)


@dashboard_bp.route(
    "/filter-options",
    methods=["GET"]
)
def filter_options():
    """
    Distinct filter values read from MySQL.

    Deliberately unfiltered: the control lists must offer
    every value in the dataset, not only those surviving
    the current selection.
    """

    try:
        data = SalesMetrics.filter_options()

    except Exception as error:  # noqa: BLE001

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

    return jsonify({
        "success": True,
        "data": data
    })


# =========================================================
# ANALYTICS BLUEPRINT
# =========================================================

dashboard_api = Blueprint(
    "dashboard_api",
    __name__,
    url_prefix="/api/dashboard"
)


@dashboard_api.route(
    "/",
    methods=["GET"]
)
def dashboard():
    """Every dataset in one payload."""

    return _respond(get_dashboard_data)


@dashboard_api.route(
    "/kpis",
    methods=["GET"]
)
def kpis():
    """Alias of /summary -- same SalesMetrics call."""

    return _respond(get_kpis)


@dashboard_api.route(
    "/trend",
    methods=["GET"]
)
def trend():
    """Net sales by order_date."""

    return _respond(get_sales_trend)


@dashboard_api.route(
    "/categories",
    methods=["GET"]
)
def categories():
    """Net sales by category."""

    return _respond(get_category_sales)


@dashboard_api.route(
    "/states",
    methods=["GET"]
)
def states():
    """Net sales by ship_state."""

    return _respond(get_state_sales)


@dashboard_api.route(
    "/fulfilment",
    methods=["GET"]
)
def fulfilment():
    """Net sales by fulfilment."""

    return _respond(get_fulfilment)


@dashboard_api.route(
    "/status",
    methods=["GET"]
)
def status():
    """Distinct orders and GROSS value by status."""

    return _respond(get_order_status)


@dashboard_api.route(
    "/channels",
    methods=["GET"]
)
def channels():
    """Net sales by sales_channel."""

    return _respond(get_sales_channel)


@dashboard_api.route(
    "/top-products",
    methods=["GET"]
)
def top_products():
    """Net sales by SKU, highest first."""

    return _respond(get_top_products)
