WITH best_races AS (
    SELECT r.circuitId, r.profit_margin_percentage
    FROM races r
    WHERE r.year IN (
        SELECT DISTINCT r2.year
        FROM driverStandings ds
        JOIN races r2 ON ds.raceId = r2.raceId
        WHERE ds.position <= 2
            AND r2.round = (SELECT MAX(round) FROM races r3 WHERE r3.year = r2.year)
        GROUP BY r2.year
        HAVING MAX(CASE WHEN ds.position = 1 THEN ds.points END) - MAX(CASE WHEN ds.position = 2 THEN ds.points END) < 15
    )
    ORDER BY r.profit_margin_percentage DESC
    LIMIT 5
),
grade_a_circuits AS (
    SELECT circuitId
    FROM races 
    GROUP BY circuitId 
    HAVING COUNT(*) > 30
),
premium_circuits AS (
    SELECT r.circuitId
    FROM races r
    JOIN results res ON r.raceId = res.raceId
    WHERE res.fastestLapSpeed IS NOT NULL
      AND res.fastestLapSpeed != ''
    GROUP BY r.circuitId
    HAVING AVG(CAST(res.fastestLapSpeed AS REAL)) < 190
)
SELECT DISTINCT
    c.name AS circuit_name,
    CASE WHEN ga.circuitId IS NOT NULL THEN 'Yes' ELSE 'No' END AS is_grade_a_circuit,
    CASE WHEN c.operation_status IN ('Disp', '1') THEN 'Yes' ELSE 'No' END AS is_active_status,
    CASE WHEN pc.circuitId IS NOT NULL THEN 'Yes' ELSE 'No' END AS has_premium_track_classification
FROM circuits c
JOIN best_races br ON c.circuitId = br.circuitId
LEFT JOIN grade_a_circuits ga ON c.circuitId = ga.circuitId
LEFT JOIN premium_circuits pc ON c.circuitId = pc.circuitId
ORDER BY profit_margin_percentage DESC;