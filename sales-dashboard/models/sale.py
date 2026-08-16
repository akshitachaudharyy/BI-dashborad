from database import db


class Sale(db.Model):

    __tablename__ = "sales"

    # -----------------------------------------------------
    # Composite indexes
    # -----------------------------------------------------
    #
    # Every dashboard FILTER column already carries its own
    # single-column index below, and EXPLAIN confirms those
    # are used (type=ref) for selective filters. Only one
    # composite index earns its place:
    #
    #   (sku, style, category)
    #       supports the /top-products GROUP BY, which is
    #       the heaviest dashboard query. Measured on the
    #       129k-row dataset: 592ms -> 262ms.
    #
    # No other composite index was added: unfiltered
    # summary aggregates must scan the whole table anyway,
    # so an index cannot help them.
    # -----------------------------------------------------

    __table_args__ = (
        db.Index(
            "ix_sales_sku_style_category",
            "sku",
            "style",
            "category"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    # -----------------------------------------------------
    # Source information
    # -----------------------------------------------------

    source_index = db.Column(
        db.Integer,
        nullable=False,
        index=True
    )

    # -----------------------------------------------------
    # Order
    # -----------------------------------------------------

    order_id = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    order_date = db.Column(
        db.Date,
        nullable=True,
        index=True
    )

    status = db.Column(
        db.String(100),
        nullable=True,
        index=True
    )

    # -----------------------------------------------------
    # Fulfilment
    # -----------------------------------------------------

    fulfilment = db.Column(
        db.String(100),
        nullable=True,
        index=True
    )

    fulfilled_by = db.Column(
        db.String(100),
        nullable=True
    )

    courier_status = db.Column(
        db.String(100),
        nullable=True,
        index=True
    )

    # -----------------------------------------------------
    # Sales channel
    # -----------------------------------------------------

    sales_channel = db.Column(
        db.String(100),
        nullable=True,
        index=True
    )

    ship_service_level = db.Column(
        db.String(100),
        nullable=True
    )

    # -----------------------------------------------------
    # Product
    # -----------------------------------------------------

    style = db.Column(
        db.String(255),
        nullable=True
    )

    sku = db.Column(
        db.String(255),
        nullable=True,
        index=True
    )

    category = db.Column(
        db.String(100),
        nullable=True,
        index=True
    )

    size = db.Column(
        db.String(50),
        nullable=True
    )

    asin = db.Column(
        db.String(100),
        nullable=True,
        index=True
    )

    # -----------------------------------------------------
    # Shipping
    # -----------------------------------------------------

    ship_city = db.Column(
        db.String(255),
        nullable=True,
        index=True
    )

    ship_state = db.Column(
        db.String(255),
        nullable=True,
        index=True
    )

    ship_postal_code = db.Column(
        db.String(20),
        nullable=True
    )

    ship_country = db.Column(
        db.String(100),
        nullable=True
    )

    # -----------------------------------------------------
    # Financial
    # -----------------------------------------------------

    quantity = db.Column(
        db.Integer,
        nullable=True
    )

    currency = db.Column(
        db.String(20),
        nullable=True
    )

    amount = db.Column(
        db.Numeric(12, 2),
        nullable=True
    )

    # -----------------------------------------------------
    # Other
    # -----------------------------------------------------

    promotion_ids = db.Column(
        db.Text,
        nullable=True
    )

    b2b = db.Column(
        db.Boolean,
        nullable=True
    )

    def __repr__(self):

        return f"<Sale {self.order_id}>"