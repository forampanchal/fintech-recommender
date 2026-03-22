{{ config(schema='SILVER') }}
WITH source AS (
    SELECT * FROM {{ source('bronze', 'transactions') }}
)

SELECT
    transaction_id,
    customer_id,
    TRY_TO_DATE(date)       AS transaction_date,
    LOWER(category)         AS category,
    TRY_TO_DOUBLE(amount)   AS amount,
    merchant,
    CURRENT_TIMESTAMP()     AS updated_at
FROM source
WHERE transaction_id IS NOT NULL
AND customer_id IS NOT NULL