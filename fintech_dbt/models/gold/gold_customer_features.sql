
WITH customer_base AS (
    SELECT * FROM {{ ref('silver_customers') }}
),

transaction_stats AS (
    SELECT
        customer_id,
        COUNT(*)                                    AS total_transactions,
        SUM(amount)                                 AS total_spend,
        AVG(amount)                                 AS avg_transaction,
        MAX(amount)                                 AS max_transaction,
        SUM(CASE WHEN category = 'travel'        THEN amount ELSE 0 END) AS travel_spend,
        SUM(CASE WHEN category = 'dining'        THEN amount ELSE 0 END) AS dining_spend,
        SUM(CASE WHEN category = 'groceries'     THEN amount ELSE 0 END) AS groceries_spend,
        SUM(CASE WHEN category = 'rent'          THEN amount ELSE 0 END) AS rent_spend,
        SUM(CASE WHEN category = 'shopping'      THEN amount ELSE 0 END) AS shopping_spend,
        SUM(CASE WHEN category = 'entertainment' THEN amount ELSE 0 END) AS entertainment_spend,
        SUM(CASE WHEN category = 'healthcare'    THEN amount ELSE 0 END) AS healthcare_spend,
        SUM(CASE WHEN category = 'utilities'     THEN amount ELSE 0 END) AS utilities_spend
    FROM {{ ref('silver_transactions') }}
    GROUP BY customer_id
),

product_flags AS (
    SELECT
        customer_id,
        COUNT(DISTINCT product_id)                                                    AS num_products,
        MAX(CASE WHEN product_name = 'checking_account'     THEN 1 ELSE 0 END)       AS has_checking,
        MAX(CASE WHEN product_name = 'savings_account'      THEN 1 ELSE 0 END)       AS has_savings,
        MAX(CASE WHEN product_name = 'travel_credit_card'   THEN 1 ELSE 0 END)       AS has_travel_card,
        MAX(CASE WHEN product_name = 'cashback_credit_card' THEN 1 ELSE 0 END)       AS has_cashback_card,
        MAX(CASE WHEN product_name = 'personal_loan'        THEN 1 ELSE 0 END)       AS has_personal_loan,
        MAX(CASE WHEN product_name = 'home_loan'            THEN 1 ELSE 0 END)       AS has_home_loan,
        MAX(CASE WHEN product_name = 'investment_fund'      THEN 1 ELSE 0 END)       AS has_investment,
        MAX(CASE WHEN product_name = 'fixed_deposit'        THEN 1 ELSE 0 END)       AS has_fixed_deposit
    FROM {{ ref('silver_products_held') }}
    GROUP BY customer_id
)

SELECT
    c.customer_id,
    c.age,
    c.income,
    c.credit_score,
    c.tenure_months,
    c.segment,
    c.employment_type,
    c.marital_status,

    -- Transaction features
    t.total_transactions,
    ROUND(t.total_spend, 2)                                         AS total_spend,
    ROUND(t.avg_transaction, 2)                                     AS avg_transaction,
    ROUND(t.max_transaction, 2)                                     AS max_transaction,

    -- Spending percentages
    ROUND(t.travel_spend / NULLIF(t.total_spend, 0), 3)            AS travel_pct,
    ROUND(t.dining_spend / NULLIF(t.total_spend, 0), 3)            AS dining_pct,
    ROUND(t.groceries_spend / NULLIF(t.total_spend, 0), 3)         AS groceries_pct,
    ROUND(t.rent_spend / NULLIF(t.total_spend, 0), 3)              AS rent_pct,
    ROUND(t.shopping_spend / NULLIF(t.total_spend, 0), 3)          AS shopping_pct,
    ROUND(t.entertainment_spend / NULLIF(t.total_spend, 0), 3)     AS entertainment_pct,
    ROUND(t.healthcare_spend / NULLIF(t.total_spend, 0), 3)        AS healthcare_pct,
    ROUND(t.utilities_spend / NULLIF(t.total_spend, 0), 3)         AS utilities_pct,

    -- Product ownership flags
    p.num_products,
    p.has_checking,
    p.has_savings,
    p.has_travel_card,
    p.has_cashback_card,
    p.has_personal_loan,
    p.has_home_loan,
    p.has_investment,
    p.has_fixed_deposit,

    CURRENT_TIMESTAMP()                                             AS updated_at

FROM customer_base c
LEFT JOIN transaction_stats t ON c.customer_id = t.customer_id
LEFT JOIN product_flags p ON c.customer_id = p.customer_id