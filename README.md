# Sales BI Dashboard

A single-page business intelligence dashboard for Amazon sales data.
Flask serves the page and a JSON API, MySQL stores the data, and the
BI layer decides which records contribute to each KPI.

## Links

- Live dashboard: [web-production-21caac.up.railway.app](https://web-production-21caac.up.railway.app)
- Repository: [github.com/akshitachaudharyy/BI-dashborad](https://github.com/akshitachaudharyy/BI-dashborad)
- Database: MySQL hosted on Railway (project `bi-dashboard`)

The application and the database both run on Railway. The dashboard
page and the JSON API are served by the same Flask service.

## Stack

- Python / Flask
- MySQL with SQLAlchemy
- HTML, SCSS, vanilla JavaScript
- No frontend framework, no chart library

## Project layout

    sales-dashboard/
        app.py                  application entry point
        config.py               database connection resolution
        database.py             SQLAlchemy instance

        models/                 Sale, ImportBatch
        routes/                 page and API blueprints

        services/
            bi_definitions.py   single source of truth for KPIs
            bi_metrics.py       dashboard summary
            analytics.py        chart aggregations
            query_filters.py    reusable filter layer
            importer.py         CSV / Excel ingestion

        templates/dashboard.html
        static/css/dashboard.scss
        static/css/dashboard.css
        static/js/dashboard.js

        scripts/
            init_database.py    create tables
            import_data.py      load a source file
            test_dashboard.py   API and BI test suite

## Running locally

Create `sales-dashboard/.env` from `.env.example` and fill in your
MySQL credentials, then:

    cd sales-dashboard
    pip install -r requirements.txt
    python -m scripts.init_database
    python -m scripts.import_data "../data/amazon-sale-report.csv"
    python app.py

The dashboard is served at http://127.0.0.1:5000/

To use the Railway database instead of a local one, set `DATABASE_URL`
to the connection string and skip the `.env` values. `config.py` prefers
`DATABASE_URL` over the local settings.

## Tests

    cd sales-dashboard
    python -m scripts.test_dashboard

The suite covers the KPI definitions, every filter, invalid input,
empty results, cancelled transactions and duplicate order IDs.

## API

All endpoints are under `/api/dashboard` and accept the same optional
filters: `date_from`, `date_to`, `status`, `category`, `state`,
`fulfilment`, `sales_channel`. Dates use `YYYY-MM-DD`. Invalid input
returns HTTP 400.

| Endpoint | Returns |
| --- | --- |
| `/summary` | headline KPIs |
| `/trend` | net sales by date |
| `/categories` | net sales by category |
| `/states` | net sales by shipping state |
| `/fulfilment` | net sales by fulfilment channel |
| `/status` | distinct orders and gross value by status |
| `/channels` | net sales by sales channel |
| `/top-products` | net sales by SKU |
| `/filter-options` | distinct values for the filter controls |

Example:

    /api/dashboard/summary?date_from=2022-04-01&date_to=2022-04-30
    /api/dashboard/categories?state=MAHARASHTRA

Responses use a consistent envelope:

    {
        "success": true,
        "filters": { ... },
        "data": { ... }
    }

## KPI definitions

Cancelled rows are never deleted, so the source data stays auditable.
Each measure decides whether a cancelled row contributes to it.

| Measure | Definition |
| --- | --- |
| `total_rows` | count of transaction rows |
| `total_orders` | distinct order IDs, all statuses |
| `valid_orders` | distinct order IDs, excluding cancelled |
| `cancelled_orders` | distinct order IDs that are cancelled |
| `gross_sales` | sum of amount, cancellations included |
| `net_sales` | sum of amount, cancellations excluded |
| `cancelled_value` | sum of amount for cancelled rows |
| `total_units` | sum of quantity, cancellations excluded |
| `average_order_value` | net_sales / valid_orders |
| `average_selling_price` | net_sales / total_units |

One order ID can span several rows, so any measure representing orders
uses `COUNT(DISTINCT order_id)` rather than a row count.

All KPIs are calculated in MySQL. JavaScript only formats values for
display.
