
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

required_settings = [
    "PGHOST",
    "PGPORT",
    "PGDATABASE",
    "PGUSER",
    "PGPASSWORD",
]

missing = [
    name for name in required_settings
    if not os.getenv(name)
]

if missing:
    raise RuntimeError(
        "Missing settings in .env: " + ", ".join(missing)
    )

connection = None

try:
    connection = psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        connect_timeout=5,
    )

    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), version()")
        database, version = cursor.fetchone()

    print("Connection successful!")
    print(f"Database: {database}")
    print(f"PostgreSQL: {version.split(',')[0]}")

except psycopg2.Error as error:
    print("Database connection failed.")
    print(f"Error: {error}")

finally:
    if connection is not None:
        connection.close()
