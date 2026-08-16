from flask import (
    Blueprint,
    render_template
)


# =========================================================
# PAGE ROUTES
# =========================================================
#
# This blueprint serves rendered HTML only.
#
# All KPI/analytics data is fetched by the browser from
# the JSON API (see routes/dashboard.py). No business
# logic belongs in this module or in the template.
# =========================================================

pages_bp = Blueprint(
    "pages",
    __name__
)


@pages_bp.route(
    "/",
    methods=["GET"]
)
@pages_bp.route(
    "/dashboard",
    methods=["GET"]
)
def dashboard_page():

    return render_template(
        "dashboard.html"
    )
