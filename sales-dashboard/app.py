from flask import Flask, jsonify

from config import Config
from database import db
from routes.dashboard import dashboard_api, dashboard_bp
from routes.pages import pages_bp


# =========================================================
# APPLICATION
# =========================================================

app = Flask(__name__)


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

app.config.from_object(Config)


# =========================================================
# INITIALIZE DATABASE
# =========================================================

db.init_app(app)


# =========================================================
# REGISTER ROUTES
# =========================================================
#
# pages_bp       -> rendered HTML ("/", "/dashboard")
# dashboard_bp   -> KPI summary   ("/api/dashboard/summary")
# dashboard_api  -> analytics     ("/api/dashboard/trend", ...)
# =========================================================

app.register_blueprint(
    pages_bp
)

app.register_blueprint(
    dashboard_bp
)

app.register_blueprint(
    dashboard_api
)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "success": True,

        "message":
            "Sales Dashboard API is running"

    })


# =========================================================
# SERVICE INFO
# =========================================================
#
# "/" now renders the dashboard page, so the previous
# JSON service descriptor lives here instead.
# =========================================================

@app.route(
    "/api/info",
    methods=["GET"]
)
def info():

    return jsonify({

        "application":
            "Sales BI Dashboard",

        "status":
            "running",

        "api":
            "/api/dashboard/summary"

    })


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
