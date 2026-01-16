-- Dimension: Countries
-- Combines SDG geo areas with World Bank country metadata
-- Includes manual mapping for countries with mismatched codes

WITH sdg_countries AS (
    SELECT DISTINCT
        geo_area_code,
        geo_area_name
    FROM {{ source('raw', 'sdg_geo_areas') }}
),

wb_countries AS (
    SELECT * FROM {{ ref('stg_wb_countries') }}
),

-- Fallback region/income for major countries not matched in World Bank data
major_country_defaults AS (
    SELECT country_name, region, income_level FROM UNNEST([
        STRUCT('United States of America' AS country_name, 'North America' AS region, 'High income' AS income_level),
        STRUCT('United States', 'North America', 'High income'),
        STRUCT('Canada', 'North America', 'High income'),
        STRUCT('Australia', 'East Asia & Pacific', 'High income'),
        STRUCT('New Zealand', 'East Asia & Pacific', 'High income'),
        STRUCT('Japan', 'East Asia & Pacific', 'High income'),
        STRUCT('Germany', 'Europe & Central Asia', 'High income'),
        STRUCT('France', 'Europe & Central Asia', 'High income'),
        STRUCT('United Kingdom', 'Europe & Central Asia', 'High income'),
        STRUCT('United Kingdom of Great Britain and Northern Ireland', 'Europe & Central Asia', 'High income'),
        STRUCT('Italy', 'Europe & Central Asia', 'High income'),
        STRUCT('Spain', 'Europe & Central Asia', 'High income'),
        STRUCT('China', 'East Asia & Pacific', 'Upper middle income'),
        STRUCT('India', 'South Asia', 'Lower middle income'),
        STRUCT('Brazil', 'Latin America & Caribbean', 'Upper middle income'),
        STRUCT('Mexico', 'Latin America & Caribbean', 'Upper middle income'),
        STRUCT('South Africa', 'Sub-Saharan Africa', 'Upper middle income'),
        STRUCT('Nigeria', 'Sub-Saharan Africa', 'Lower middle income'),
        STRUCT('Russian Federation', 'Europe & Central Asia', 'Upper middle income'),
        STRUCT('Indonesia', 'East Asia & Pacific', 'Upper middle income'),
        STRUCT('Philippines', 'East Asia & Pacific', 'Lower middle income'),
        STRUCT('Vietnam', 'East Asia & Pacific', 'Lower middle income'),
        STRUCT('Thailand', 'East Asia & Pacific', 'Upper middle income'),
        STRUCT('Korea, Republic of', 'East Asia & Pacific', 'High income'),
        STRUCT('Republic of Korea', 'East Asia & Pacific', 'High income')
    ])
),

combined AS (
    SELECT
        COALESCE(s.geo_area_code, w.country_code) AS country_code,
        COALESCE(s.geo_area_name, w.country_name) AS country_name,
        COALESCE(w.region, mcd.region) AS region,
        COALESCE(w.income_level, mcd.income_level) AS income_level,
        w.capital_city,
        w.longitude,
        w.latitude
    FROM sdg_countries s
    LEFT JOIN wb_countries w 
        ON s.geo_area_name = w.country_name
        OR s.geo_area_code = w.country_code
    LEFT JOIN major_country_defaults mcd 
        ON s.geo_area_name = mcd.country_name
)

SELECT
    country_code,
    country_name,
    COALESCE(region, 'Unknown') AS region,
    COALESCE(income_level, 'Unknown') AS income_level,
    capital_city,
    longitude,
    latitude
FROM combined
WHERE country_code IS NOT NULL
