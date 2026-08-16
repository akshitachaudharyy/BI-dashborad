from app import app

from services.bi_metrics import SalesMetrics


def main():

    print()
    print("=" * 60)
    print("BI METRICS TEST")
    print("=" * 60)

    with app.app_context():

        summary = (
            SalesMetrics
            .dashboard_summary()
        )

        for key, value in summary.items():

            print(
                f"{key:30} : {value}"
            )

    print("=" * 60)
    print()


if __name__ == "__main__":

    main()