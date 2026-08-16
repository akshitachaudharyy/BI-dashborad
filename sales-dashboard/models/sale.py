from database import db


class Sale(db.Model):

    __tablename__ = "sales"

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