"""
Generate synthetic raw e-commerce data with intentional data quality issues.
"""
import csv
import random
from pathlib import Path
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

N_CUSTOMERS = 200
N_PRODUCTS = 50
N_ORDERS = 500
MAX_ITEMS_PER_ORDER = 5


def generate_customers():
    rows = []
    for i in range(1, N_CUSTOMERS + 1):
        email = fake.email()
        if random.random() < 0.05:
            email = ""
        elif random.random() < 0.03:
            email = email.upper()
        name = fake.name()
        if random.random() < 0.04:
            name = f"  {name}  "
        rows.append({
            "customer_id": i,
            "name": name,
            "email": email,
            "country": fake.country(),
            "signup_date": fake.date_between(start_date="-3y", end_date="today").isoformat(),
        })
    dup = dict(rows[0])
    dup["email"] = "duplicate@example.com"
    rows.append(dup)
    return rows


def generate_products():
    categories = ["Electronics", "Clothing", "Books", "Home", "Toys", "Sports"]
    return [
        {
            "product_id": i,
            "name": fake.catch_phrase(),
            "category": random.choice(categories),
            "price": round(random.uniform(5, 500), 2),
        }
        for i in range(1, N_PRODUCTS + 1)
    ]


def generate_orders():
    statuses = ["pending", "shipped", "delivered", "cancelled"]
    rows = []
    for i in range(1, N_ORDERS + 1):
        rows.append({
            "order_id": i,
            "customer_id": random.randint(1, N_CUSTOMERS),
            "order_date": fake.date_time_between(start_date="-1y", end_date="now").isoformat(),
            "status": random.choice(statuses),
        })
    for _ in range(3):
        rows.append({
            "order_id": len(rows) + 1,
            "customer_id": 99999,
            "order_date": fake.date_time_between(start_date="-1y", end_date="now").isoformat(),
            "status": random.choice(statuses),
        })
    return rows


def generate_order_items(orders, products):
    rows = []
    item_id = 1
    for order in orders:
        for _ in range(random.randint(1, MAX_ITEMS_PER_ORDER)):
            product = random.choice(products)
            quantity = random.randint(1, 4)
            if random.random() < 0.02:
                quantity = -quantity
            rows.append({
                "item_id": item_id,
                "order_id": order["order_id"],
                "product_id": product["product_id"],
                "quantity": quantity,
                "unit_price": product["price"],
            })
            item_id += 1
    for _ in range(5):
        rows.append({
            "item_id": item_id,
            "order_id": 88888,
            "product_id": random.randint(1, N_PRODUCTS),
            "quantity": 1,
            "unit_price": 10.0,
        })
        item_id += 1
    return rows


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def main():
    print("Generating synthetic e-commerce data with intentional DQ issues...")
    customers = generate_customers()
    products = generate_products()
    orders = generate_orders()
    order_items = generate_order_items(orders, products)
    write_csv(RAW_DIR / "customers.csv", customers)
    write_csv(RAW_DIR / "products.csv", products)
    write_csv(RAW_DIR / "orders.csv", orders)
    write_csv(RAW_DIR / "order_items.csv", order_items)
    print(f"  customers.csv:   {len(customers)} rows")
    print(f"  products.csv:    {len(products)} rows")
    print(f"  orders.csv:      {len(orders)} rows")
    print(f"  order_items.csv: {len(order_items)} rows")
    print(f"Raw data written to: {RAW_DIR}")


if __name__ == "__main__":
    main()