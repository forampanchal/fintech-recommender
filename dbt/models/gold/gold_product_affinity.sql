WITH customer_products AS (
    SELECT
        c.customer_id,
        c.segment,
        c.income,
        c.credit_score,
        p.product_name
    FROM {{ ref('silver_customers') }} c
    LEFT JOIN {{ ref('silver_products_held') }} p
        ON c.customer_id = p.customer_id
),

segment_totals AS (
    SELECT
        segment,
        COUNT(DISTINCT customer_id) AS total_customers
    FROM {{ ref('silver_customers') }}
    GROUP BY segment
),

segment_product_counts AS (
    SELECT
        cp.segment,
        cp.product_name,
        COUNT(DISTINCT cp.customer_id) AS customers_with_product
    FROM customer_products cp
    WHERE cp.product_name IS NOT NULL
    GROUP BY cp.segment, cp.product_name
)

SELECT
    spc.segment,
    spc.product_name,
    spc.customers_with_product,
    st.total_customers,
    ROUND(spc.customers_with_product / st.total_customers, 3) AS conversion_rate,
    RANK() OVER (
        PARTITION BY spc.segment
        ORDER BY spc.customers_with_product DESC
    ) AS rank_within_segment,
    CURRENT_TIMESTAMP() AS updated_at
FROM segment_product_counts spc
JOIN segment_totals st ON spc.segment = st.segment
ORDER BY spc.segment, conversion_rate DESC