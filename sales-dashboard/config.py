import os

from dotenv import load_dotenv


load_dotenv()


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "development-secret-key"
    )

    MYSQL_HOST = os.getenv(
        "MYSQL_HOST",
        "localhost"
    )

    MYSQL_PORT = os.getenv(
        "MYSQL_PORT",
        "3306"
    )

    MYSQL_DATABASE = os.getenv(
        "MYSQL_DATABASE",
        "sales_dashboard"
    )

    MYSQL_USER = os.getenv(
        "MYSQL_USER",
        "root"
    )

    MYSQL_PASSWORD = os.getenv(
        "MYSQL_PASSWORD",
        ""
    )

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://"
        f"{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/"
        f"{MYSQL_DATABASE}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False