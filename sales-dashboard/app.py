from flask import (
    Flask,
    jsonify,
    render_template
)

from config import Config

from database import db

from models import (
    Sale,
    ImportBatch
)

from routes.dashboard import (
    dashboard_api
)


def create_app():

    app = Flask(
        __name__
    )

    # -----------------------------------------------------
    # Config
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
    # API
    # -----------------------------------------------------

    app.register_blueprint(
        dashboard_api
    )

    # -----------------------------------------------------
    # Dashboard
    # -----------------------------------------------------

    @app.route("/")
    def dashboard():

        return render_template(
            "dashboard.html"
        )

    # -----------------------------------------------------
    # Health
    # -----------------------------------------------------

    @app.route(
        "/api/health"
    )
    def health():

        return jsonify({

            "status":
                "success",

            "message":
                "Sales Analytics API is running"
        })

    # -----------------------------------------------------
    # Database
    # -----------------------------------------------------

    @app.route(
        "/api/database"
    )
    def database_test():

        try:

            sales_count = (

                db.session

                .query(Sale)

                .count()
            )

            import_count = (

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
                    sales_count,

                "import_batches":
                    import_count
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