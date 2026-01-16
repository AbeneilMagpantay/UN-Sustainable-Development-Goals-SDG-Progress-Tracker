-- Dimension: Time
-- Calendar dimension for time-based analysis

WITH years AS (
    SELECT DISTINCT year
    FROM {{ ref('stg_sdg_indicator_data') }}
    WHERE year IS NOT NULL
)

SELECT
    year,
    CAST(FLOOR(year / 10) * 10 AS INT64) AS decade,
    CASE 
        WHEN year < 2015 THEN 'MDG Era'
        WHEN year >= 2015 AND year <= 2030 THEN 'SDG Era'
        ELSE 'Post-SDG'
    END AS development_era,
    CASE 
        WHEN year = 2015 THEN TRUE
        ELSE FALSE
    END AS is_sdg_baseline,
    CASE 
        WHEN year = 2030 THEN TRUE
        ELSE FALSE
    END AS is_sdg_target_year
FROM years
ORDER BY year
