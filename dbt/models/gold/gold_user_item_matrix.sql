WITH products_held AS (
    SELECT * FROM {{ ref('silver_products_held') }}
),

all_customers AS (
    SELECT DISTINCT customer_id FROM {{ ref('silver_customers') }}
)

SELECT
    c.customer_id,
    MAX(CASE WHEN p.product_name = 'checking_account'     THEN 1 ELSE 0 END) AS checking_account,
    MAX(CASE WHEN p.product_name = 'savings_account'      THEN 1 ELSE 0 END) AS savings_account,
    MAX(CASE WHEN p.product_name = 'travel_credit_card'   THEN 1 ELSE 0 END) AS travel_credit_card,
    MAX(CASE WHEN p.product_name = 'cashback_credit_card' THEN 1 ELSE 0 END) AS cashback_credit_card,
    MAX(CASE WHEN p.product_name = 'personal_loan'        THEN 1 ELSE 0 END) AS personal_loan,
    MAX(CASE WHEN p.product_name = 'home_loan'            THEN 1 ELSE 0 END) AS home_loan,
    MAX(CASE WHEN p.product_name = 'investment_fund'      THEN 1 ELSE 0 END) AS investment_fund,
    MAX(CASE WHEN p.product_name = 'fixed_deposit'        THEN 1 ELSE 0 END) AS fixed_deposit
FROM all_customers c
LEFT JOIN products_held p ON c.customer_id = p.customer_id
GROUP BY c.customer_id
ORDER BY c.customer_id