-- Dimension: SDG Goals
-- The 17 Sustainable Development Goals

SELECT
    goal_code,
    goal_title,
    goal_description,
    -- Add goal category for grouping
    CASE 
        WHEN goal_code IN ('1', '2', '3', '4', '5', '6') THEN 'People'
        WHEN goal_code IN ('7', '8', '9', '10', '11', '12') THEN 'Prosperity'
        WHEN goal_code IN ('13', '14', '15') THEN 'Planet'
        WHEN goal_code IN ('16', '17') THEN 'Peace & Partnership'
        ELSE 'Other'
    END AS goal_category
FROM {{ ref('stg_sdg_goals') }}
