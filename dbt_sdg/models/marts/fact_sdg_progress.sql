-- Fact: SDG Progress
-- Main fact table combining SDG indicator data with country and goal dimensions

WITH indicator_data AS (
    SELECT * FROM {{ ref('stg_sdg_indicator_data') }}
),

countries AS (
    SELECT * FROM {{ ref('dim_countries') }}
),

-- Aggregate by country, year, and goal
goal_level_data AS (
    SELECT
        geo_area_code AS country_code,
        geo_area_name AS country_name,
        SPLIT(indicator_code, '.')[OFFSET(0)] AS goal_code,
        year,
        COUNT(DISTINCT indicator_code) AS indicators_measured,
        AVG(value) AS avg_indicator_value,
        MIN(value) AS min_indicator_value,
        MAX(value) AS max_indicator_value
    FROM indicator_data
    GROUP BY 1, 2, 3, 4
)

SELECT
    -- Surrogate key
    CONCAT(g.country_code, '_', g.goal_code, '_', CAST(g.year AS STRING)) AS progress_id,
    
    -- Dimensions
    g.country_code,
    g.country_name,
    g.goal_code,
    g.year,
    
    -- Country attributes (from dimension)
    c.region,
    c.income_level,
    
    -- Metrics
    g.indicators_measured,
    g.avg_indicator_value,
    g.min_indicator_value,
    g.max_indicator_value,
    
    -- Calculate year-over-year change
    LAG(g.avg_indicator_value) OVER (
        PARTITION BY g.country_code, g.goal_code 
        ORDER BY g.year
    ) AS prev_year_avg,
    
    g.avg_indicator_value - LAG(g.avg_indicator_value) OVER (
        PARTITION BY g.country_code, g.goal_code 
        ORDER BY g.year
    ) AS yoy_change

FROM goal_level_data g
LEFT JOIN countries c ON g.country_code = c.country_code
WHERE g.year IS NOT NULL
