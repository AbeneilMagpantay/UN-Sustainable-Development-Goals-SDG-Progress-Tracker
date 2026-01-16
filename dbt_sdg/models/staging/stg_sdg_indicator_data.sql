-- Staging model for SDG Indicator Data
-- Clean and standardize indicator measurements

SELECT
    indicator_code,
    geo_area_code,
    geo_area_name,
    CAST(time_period AS INT64) AS year,
    SAFE_CAST(value AS FLOAT64) AS value,
    value_type,
    unit,
    source AS data_source,
    extracted_at
FROM {{ source('raw', 'sdg_indicator_data') }}
WHERE 
    value IS NOT NULL
    AND time_period IS NOT NULL
    AND SAFE_CAST(time_period AS INT64) >= 2000
