from flask import Flask, jsonify, render_template

from config import Config
from database import db

from models import Sale


def create_app():

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Home page
    @app.route("/")
    def dashboard():
        return render_template("dashboard.html")

    # Health check
    @app.route("/api/health")
    def health():

        return jsonify({
            "status": "success",
            "message": "Sales Analytics API is running"
        })

    # Basic database test
    @app.route("/api/database")
    def database_test():

        try:

            total_records = db.session.query(
                Sale
            ).count()

            return jsonify({
                "status": "success",
                "database": "connected",
                "records": total_records
            })

        except Exception as error:

            return jsonify({
                "status": "error",
                "database": "connection failed",
                "message": str(error)
            }), 500

    return app


app = create_app()


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )