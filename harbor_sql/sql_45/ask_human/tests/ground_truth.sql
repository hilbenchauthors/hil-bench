WITH races_in_scope AS (
SELECT r.raceId,
r.date,
c.name AS circuit_name,
c.location,
c.lat
FROM races r
JOIN circuits c ON c.circuitId = r.circuitId
WHERE r.date BETWEEN '2008-01-01' AND '2008-06-01'
AND c.lat > 24
), winners AS (
SELECT res.raceId, res.driverId
FROM results res
JOIN races_in_scope rs ON rs.raceId = res.raceId
WHERE res.positionOrder = 1
), lap_aggs AS (
SELECT lt.raceId,
lt.driverId,
AVG(lt.milliseconds) AS avg_lap_time_ms,
SUM((lt.milliseconds * 1.0) / lt.lap * 2.0) / COUNT(*) AS balanced_avg_lap_time_ms
FROM lapTimes lt
JOIN winners w ON w.raceId = lt.raceId AND w.driverId = lt.driverId
GROUP BY lt.raceId, lt.driverId
)
SELECT rs.circuit_name,
rs.location,
CASE WHEN ltv.top = 'V' THEN 'Yes' ELSE 'No' END AS good_place_to_visit,
(d.forename || ' ' || d.surname) AS winner_name,
la.avg_lap_time_ms AS winner_avg_lap_time,
la.balanced_avg_lap_time_ms AS winner_balanced_avg_lap_time,
88792 AS verstappen_current_avg_lap_time
FROM races_in_scope rs
JOIN winners w ON w.raceId = rs.raceId
JOIN drivers d ON d.driverId = w.driverId
JOIN lap_aggs la ON la.raceId = w.raceId AND la.driverId = w.driverId
LEFT JOIN location_to_visit ltv ON ltv.name = rs.location
ORDER BY rs.circuit_name ASC;

