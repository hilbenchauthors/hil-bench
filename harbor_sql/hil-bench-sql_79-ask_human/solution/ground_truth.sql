SELECT
  c.name,
  SUM(COALESCE(cr.verified_logs, 0) + (cr.logs / 2.0)) AS verified_points
FROM constructorResults AS cr
JOIN constructors AS c ON cr.constructorId = c.constructorId
JOIN races AS r ON cr.raceId = r.raceId
JOIN circuits AS circ ON r.circuitId = circ.circuitId
WHERE
  r.year = 2017
  AND circ.circuitRef IN ('monaco', 'silverstone', 'spa', 'monza', 'suzuka')
  AND r.raceId IN (
    SELECT DISTINCT raceId
    FROM pitStops
    WHERE milliseconds BETWEEN 18250 AND 24890
  )
GROUP BY
  c.name
ORDER BY
  verified_points DESC;