from app import create_app
from database import db

# Important:
# Import models before db.create_all()
from models import Sale, ImportBatch


def main():

    app = create_app()

    with app.app_context():

        db.create_all()

        print(
            "Database tables created successfully."
        )


if __name__ == "__main__":
    main()