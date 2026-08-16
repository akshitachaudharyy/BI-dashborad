from flask import (
    Flask,
    jsonify,
    render_template
)

from config import Config
from database import db

# Import models
from models import Sale, ImportBatch


def create_app():

    app = Flask(
        __name__
    )

    # -----------------------------------------------------
    # Configuration
    # -----------------------------------------------------

    app.config.from_object(
        Config
    )

    # -----------------------------------------------------
    # Database
    # -----------------------------------------------------

    db.init_app(
        app
    )

    # -----------------------------------------------------
    # Routes
    # -----------------------------------------------------

    @app.route("/")
    def dashboard():

        return render_template(
            "dashboard.html"
        )

    # -----------------------------------------------------
    # Health check
    # -----------------------------------------------------

    @app.route(
        "/api/health"
    )
    def health():

        return jsonify({

            "status": "success",

            "message":
                "Sales Analytics API is running"
        })

    # -----------------------------------------------------
    # Database check
    # -----------------------------------------------------

    @app.route(
        "/api/database"
    )
    def database_test():

        try:

            total_records = (
                db.session
                .query(Sale)
                .count()
            )

            total_imports = (
                db.session
                .query(ImportBatch)
                .count()
            )

            return jsonify({

                "status":
                    "success",

                "database":
                    "connected",

                "sales_records":
                    total_records,

                "import_batches":
                    total_imports
            })

        except Exception as error:

            return jsonify({

                "status":
                    "error",

                "database":
                    "connection failed",

                "message":
                    str(error)
            }), 500

    return app


app = create_app()


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )