-- Staging model for World Bank Indicators
-- Clean economic indicator data

SELECT
    indicator_code,
    indicator_name,
    country_code,
    country_name,
    year,
    value,
    extracted_at
FROM {{ source('raw', 'wb_indicators') }}
WHERE 
    value IS NOT NULL
    AND year >= 2000
