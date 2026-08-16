"""
=========================================================
REUSABLE DASHBOARD FILTER LAYER
=========================================================

Every dashboard endpoint accepts the same optional query
parameters and interprets them identically, because they
all build their criteria here:

    request args
          |
    DashboardFilters.from_request()   <- validates
          |
    .conditions()                     <- SQLAlchemy criteria
          |
    base query  ->  aggregation  ->  API

Supported parameters
--------------------

    date_from       YYYY-MM-DD   inclusive lower bound
    date_to         YYYY-MM-DD   inclusive upper bound
    status          exact match, case-insensitive
    category        exact match, case-insensitive
    state           exact match, case-insensitive (ship_state)
    fulfilment      exact match, case-insensitive
    sales_channel   exact match, case-insensitive

All filters are optional. With no parameters the complete
dataset is returned.

Filtering happens in MySQL. Rows are never shipped to the
browser for client-side filtering.
"""

from datetime import datetime

from models import Sale


DATE_FORMAT = "%Y-%m-%d"


# =========================================================
# ERROR
# =========================================================

class FilterError(ValueError):
    """Raised for invalid filter input -> HTTP 400."""

    pass


# =========================================================
# PARSING HELPERS
# =========================================================

def _clean_text(value):
    """Trim a value, treating blanks as "not supplied"."""

    if value is None:
        return None

    cleaned = str(value).strip()

    return cleaned or None


def _parse_date(value, field_name):
    """
    Strict YYYY-MM-DD parsing.

    Ambiguous formats are rejected rather than guessed --
    silently reinterpreting a date would corrupt every KPI
    on the dashboard.
    """

    cleaned = _clean_text(value)

    if cleaned is None:
        return None

    try:
        return datetime.strptime(
            cleaned,
            DATE_FORMAT
        ).date()

    except ValueError:

        raise FilterError(
            f"Invalid '{field_name}' value: '{cleaned}'. "
            f"Expected format YYYY-MM-DD."
        )


# =========================================================
# FILTER SET
# =========================================================

class DashboardFilters:

    FIELDS = (
        "date_from",
        "date_to",
        "status",
        "category",
        "state",
        "fulfilment",
        "sales_channel"
    )

    def __init__(
        self,
        date_from=None,
        date_to=None,
        status=None,
        category=None,
        state=None,
        fulfilment=None,
        sales_channel=None
    ):

        self.date_from = date_from
        self.date_to = date_to
        self.status = status
        self.category = category
        self.state = state
        self.fulfilment = fulfilment
        self.sales_channel = sales_channel

    # -----------------------------------------------------
    # Construction
    # -----------------------------------------------------

    @classmethod
    def from_request(cls, args):
        """
        Build a validated filter set from request.args.

        Raises FilterError on invalid input.
        """

        date_from = _parse_date(
            args.get("date_from"),
            "date_from"
        )

        date_to = _parse_date(
            args.get("date_to"),
            "date_to"
        )

        if date_from and date_to and date_from > date_to:

            raise FilterError(
                f"'date_from' ({date_from.isoformat()}) is after "
                f"'date_to' ({date_to.isoformat()})."
            )

        return cls(
            date_from=date_from,
            date_to=date_to,
            status=_clean_text(args.get("status")),
            category=_clean_text(args.get("category")),
            state=_clean_text(args.get("state")),
            fulfilment=_clean_text(args.get("fulfilment")),
            sales_channel=_clean_text(args.get("sales_channel"))
        )

    # -----------------------------------------------------
    # Criteria
    # -----------------------------------------------------

    def conditions(self):
        """
        SQLAlchemy criteria for these filters.

        Returned as a list so callers can use either
        query.filter(*conditions) or select().where(...).
        """

        criteria = []

        if self.date_from is not None:
            criteria.append(Sale.order_date >= self.date_from)

        if self.date_to is not None:
            criteria.append(Sale.order_date <= self.date_to)

        # Plain equality on purpose.
        #
        # These columns are utf8mb4_unicode_ci, so `=` is
        # ALREADY case-insensitive: status='shipped' matches
        # 'Shipped'. Wrapping the column in LOWER()/TRIM()
        # would add nothing AND make the predicate
        # non-sargable, forcing a full table scan instead of
        # using ix_sales_status / ix_sales_category /
        # ix_sales_ship_state (verified with EXPLAIN:
        # type=ALL vs type=ref).
        #
        # The supplied VALUE is still trimmed, in
        # _clean_text, so stray whitespace from the UI does
        # not break a match.
        text_filters = (
            (self.status, Sale.status),
            (self.category, Sale.category),
            (self.state, Sale.ship_state),
            (self.fulfilment, Sale.fulfilment),
            (self.sales_channel, Sale.sales_channel)
        )

        for value, column in text_filters:

            if value is not None:
                criteria.append(column == value)

        return criteria

    def apply(self, query):
        """Apply these filters to an existing query."""

        criteria = self.conditions()

        if criteria:
            query = query.filter(*criteria)

        return query

    # -----------------------------------------------------
    # Introspection
    # -----------------------------------------------------

    def is_empty(self):

        return not any(
            getattr(self, field) is not None
            for field in self.FIELDS
        )

    def as_dict(self):
        """JSON-safe echo of the applied filters."""

        payload = {}

        for field in self.FIELDS:

            value = getattr(self, field)

            if value is None:
                payload[field] = None

            elif hasattr(value, "isoformat"):
                payload[field] = value.isoformat()

            else:
                payload[field] = value

        return payload
