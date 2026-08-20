import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(ROOT_DIR, ".env"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "price_analytics")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


def execute_analytics():
    sql_path = os.path.join(ROOT_DIR, "src", "analytics.sql")
    with open(sql_path, "r") as f:
        sql_script = f.read()

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    with conn.cursor() as cur:
        print("🧠 Creating analytical views and running window functions...")
        cur.execute(sql_script)
        conn.commit()

        # Query top 5 high-risk alerts to verify
        cur.execute("""
            SELECT product_id, product_name, pct_price_change, pct_sales_volume_change, elasticity_flag 
            FROM v_product_price_impact 
            WHERE elasticity_flag = 'HIGH RISK (ELASTIC DROP)' 
            LIMIT 5;
        """)
        rows = cur.fetchall()

        print("\n🚨 Sample High-Risk Elasticity Alerts Flagged by SQL:")
        print("-" * 75)
        for r in rows:
            print(f"Product: {r[0]} ({r[1]}) | Price Δ: +{r[2]}% | Sales Δ: {r[3]}% | Status: {r[4]}")
        print("-" * 75)

    conn.close()
    print("✨ Analytics view `v_product_price_impact` created successfully!")


if __name__ == "__main__":
    execute_analytics()