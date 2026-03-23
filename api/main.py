from utils.snowflake_connector import read_table
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import sys
import os


# ─────────────────────────────
# Initialize FastAPI
# ─────────────────────────────
app = FastAPI(
    title="Fintech Product Recommender",
    description="AI-powered banking product recommendations",
    version="1.0.0"
)

# ─────────────────────────────
# Load data from Snowflake on startup
print("Loading data from Snowflake...")

customer_features = read_table('GOLD_CUSTOMER_FEATURES')
customer_features.columns = customer_features.columns.str.lower()

product_affinity = read_table('GOLD_PRODUCT_AFFINITY')
product_affinity.columns = product_affinity.columns.str.lower()

hybrid_df = read_table('HYBRID_RECOMMENDATIONS')
hybrid_df.columns = hybrid_df.columns.str.lower()

print("✅ All data loaded from Snowflake!")
print(f"Customers: {len(customer_features):,}")
print(f"Hybrid recs: {len(hybrid_df):,}")

# ─────────────────────────────
# Product profiles for CB model
# ─────────────────────────────
PRODUCT_PROFILES = {
    'checking_account':     [0.1, 0.1, 0.2, 0.3, 0.1, 0.1, 0.05, 0.05],
    'savings_account':      [0.1, 0.1, 0.2, 0.2, 0.1, 0.1, 0.1,  0.1],
    'travel_credit_card':   [0.4, 0.2, 0.1, 0.1, 0.1, 0.05, 0.02, 0.03],
    'cashback_credit_card': [0.1, 0.2, 0.3, 0.1, 0.2, 0.05, 0.02, 0.03],
    'personal_loan':        [0.1, 0.1, 0.2, 0.3, 0.1, 0.05, 0.05, 0.1],
    'home_loan':            [0.05, 0.1, 0.2, 0.4, 0.1, 0.05, 0.05, 0.05],
    'investment_fund':      [0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,  0.1],
    'fixed_deposit':        [0.1, 0.1, 0.2, 0.1, 0.1, 0.1, 0.1,  0.2],
}

CATEGORIES = ['travel_pct', 'dining_pct', 'groceries_pct', 'rent_pct',
              'shopping_pct', 'entertainment_pct', 'healthcare_pct', 'utilities_pct']

PRODUCT_EMOJIS = {
    'checking_account': '🏦',
    'savings_account': '💰',
    'travel_credit_card': '✈️',
    'cashback_credit_card': '💳',
    'personal_loan': '💵',
    'home_loan': '🏠',
    'investment_fund': '📈',
    'fixed_deposit': '🔒'
}

# ─────────────────────────────
# Input model for new customer
# ─────────────────────────────


class CustomerProfile(BaseModel):
    age: int
    income: float
    credit_score: int
    segment: str
    travel_pct: float = 0.1
    dining_pct: float = 0.1
    groceries_pct: float = 0.2
    rent_pct: float = 0.2
    shopping_pct: float = 0.1
    entertainment_pct: float = 0.1
    healthcare_pct: float = 0.1
    utilities_pct: float = 0.1

# ─────────────────────────────
# Helper — generate reason
# ─────────────────────────────


def generate_reason(customer_row, product_name, row):
    als = row.get('als_score_norm', 0)
    cb = row.get('cb_score_norm', 0)
    affinity = row.get('affinity_score_norm', 0)

    segment = customer_row.get('segment', '')

    # Product specific reasons
    product_reasons = {
        'travel_credit_card': f"You spend {round(customer_row.get('travel_pct', 0)*100, 1)}% on travel — earn rewards on every trip!",
        'cashback_credit_card': f"You spend {round(customer_row.get('dining_pct', 0)*100, 1)}% on dining — earn cashback on purchases!",
        'home_loan': f"Based on your rent spending of {round(customer_row.get('rent_pct', 0)*100, 1)}% — consider owning instead!",
        'personal_loan': f"Customers with your credit profile frequently use personal loans for financial flexibility",
        'investment_fund': f"With your income level, growing wealth through investments is the next step",
        'savings_account': f"Building an emergency fund is recommended for your financial profile",
        'fixed_deposit': f"Secure your savings with guaranteed returns matching your risk profile",
        'checking_account': f"100% of {segment.replace('_',' ')} customers use a checking account"
    }

    # Use product specific reason if available
    if product_name in product_reasons:
        return product_reasons[product_name]

    # Fallback to signal based reason
    if cb > als and cb > affinity:
        return f"Your spending behavior closely matches this product profile"
    elif als > cb and als > affinity:
        return f"Customers with similar product ownership frequently choose this"
    else:
        affinity_row = product_affinity[
            (product_affinity['segment'] == segment) &
            (product_affinity['product_name'] == product_name)
        ]
        if len(affinity_row) > 0:
            rate = int(affinity_row['conversion_rate'].values[0] * 100)
            return f"{rate}% of {segment.replace('_', ' ')} customers own this product"
        return "Recommended based on your financial profile"

# ─────────────────────────────
# ENDPOINT 1 — Health Check
# ─────────────────────────────


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model": "hybrid",
        "total_customers": len(customer_features),
        "total_recommendations": len(hybrid_df)
    }

# ─────────────────────────────
# ENDPOINT 2 — Existing Customer
# ─────────────────────────────


@app.get("/recommend/{customer_id}")
def recommend_existing(customer_id: str):
    # Check customer exists
    customer_row = customer_features[
        customer_features['customer_id'] == customer_id
    ]
    if len(customer_row) == 0:
        raise HTTPException(
            status_code=404, detail=f"Customer {customer_id} not found")

    customer = customer_row.iloc[0].to_dict()

    # Product ownership mapping
    product_flags = {
        'has_checking': 'checking_account',
        'has_savings': 'savings_account',
        'has_travel_card': 'travel_credit_card',
        'has_cashback_card': 'cashback_credit_card',
        'has_personal_loan': 'personal_loan',
        'has_home_loan': 'home_loan',
        'has_investment': 'investment_fund',
        'has_fixed_deposit': 'fixed_deposit'
    }

    # Build owned products set
    owned_products_set = set()
    current_products = []
    for flag, name in product_flags.items():
        if customer.get(flag, 0) == 1:
            owned_products_set.add(name)
            current_products.append(
                f"{PRODUCT_EMOJIS.get(name, '')} {name.replace('_', ' ').title()}"
            )

    # Get top 3 from pre-filtered hybrid recommendations
    recs = hybrid_df[
        hybrid_df['customer_id'] == customer_id
    ].sort_values('hybrid_score', ascending=False).head(3)

    if len(recs) == 0:
        raise HTTPException(status_code=404, detail="No recommendations found")

    # Build recommendations with rank, score %, type and reason
    recommendations = []
    rank = 1
    for _, row in recs.iterrows():
        product = row['product_name']
        score = round(row['hybrid_score'] * 100, 1)

        # Determine recommendation type
        if customer.get('num_products', 0) <= 2:
            rec_type = "cross-sell"
        elif score > 50:
            rec_type = "upsell"
        else:
            rec_type = "cross-sell"

        recommendations.append({
            "rank": rank,
            "product": product.replace('_', ' ').title(),
            "emoji": PRODUCT_EMOJIS.get(product, '💼'),
            "score": score,
            "type": rec_type,
            "reason": generate_reason(customer, product, row)
        })
        rank += 1

    return {
        "customer_id": customer_id,
        "profile": {
            "age": int(customer.get('age', 0)),
            "income": f"${int(customer.get('income', 0)):,}",
            "credit_score": int(customer.get('credit_score', 0)),
            "segment": customer.get('segment', '').replace('_', ' ').title(),
            "tenure_months": int(customer.get('tenure_months', 0))
        },
        "spending": {
            "travel": f"{round(customer.get('travel_pct', 0) * 100, 1)}%",
            "dining": f"{round(customer.get('dining_pct', 0) * 100, 1)}%",
            "groceries": f"{round(customer.get('groceries_pct', 0) * 100, 1)}%",
            "rent": f"{round(customer.get('rent_pct', 0) * 100, 1)}%",
            "shopping": f"{round(customer.get('shopping_pct', 0) * 100, 1)}%"
        },
        "current_products": current_products,
        "recommendations": recommendations
    }

# ─────────────────────────────
# ENDPOINT 3 — New Customer
# ─────────────────────────────


@app.post("/recommend/profile")
def recommend_new_customer(profile: CustomerProfile):

    # Build spending vector
    spending_vector = np.array([[
        profile.travel_pct, profile.dining_pct,
        profile.groceries_pct, profile.rent_pct,
        profile.shopping_pct, profile.entertainment_pct,
        profile.healthcare_pct, profile.utilities_pct
    ]])

    # Calculate cosine similarity
    product_names = list(PRODUCT_PROFILES.keys())
    product_matrix = np.array(list(PRODUCT_PROFILES.values()))
    similarities = cosine_similarity(spending_vector, product_matrix)[0]

    # Get affinity scores for segment
    affinity_scores = {}
    segment_affinity = product_affinity[
        product_affinity['segment'] == profile.segment
    ]
    for _, row in segment_affinity.iterrows():
        affinity_scores[row['product_name']] = row['conversion_rate']

    # Combine CB + affinity
    results = []
    for i, product in enumerate(product_names):
        cb_score = similarities[i]
        aff_score = affinity_scores.get(product, 0)
        final_score = 0.7 * cb_score + 0.3 * aff_score
        results.append({
            "product_key": product,
            "product": product.replace('_', ' ').title(),
            "emoji": PRODUCT_EMOJIS.get(product, '💼'),
            "score": final_score,
        })

    # Sort and get top 3
    results = sorted(results, key=lambda x: x['score'], reverse=True)[:3]

    # Product specific reasons — intelligent per product + segment
    def get_reason(product_key, segment, profile):
        travel_pct = round(profile.travel_pct * 100, 1)
        dining_pct = round(profile.dining_pct * 100, 1)
        rent_pct = round(profile.rent_pct * 100, 1)
        income = f"${int(profile.income):,}"

        reasons = {
            'travel_credit_card': f"High travel spending ({travel_pct}%) makes this ideal for maximizing rewards and premium benefits",
            'cashback_credit_card': f"Your dining spend ({dining_pct}%) means cashback rewards add up fast every month",
            'home_loan': f"With {rent_pct}% going to rent, owning a home could be more cost-effective long term",
            'personal_loan': f"Customers with your credit profile use personal loans for smart financial flexibility",
            'investment_fund': f"Your income level ({income}) makes diversified investments key for long-term wealth growth",
            'savings_account': f"Building a 6-month emergency fund is the recommended next step for your profile",
            'fixed_deposit': f"Lock in guaranteed returns — ideal for securing a portion of your savings safely",
            'checking_account': f"A premium checking account supports high-value transactions and daily liquidity needs"
        }

        # Segment specific overrides
        if segment == 'high_net_worth':
            reasons['investment_fund'] = f"High net worth customers grow wealth through diversified investment portfolios"
            reasons['checking_account'] = f"Premium checking accounts offer exclusive benefits for high net worth clients"
            reasons['fixed_deposit'] = f"Secure high-yield fixed deposits are ideal for wealth preservation"

        elif segment == 'young_professional':
            reasons['investment_fund'] = f"Start investing early — even small amounts compound significantly over time"
            reasons['travel_credit_card'] = f"Your travel lifestyle ({travel_pct}% spending) deserves premium travel rewards"

        elif segment == 'family':
            reasons['home_loan'] = f"With {rent_pct}% going to rent, a home loan builds long-term family wealth"
            reasons['fixed_deposit'] = f"Secure your family's financial future with guaranteed fixed deposit returns"

        return reasons.get(product_key, f"Recommended based on your {segment.replace('_', ' ')} profile")

    # Determine recommendation type
    def get_type(product_key, score_pct, segment):
        if score_pct > 70:
            return "upsell" if segment == 'high_net_worth' else "cross-sell"
        return "cross-sell"

    # Build final results
    final_results = []
    for i, rec in enumerate(results):
        score_pct = round(rec['score'] * 100, 1)
        product_key = rec['product_key']
        final_results.append({
            "rank": i + 1,
            "product": rec['product'],
            "emoji": rec['emoji'],
            "score": score_pct,
            "type": get_type(product_key, score_pct, profile.segment),
            "reason": get_reason(product_key, profile.segment, profile)
        })

    return {
        "customer_type": "new",
        "profile_summary": {
            "age": profile.age,
            "income": f"${int(profile.income):,}",
            "credit_score": profile.credit_score,
            "segment": profile.segment.replace('_', ' ').title()
        },
        "recommendations": final_results
    }
