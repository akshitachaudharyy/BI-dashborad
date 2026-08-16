from app import app
from database import db

from models import (
    Sale,
    ImportBatch
)


def main():

    with app.app_context():

        db.create_all()

        print(
            "Database tables created successfully."
        )


if __name__ == "__main__":
    main()