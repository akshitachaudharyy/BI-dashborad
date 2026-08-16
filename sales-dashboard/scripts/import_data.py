import sys

from app import create_app
from services.importer import import_file


def main():

    if len(sys.argv) < 2:

        print(
            "Usage:"
        )

        print(
            "python -m scripts.import_data "
            "<file_path>"
        )

        sys.exit(1)

    file_path = sys.argv[1]

    app = create_app()

    with app.app_context():

        try:

            result = import_file(
                file_path
            )

            print()
            print("=" * 50)
            print("IMPORT SUCCESSFUL")
            print("=" * 50)

            print(
                f"Batch ID: "
                f"{result['batch_id']}"
            )

            print(
                f"File: "
                f"{result['file_name']}"
            )

            print(
                f"Rows: "
                f"{result['rows_imported']:,}"
            )

        except Exception as error:

            print()
            print("=" * 50)
            print("IMPORT FAILED")
            print("=" * 50)

            print(error)

            sys.exit(1)


if __name__ == "__main__":
    main()