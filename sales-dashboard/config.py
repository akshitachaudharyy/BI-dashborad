"""
=========================================================
APPLICATION CONFIGURATION
=========================================================

Resolves the database connection in this order:

  1. DATABASE_URL / MYSQL_URL      (Railway, Heroku, etc.)
  2. MYSQLHOST / MYSQLUSER / ...   (Railway's discrete vars)
  3. MYSQL_HOST / MYSQL_USER / ... (local .env)

Local development keeps working unchanged: with none of
the platform variables set, it falls through to the .env
values it has always used.
"""

import os

from urllib.parse import quote_plus, urlparse

from dotenv import load_dotenv


# Local .env only. On a platform the real environment
# already holds the values and takes precedence.
load_dotenv()


# =========================================================
# HELPERS
# =========================================================

def _first_env(*names, default=None):
    """First environment variable that is set and non-empty."""

    for name in names:

        value = os.getenv(name)

        if value:
            return value

    return default


def _normalise_url(url):
    """
    Force the PyMySQL driver onto a platform-supplied URL.

    Railway hands out `mysql://user:pass@host:port/db`.
    SQLAlchemy would try the (uninstalled) MySQLdb driver
    for that scheme, so rewrite it to mysql+pymysql://.

    The password is re-encoded because Railway generates
    passwords containing characters such as '#' and '@',
    which break URL parsing when passed through raw.
    """

    parsed = urlparse(url)

    if parsed.scheme in ("mysql", "mysql+mysqldb"):

        username = quote_plus(parsed.username or "")
        password = quote_plus(parsed.password or "")
        host = parsed.hostname or ""
        port = parsed.port or 3306
        database = (parsed.path or "/").lstrip("/")

        return (
            f"mysql+pymysql://{username}:{password}"
            f"@{host}:{port}/{database}"
        )

    return url


def _build_uri():

    # ---- 1. Full connection URL -------------------------

    url = _first_env(
        "DATABASE_URL",
        "MYSQL_URL",
        "MYSQL_PUBLIC_URL"
    )

    if url:
        return _normalise_url(url)

    # ---- 2/3. Discrete variables ------------------------
    #
    # Railway exposes MYSQLHOST/MYSQLUSER/...; the local
    # .env uses MYSQL_HOST/MYSQL_USER/...

    host = _first_env("MYSQLHOST", "MYSQL_HOST", default="localhost")
    port = _first_env("MYSQLPORT", "MYSQL_PORT", default="3306")
    user = _first_env("MYSQLUSER", "MYSQL_USER", default="root")
    password = _first_env("MYSQLPASSWORD", "MYSQL_PASSWORD", default="")

    database = _first_env(
        "MYSQLDATABASE",
        "MYSQL_DATABASE",
        default="sales_dashboard"
    )

    # Escape credentials so characters such as # @ : /
    # do not break the connection URI.
    return (
        f"mysql+pymysql://"
        f"{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{database}"
    )


# =========================================================
# CONFIG
# =========================================================

class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "development-secret-key"
    )

    SQLALCHEMY_DATABASE_URI = _build_uri()

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Managed MySQL instances drop idle connections. Recycle
    # below the typical 5-minute idle timeout and verify a
    # connection before handing it out, so the dashboard does
    # not fail on the first request after a quiet period.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280
    }
