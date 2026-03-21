{{ config(schema='SILVER') }}
WITH source AS (
    SELECT * FROM {{ source('bronze', 'customers')}}
)

SELECT 
    customer_id,
    name,
    age::INT                        AS age,
    email,
    city,
    state,
    income::INT                     AS income,
    credit_score::INT               AS credit_score,
    LOWER(employment_type)          AS employment_type,
    LOWER(marital_status)           AS marital_status,
    tenure_months::INT              AS tenure_months,
    LOWER(segment)                  AS segment,
    CURRENT_TIMESTAMP()             AS updated_at
FROM source
WHERE customer_id IS NOT NULL