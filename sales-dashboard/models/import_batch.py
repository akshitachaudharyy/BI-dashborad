from database import db


class ImportBatch(db.Model):

    __tablename__ = "import_batches"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    file_name = db.Column(
        db.String(255),
        nullable=False
    )

    file_hash = db.Column(
        db.String(64),
        nullable=False,
        unique=True,
        index=True
    )

    row_count = db.Column(
        db.Integer,
        nullable=False
    )

    status = db.Column(
        db.String(50),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def __repr__(self):

        return f"<ImportBatch {self.file_name}>"