SELECT DISTINCT d.surname AS last_name,
  d.wikiUrl as main_webpage
FROM results r
JOIN races ra ON r.raceId = ra.raceId
JOIN drivers d ON r.driverId = d.driverId
WHERE ra.year = 2016
  AND r.points = 25
  AND d.driverId IN (
    SELECT results.driverId
    FROM results
    JOIN races ON results.raceId = races.raceId
    GROUP BY results.driverId
    HAVING COUNT(DISTINCT races.year) >= 5
  )
ORDER BY last_name ASC
;