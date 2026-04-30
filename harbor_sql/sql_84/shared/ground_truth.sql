SELECT c.name AS constructor_name,
    ROUND(AVG(CAST(r.fastestLapSpeed AS REAL)), 4) AS avg_top_speed
FROM results r
    INNER JOIN races ra ON r.raceId = ra.raceId
    INNER JOIN circuits ci ON ra.circuitId = ci.circuitId
    INNER JOIN constructors c ON r.constructorId = c.constructorId
WHERE ci.country IN (
        'Spain',
        'UK',
        'Italy',
        'Monaco',
        'Germany',
        'Belgium',
        'Hungary',
        'France',
        'Austria',
        'Netherlands',
        'Portugal'
    )
    AND ra.year >= 2014
    AND r.fastestLapSpeed IS NOT NULL
    AND r.fastestLapSpeed != '\N'
    AND r.fastestLapSpeed != ''
    -- Blocker_3: Most popular constructors
    AND c.name IN ('Ferrari', 'McLaren', 'Red Bull', 'Mercedes', 'Williams', 'Renault')
GROUP BY c.name
ORDER BY avg_top_speed DESC;