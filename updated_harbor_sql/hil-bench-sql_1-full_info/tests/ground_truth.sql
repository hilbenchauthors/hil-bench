WITH technical_circuits AS (
  SELECT
    r.circuitId
  FROM races r
  JOIN results res
    ON res.raceId = r.raceId
  WHERE res.fastestLapSpeed IS NOT NULL
  GROUP BY r.circuitId
  HAVING AVG(CAST(res.fastestLapSpeed AS REAL)) < 192
),
ra_competitive_index AS (
  SELECT
    r.circuitId
  FROM races r
  JOIN results res
    ON res.raceId = r.raceId
   AND res.positionOrder = 1
  GROUP BY r.circuitId
  HAVING COUNT(DISTINCT res.driverId) <= 5
),
landslide_host_circuits AS (
  SELECT DISTINCT
    r.circuitId
  FROM races r
  JOIN results res1
    ON res1.raceId = r.raceId
   AND res1.positionOrder = 1
  JOIN results res2
    ON res2.raceId = r.raceId
   AND res2.positionOrder = 2
  WHERE res1.milliseconds IS NOT NULL
    AND res2.milliseconds IS NOT NULL
    AND res1.milliseconds > 0
    AND (res2.milliseconds - res1.milliseconds) * 100.0 / res1.milliseconds > 0.35
)
SELECT DISTINCT
  c.lat,
  c.lng
FROM circuits c
JOIN circuit_performance cp
  ON cp.circuitId = c.circuitId
JOIN technical_circuits tc
  ON tc.circuitId = c.circuitId
JOIN ra_competitive_index ra
  ON ra.circuitId = c.circuitId
JOIN landslide_host_circuits lh
  ON lh.circuitId = c.circuitId
WHERE c.country IN ('UAE', 'Bahrain')
  AND LOWER(cp.driver_performance) = 'premier';
