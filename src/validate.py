import os
import sys
from datetime import date
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TODAY = date.today()


def validate_file_exists(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        print(f" [FAIL] Missing file: {filename}")
        sys.exit(1)
    return filepath


def validate_products():
    path = validate_file_exists("products.csv")
    df = pd.read_csv(path)

    # 1. Null check
    if df["product_id"].isnull().any():
        print("❌ [FAIL] Data Quality Violation: Null product_id found in products.csv")
        sys.exit(1)

    # 2. Base cost positive check
    if (df["base_cost"] <= 0).any():
        print("❌ [FAIL] Data Quality Violation: Non-positive base_cost found in products.csv")
        sys.exit(1)

    print("✅ products.csv passed all quality checks.")


def validate_daily_prices():
    path = validate_file_exists("daily_prices.csv")
    df = pd.read_csv(path)
    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date

    # 1. Null checks
    if df["product_id"].isnull().any() or df["price"].isnull().any():
        print("❌ [FAIL] Data Quality Violation: Null values in daily_prices.csv")
        sys.exit(1)

    # 2. Negative price check
    if (df["price"] <= 0).any():
        bad_rows = df[df["price"] <= 0]
        print(f"❌ [FAIL] Data Quality Violation: Negative/zero price detected for Product {bad_rows['product_id'].iloc[0]}")
        sys.exit(1)

    # 3. Future date check
    if (df["price_date"] > TODAY).any():
        print("❌ [FAIL] Data Quality Violation: Future dates detected in daily_prices.csv")
        sys.exit(1)

    print("✅ daily_prices.csv passed all quality checks.")


def validate_daily_sales():
    path = validate_file_exists("daily_sales.csv")
    df = pd.read_csv(path)
    df["sale_date"] = pd.to_datetime(df["sale_date"]).dt.date

    # 1. Null checks
    if df["product_id"].isnull().any() or df["quantity_sold"].isnull().any():
        print("❌ [FAIL] Data Quality Violation: Null values in daily_sales.csv")
        sys.exit(1)

    # 2. Quantity non-negative check
    if (df["quantity_sold"] < 0).any():
        print("❌ [FAIL] Data Quality Violation: Negative quantity_sold in daily_sales.csv")
        sys.exit(1)

    # 3. Future date check
    if (df["sale_date"] > TODAY).any():
        print("❌ [FAIL] Data Quality Violation: Future dates detected in daily_sales.csv")
        sys.exit(1)

    print("✅ daily_sales.csv passed all quality checks.")


def run_all_validations():
    print("🛡️ Running Data Quality Gates...")
    validate_products()
    validate_daily_prices()
    validate_daily_sales()
    print("✨ All data quality gates passed! Ready for database loading.")


if __name__ == "__main__":
    run_all_validations()