import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "price_analytics")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mysecret")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def initialize_tables(conn):
    """Creates the dimension and fact tables if they don't exist."""
    with conn.cursor() as cur:
        # 1. SCD Type 2 Dimension Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dim_product (
                product_key SERIAL PRIMARY KEY,
                product_id VARCHAR(10) NOT NULL,
                product_name VARCHAR(100) NOT NULL,
                price NUMERIC(10, 2) NOT NULL,
                valid_from DATE NOT NULL,
                valid_to DATE NOT NULL DEFAULT '9999-12-31',
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                UNIQUE (product_id, valid_from)
            );
        """)

        # 2. Fact Table for Sales
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fact_sales (
                sales_id SERIAL PRIMARY KEY,
                product_id VARCHAR(10) NOT NULL,
                sale_date DATE NOT NULL,
                quantity_sold INT NOT NULL,
                UNIQUE (product_id, sale_date)
            );
        """)
        conn.commit()
    print("✅ Database tables initialized (dim_product, fact_sales).")


def load_scd_type2(conn):
    """
    Loads price history into dim_product using SCD Type 2 logic.
    If price changes, closes previous active record and inserts a new one.
    """
    df_products = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
    df_prices = pd.read_csv(os.path.join(DATA_DIR, "daily_prices.csv"))

    # Merge product details with price history
    df_merged = df_prices.merge(df_products, on="product_id").sort_values(
        by=["product_id", "price_date"]
    )

    with conn.cursor() as cur:
        for product_id, group in df_merged.groupby("product_id"):
            product_name = group["product_name"].iloc[0]
            prev_price = None

            for _, row in group.iterrows():
                curr_price = row["price"]
                price_date = row["price_date"]

                # First price or price changed
                if prev_price is None or curr_price != prev_price:
                    # Close out the old active record
                    cur.execute("""
                        UPDATE dim_product
                        SET valid_to = %s, is_active = FALSE
                        WHERE product_id = %s AND is_active = TRUE;
                    """, (price_date, product_id))

                    # Insert new active record
                    cur.execute("""
                        INSERT INTO dim_product (product_id, product_name, price, valid_from, valid_to, is_active)
                        VALUES (%s, %s, %s, %s, '9999-12-31', TRUE)
                        ON CONFLICT (product_id, valid_from) 
                        DO UPDATE SET price = EXCLUDED.price, is_active = EXCLUDED.is_active;
                    """, (product_id, product_name, curr_price, price_date))

                    prev_price = curr_price

        conn.commit()
    print("✅ SCD Type 2 dim_product loaded successfully.")


def load_fact_sales(conn):
    """Loads daily sales records with ON CONFLICT idempotency."""
    df_sales = pd.read_csv(os.path.join(DATA_DIR, "daily_sales.csv"))

    records = [
        (row["product_id"], row["sale_date"], int(row["quantity_sold"]))
        for _, row in df_sales.iterrows()
    ]

    query = """
        INSERT INTO fact_sales (product_id, sale_date, quantity_sold)
        VALUES %s
        ON CONFLICT (product_id, sale_date)
        DO UPDATE SET quantity_sold = EXCLUDED.quantity_sold;
    """

    with conn.cursor() as cur:
        execute_values(cur, query, records)
        conn.commit()

    print(f"✅ Loaded {len(records)} records into fact_sales.")


def main():
    print("🚀 Connecting to PostgreSQL and running data load...")
    conn = get_connection()
    try:
        initialize_tables(conn)
        load_scd_type2(conn)
        load_fact_sales(conn)
        print("✨ Database load complete!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()