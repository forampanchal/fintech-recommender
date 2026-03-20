import pandas as pd
import numpy as np
import os
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()
np.random.seed(42)
random.seed(42)

# ─────────────────────────────
# CONFIG
# ─────────────────────────────
N_CUSTOMERS = 10000
N_TRANSACTIONS_PER_CUSTOMER = (10, 50)  # random range
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)

# ─────────────────────────────
# PRODUCT CATALOG
# ─────────────────────────────
PRODUCTS = {
    "P001": "checking_account",
    "P002": "savings_account",
    "P003": "travel_credit_card",
    "P004": "cashback_credit_card",
    "P005": "personal_loan",
    "P006": "home_loan",
    "P007": "investment_fund",
    "P008": "fixed_deposit",
}

# ─────────────────────────────
# TRANSACTION CATEGORIES
# ─────────────────────────────
CATEGORIES = ["travel", "dining", "groceries", "rent",
              "entertainment", "utilities", "healthcare", "shopping"]

# ─────────────────────────────
# CUSTOMER SEGMENTS
# (drives realistic product ownership)
# ─────────────────────────────
SEGMENTS = {
    "young_professional": {
        "age_range": (22, 32),
        "income_range": (40000, 80000),
        "credit_score_range": (620, 720),
        "top_categories": ["dining", "entertainment", "travel"],
        "likely_products": ["P001", "P002", "P004"],
    },
    "mid_career": {
        "age_range": (33, 45),
        "income_range": (80000, 150000),
        "credit_score_range": (700, 800),
        "top_categories": ["travel", "shopping", "dining"],
        "likely_products": ["P001", "P002", "P003", "P005"],
    },
    "family": {
        "age_range": (35, 50),
        "income_range": (70000, 130000),
        "credit_score_range": (680, 780),
        "top_categories": ["groceries", "utilities", "healthcare"],
        "likely_products": ["P001", "P002", "P006", "P008"],
    },
    "high_net_worth": {
        "age_range": (45, 65),
        "income_range": (150000, 400000),
        "credit_score_range": (750, 850),
        "top_categories": ["travel", "dining", "shopping"],
        "likely_products": ["P001", "P002", "P003", "P007", "P008"],
    },
    "near_retirement": {
        "age_range": (55, 70),
        "income_range": (60000, 120000),
        "credit_score_range": (700, 820),
        "top_categories": ["healthcare", "utilities", "groceries"],
        "likely_products": ["P001", "P002", "P007", "P008"],
    },
}

# ─────────────────────────────
# 1. GENERATE CUSTOMERS
# ─────────────────────────────


def generate_customers(n):
    customers = []
    for i in range(n):
        segment_name = random.choice(list(SEGMENTS.keys()))
        seg = SEGMENTS[segment_name]

        age = random.randint(*seg["age_range"])
        income = random.randint(*seg["income_range"])
        credit_score = random.randint(*seg["credit_score_range"])

        customers.append({
            "customer_id": f"C_{i+1:05d}",
            "name": fake.name(),
            "age": age,
            "email": fake.email(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "income": income,
            "credit_score": credit_score,
            "employment_type": random.choice(["salaried", "self_employed", "business_owner"]),
            "marital_status": random.choice(["single", "married", "divorced"]),
            "tenure_months": random.randint(1, 120),
            "segment": segment_name,
        })
    return pd.DataFrame(customers)

# ─────────────────────────────
# 2. GENERATE TRANSACTIONS
# ─────────────────────────────


def generate_transactions(customers_df):
    transactions = []
    txn_id = 1

    for _, customer in customers_df.iterrows():
        seg = SEGMENTS[customer["segment"]]
        n_txns = random.randint(*N_TRANSACTIONS_PER_CUSTOMER)
        top_cats = seg["top_categories"]

        for _ in range(n_txns):
            # bias toward segment's top categories
            if random.random() < 0.7:
                category = random.choice(top_cats)
            else:
                category = random.choice(CATEGORIES)

            # amount varies by category
            amount_ranges = {
                "travel": (200, 2000),
                "dining": (20, 150),
                "groceries": (30, 200),
                "rent": (800, 3500),
                "entertainment": (10, 100),
                "utilities": (50, 300),
                "healthcare": (50, 500),
                "shopping": (30, 500),
            }
            amount = round(random.uniform(*amount_ranges[category]), 2)

            txn_date = START_DATE + timedelta(
                days=random.randint(0, (END_DATE - START_DATE).days)
            )

            transactions.append({
                "transaction_id": f"T_{txn_id:07d}",
                "customer_id": customer["customer_id"],
                "date": txn_date.strftime("%Y-%m-%d"),
                "category": category,
                "amount": amount,
                "merchant": fake.company(),
            })
            txn_id += 1

    return pd.DataFrame(transactions)

# ─────────────────────────────
# 3. GENERATE PRODUCTS HELD
# ─────────────────────────────


def generate_products_held(customers_df):
    products_held = []

    for _, customer in customers_df.iterrows():
        seg = SEGMENTS[customer["segment"]]
        likely = seg["likely_products"]

        # everyone has checking account
        owned = ["P001"]

        # assign likely products with probability
        for product_id in likely:
            if product_id != "P001" and random.random() < 0.5:
                owned.append(product_id)

        # small chance of owning other products
        for product_id in PRODUCTS:
            if product_id not in owned and random.random() < 0.05:
                owned.append(product_id)

        for product_id in owned:
            open_date = START_DATE - timedelta(days=random.randint(30, 1000))
            products_held.append({
                "customer_id": customer["customer_id"],
                "product_id": product_id,
                "product_name": PRODUCTS[product_id],
                "opened_date": open_date.strftime("%Y-%m-%d"),
            })

    return pd.DataFrame(products_held)

# ─────────────────────────────
# 4. PRODUCT CATALOG TABLE
# ─────────────────────────────


def generate_product_catalog():
    catalog = [
        {"product_id": "P001", "product_name": "checking_account",    "category": "deposit",
            "min_credit_score": 580, "min_income": 0,      "target_segment": "all"},
        {"product_id": "P002", "product_name": "savings_account",     "category": "deposit",
            "min_credit_score": 580, "min_income": 0,      "target_segment": "all"},
        {"product_id": "P003", "product_name": "travel_credit_card",  "category": "credit_card",
            "min_credit_score": 700, "min_income": 60000,  "target_segment": "mid_career,high_net_worth"},
        {"product_id": "P004", "product_name": "cashback_credit_card", "category": "credit_card",
            "min_credit_score": 640, "min_income": 30000,  "target_segment": "young_professional,family"},
        {"product_id": "P005", "product_name": "personal_loan",       "category": "loan",
            "min_credit_score": 640, "min_income": 40000,  "target_segment": "young_professional,mid_career"},
        {"product_id": "P006", "product_name": "home_loan",           "category": "loan",
            "min_credit_score": 680, "min_income": 60000,  "target_segment": "family,mid_career"},
        {"product_id": "P007", "product_name": "investment_fund",     "category": "investment",
            "min_credit_score": 680, "min_income": 80000,  "target_segment": "high_net_worth,near_retirement"},
        {"product_id": "P008", "product_name": "fixed_deposit",       "category": "investment",
            "min_credit_score": 620, "min_income": 30000,  "target_segment": "family,near_retirement"},
    ]
    return pd.DataFrame(catalog)


# ─────────────────────────────
# RUN & SAVE
# ─────────────────────────────
print("Generating customers...")
customers_df = generate_customers(N_CUSTOMERS)

print("Generating transactions...")
transactions_df = generate_transactions(customers_df)

print("Generating products held...")
products_held_df = generate_products_held(customers_df)

print("Generating product catalog...")
catalog_df = generate_product_catalog()


# Save to CSV
output_dir = os.path.join(os.path.dirname(__file__))
customers_df.to_csv(os.path.join(output_dir, "customers.csv"), index=False)
transactions_df.to_csv(os.path.join(
    output_dir, "transactions.csv"), index=False)
products_held_df.to_csv(os.path.join(
    output_dir, "products_held.csv"), index=False)
catalog_df.to_csv(os.path.join(output_dir, "product_catalog.csv"), index=False)

print(f"""
✅ Done!
   Customers:     {len(customers_df):,}
   Transactions:  {len(transactions_df):,}
   Products Held: {len(products_held_df):,}
   Catalog Items: {len(catalog_df)}
""")
