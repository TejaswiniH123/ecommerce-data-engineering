
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

connection = psycopg2.connect(
    host=os.getenv("PGHOST", "localhost"),
    port=os.getenv("PGPORT", "5432"),
    dbname=os.getenv("PGDATABASE", "ecommerce_dw"),
    user=os.getenv("PGUSER", "postgres"),
    password=os.getenv("PGPASSWORD"),
)

try:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM customers),
                (SELECT COUNT(*) FROM orders),
                (SELECT COUNT(*) FROM order_items),
                (SELECT COUNT(*) FROM orders
                 WHERE order_id LIKE 'TEST_%')
        """)

        customers, orders, order_items, synthetic_orders = cursor.fetchone()

        print(f"Customers: {customers:,}")
        print(f"Orders: {orders:,}")
        print(f"Order items: {order_items:,}")
        print(f"Synthetic orders: {synthetic_orders}")

        if (
            customers == 99441
            and orders == 99441
            and order_items == 112650
            and synthetic_orders == 0
        ):
            print("PASS: Warehouse baseline is verified.")
        else:
            print("WARNING: Counts differ from the expected baseline.")

finally:
    connection.close()
