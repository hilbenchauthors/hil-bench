SELECT 
    d.surname,
    AVG(race_avg) AS driver_efficiency_index
FROM drivers d
JOIN (
    SELECT driverId, raceId, AVG(milliseconds) AS race_avg
    FROM lapTimes
    WHERE milliseconds IS NOT NULL
    GROUP BY driverId, raceId
) race_avgs ON d.driverId = race_avgs.driverId
WHERE d.married IN ('L', 'C', 0)
GROUP BY d.driverId, d.surname
ORDER BY (SELECT MIN(lt.milliseconds) FROM lapTimes lt WHERE lt.driverId = d.driverId) ASC
LIMIT 10