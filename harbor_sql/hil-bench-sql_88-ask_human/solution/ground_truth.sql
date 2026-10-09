SELECT DISTINCT c.name, cr.Paddock_ID
FROM constructors c
JOIN constructor_registry cr ON c.constructorId = cr.constructorId
JOIN results r_results ON c.constructorId = r_results.constructorId
JOIN races r ON r_results.raceId = r.raceId
JOIN status s ON r_results.statusId = s.statusId
JOIN lapTimes lt ON r_results.driverId = lt.driverId AND r_results.raceId = lt.raceId
WHERE r.name = 'Monaco Grand Prix'
AND r.year BETWEEN 2009 AND 2014
AND lt.position BETWEEN 12 AND 17
AND s.status NOT IN ('Engine', 'Gearbox', 'Transmission', 'Hydraulics', 'Electrical')
AND c.constructorId IN (
    SELECT constructorId
    FROM results
    WHERE position = 1
    GROUP BY constructorId
    HAVING COUNT(*) >= 5
)
ORDER BY c.name;