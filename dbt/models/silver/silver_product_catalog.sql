{{ config(schema='SILVER') }}
WITH source AS (
    SELECT * FROM {{ source('bronze', 'product_catalog') }}
)

SELECT
    product_id,
    LOWER(product_name)   AS product_name,
    LOWER(category)       AS category,
    min_credit_score::INT AS min_credit_score,
    min_income::INT       AS min_income,
    LOWER(target_segment) AS target_segment,
    CURRENT_TIMESTAMP()   AS updated_at
FROM source
WHERE product_id IS NOT NULL