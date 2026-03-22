{{ config(schema='SILVER') }}
WITH source AS (
    SELECT * FROM {{ source('bronze', 'products_held') }}
)

SELECT
    customer_id,
    product_id,
    LOWER(product_name)      AS product_name,
    TRY_TO_DATE(opened_date) AS opened_date,
    CURRENT_TIMESTAMP()      AS updated_at
FROM source
WHERE customer_id IS NOT NULL