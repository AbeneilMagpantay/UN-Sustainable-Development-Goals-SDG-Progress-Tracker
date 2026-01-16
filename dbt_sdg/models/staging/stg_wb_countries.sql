-- Staging model for World Bank Countries
-- Clean country metadata with region and income level

SELECT
    country_code,
    country_name,
    country_code_iso3,
    region,
    income_level,
    capital_city,
    SAFE_CAST(longitude AS FLOAT64) AS longitude,
    SAFE_CAST(latitude AS FLOAT64) AS latitude,
    extracted_at
FROM {{ source('raw', 'wb_countries') }}
WHERE 
    region IS NOT NULL 
    AND region != ''
    AND country_code IS NOT NULL
