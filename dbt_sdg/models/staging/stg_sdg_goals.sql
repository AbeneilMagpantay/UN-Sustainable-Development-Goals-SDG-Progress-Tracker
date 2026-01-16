-- Staging model for SDG Goals
-- Clean and standardize the 17 Sustainable Development Goals

SELECT
    CAST(goal_code AS STRING) AS goal_code,
    goal_title,
    goal_description,
    PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', CAST(extracted_at AS STRING)) AS extracted_at
FROM {{ source('raw', 'sdg_goals') }}
