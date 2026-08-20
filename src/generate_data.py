import os
import random
from datetime import date, timedelta
from faker import Faker
import pandas as pd

# Set a random seed so results are repeatable
fake = Faker()
random.seed(42)
Faker.seed(42)

# Ensure the data output directory exists
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

NUM_PRODUCTS = 50
DAYS = 90
TODAY = date.today()
START_DATE = TODAY - timedelta(days=DAYS)


def generate_products():
    """Generates a catalog of 50 unique products."""
    products = []
    for i in range(1, NUM_PRODUCTS + 1):
        product_id = f"P{i:03d}"
        name = f"{fake.color_name().capitalize()} {fake.word().capitalize()}"
        base_cost = round(random.uniform(10.0, 150.0), 2)
        products.append({
            "product_id": product_id,
            "product_name": name,
            "base_cost": base_cost
        })
    df = pd.DataFrame(products)
    df.to_csv(os.path.join(DATA_DIR, "products.csv"), index=False)
    print(f"✅ Generated {len(df)} products -> data/products.csv")
    return df


def generate_price_and_sales(products_df):
    """
    Generates daily prices and sales records for 90 days.
    Injects price-elasticity logic: if price increases, sales volume drops by ~20%.
    """
    prices = []
    sales = []

    for _, prod in products_df.iterrows():
        p_id = prod["product_id"]
        current_price = prod["base_cost"]

        for day_offset in range(DAYS):
            current_date = START_DATE + timedelta(days=day_offset)

            # Price change logic: 30% chance of price change on any given day
            price_changed = False
            price_increased = False

            if day_offset > 0 and random.random() < 0.30:
                price_changed = True
                price_delta = round(random.uniform(-10.0, 15.0), 2)
                new_price = max(5.0, round(current_price + price_delta, 2))
                if new_price > current_price:
                    price_increased = True
                current_price = new_price

            prices.append({
                "product_id": p_id,
                "price_date": current_date,
                "price": current_price
            })

            # Base sales volume between 10 and 60 units per product per day
            base_sales = random.randint(10, 60)

            # If the price increased, reduce sales volume by ~20%
            if price_increased:
                sales_volume = max(1, int(base_sales * 0.80))
            else:
                sales_volume = base_sales

            sales.append({
                "product_id": p_id,
                "sale_date": current_date,
                "quantity_sold": sales_volume
            })

    # Save to CSV
    df_prices = pd.DataFrame(prices)
    df_sales = pd.DataFrame(sales)

    df_prices.to_csv(os.path.join(DATA_DIR, "daily_prices.csv"), index=False)
    df_sales.to_csv(os.path.join(DATA_DIR, "daily_sales.csv"), index=False)

    print(f"✅ Generated {len(df_prices)} price records -> data/daily_prices.csv")
    print(f"✅ Generated {len(df_sales)} sales records -> data/daily_sales.csv")


if __name__ == "__main__":
    print("🚀 Starting synthetic data generation...")
    prods = generate_products()
    generate_price_and_sales(prods)
    print("✨ Synthetic data generation completed successfully!")