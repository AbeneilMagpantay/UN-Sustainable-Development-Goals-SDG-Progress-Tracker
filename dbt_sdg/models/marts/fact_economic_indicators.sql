-- Fact: Economic Indicators
-- World Bank economic data joined with country dimension

WITH wb_data AS (
    SELECT * FROM {{ ref('stg_wb_indicators') }}
),

countries AS (
    SELECT * FROM {{ ref('dim_countries') }}
),

-- Pivot indicators to columns
pivoted AS (
    SELECT
        w.country_code,
        w.country_name,
        w.year,
        MAX(CASE WHEN w.indicator_code = 'NY.GDP.PCAP.CD' THEN w.value END) AS gdp_per_capita,
        MAX(CASE WHEN w.indicator_code = 'SP.POP.TOTL' THEN w.value END) AS population,
        MAX(CASE WHEN w.indicator_code = 'SP.DYN.LE00.IN' THEN w.value END) AS life_expectancy,
        MAX(CASE WHEN w.indicator_code = 'SE.ADT.LITR.ZS' THEN w.value END) AS adult_literacy_rate
    FROM wb_data w
    GROUP BY 1, 2, 3
)

SELECT
    CONCAT(p.country_code, '_', CAST(p.year AS STRING)) AS economic_id,
    p.country_code,
    p.country_name,
    p.year,
    c.region,
    c.income_level,
    p.gdp_per_capita,
    p.population,
    p.life_expectancy,
    p.adult_literacy_rate
FROM pivoted p
LEFT JOIN countries c ON p.country_code = c.country_code
WHERE p.year IS NOT NULL
