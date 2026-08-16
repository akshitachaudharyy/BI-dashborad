from flask import Flask, jsonify

from config import Config
from database import db
from routes.dashboard import dashboard_bp


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

app.register_blueprint(
    dashboard_bp
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
# ROOT
# =========================================================

@app.route("/")
def index():

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