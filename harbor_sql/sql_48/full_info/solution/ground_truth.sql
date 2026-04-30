WITH early_sets_list AS (
    SELECT code
    FROM sets
    ORDER BY releaseDate
    LIMIT 13
),
late_sets_list AS (
    SELECT code
    FROM sets
    ORDER BY releaseDate DESC
    LIMIT 7
),
cards_with_metrics AS (
    SELECT 
        c.setCode,
        -- Convert power to numeric following blocker resolution
        CASE 
            WHEN c.power = 'A' THEN 1.0
            WHEN c.power = 'J' THEN 2.0
            WHEN c.power = 'S' THEN 3.0
            WHEN c.power LIKE '%+*' THEN CAST(REPLACE(c.power, '+*', '') AS REAL) + 1
            WHEN c.power IS NOT NULL THEN CAST(c.power AS REAL)
            ELSE NULL
        END AS converted_power,
        -- Balanced mana cost: sum of weighted color symbols (W=1, U=1, B=1.5, R=1, G=1)
        (LENGTH(c.manaCost) - LENGTH(REPLACE(c.manaCost, '{W}', ''))) / 3.0 * 1.0 +
        (LENGTH(c.manaCost) - LENGTH(REPLACE(c.manaCost, '{U}', ''))) / 3.0 * 1.0 +
        (LENGTH(c.manaCost) - LENGTH(REPLACE(c.manaCost, '{B}', ''))) / 3.0 * 1.5 +
        (LENGTH(c.manaCost) - LENGTH(REPLACE(c.manaCost, '{R}', ''))) / 3.0 * 1.0 +
        (LENGTH(c.manaCost) - LENGTH(REPLACE(c.manaCost, '{G}', ''))) / 3.0 * 1.0 AS balanced_mana_cost
    FROM cards c
),
early_sets_stats AS (
    SELECT 
        'early_sets' AS period,
        AVG(converted_power) AS avg_power,
        AVG(balanced_mana_cost) AS avg_balanced_mana_cost
    FROM cards_with_metrics
    WHERE setCode IN (SELECT code FROM early_sets_list)
),
late_sets_stats AS (
    SELECT 
        'late_sets' AS period,
        AVG(converted_power) AS avg_power,
        AVG(balanced_mana_cost) AS avg_balanced_mana_cost
    FROM cards_with_metrics
    WHERE setCode IN (SELECT code FROM late_sets_list)
)
SELECT period, avg_power, avg_balanced_mana_cost
FROM early_sets_stats
UNION ALL
SELECT period, avg_power, avg_balanced_mana_cost
FROM late_sets_stats;
