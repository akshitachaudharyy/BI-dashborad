from flask import (
    Blueprint,
    jsonify
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

    return jsonify(
        get_dashboard_data()
    )


@dashboard_api.route(
    "/kpis",
    methods=["GET"]
)
def kpis():

    return jsonify(
        get_kpis()
    )


@dashboard_api.route(
    "/trend",
    methods=["GET"]
)
def trend():

    return jsonify(
        get_sales_trend()
    )


@dashboard_api.route(
    "/categories",
    methods=["GET"]
)
def categories():

    return jsonify(
        get_category_sales()
    )


@dashboard_api.route(
    "/states",
    methods=["GET"]
)
def states():

    return jsonify(
        get_state_sales()
    )


@dashboard_api.route(
    "/fulfilment",
    methods=["GET"]
)
def fulfilment():

    return jsonify(
        get_fulfilment()
    )


@dashboard_api.route(
    "/status",
    methods=["GET"]
)
def status():

    return jsonify(
        get_order_status()
    )


@dashboard_api.route(
    "/channels",
    methods=["GET"]
)
def channels():

    return jsonify(
        get_sales_channel()
    )


@dashboard_api.route(
    "/top-products",
    methods=["GET"]
)
def top_products():

    return jsonify(
        get_top_products()
    )