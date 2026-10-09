SELECT DISTINCT 
    c.DB_ID,
    CASE 
        WHEN c.name IN ('Alpine', 'Aston Martin', 'Williams', 'Audi', 'Cadillac', 'Ferrari', 'Haas', 'McLaren', 'Mercedes', 'Red Bull', 'Racing Bulls')
        THEN 'Yes'
        ELSE 'No'
    END AS competing_current_season
FROM constructors c
WHERE c.constructorId IN (
    -- Must have at least one collision/accident/spun off result in Singapore 2009-2015
    SELECT DISTINCT r.constructorId
    FROM results r
    INNER JOIN races ra ON r.raceId = ra.raceId
    INNER JOIN status s ON r.statusId = s.statusId
    WHERE ra.name = 'Singapore Grand Prix'
      AND ra.year BETWEEN 2009 AND 2015
      AND s.status IN ('Collision', 'Accident', 'Spun off')
  )
  AND c.constructorId IN (
    -- Constructor's average pit stop across ALL Singapore GP races < overall average
    SELECT ps_grouped.constructorId
    FROM (
        SELECT r2.constructorId, AVG(ps.milliseconds) as constructor_avg
        FROM pitStops ps
        INNER JOIN races ra2 ON ps.raceId = ra2.raceId
        INNER JOIN results r2 ON ps.raceId = r2.raceId AND ps.driverId = r2.driverId
        WHERE ra2.name = 'Singapore Grand Prix'
        GROUP BY r2.constructorId
    ) ps_grouped
    WHERE ps_grouped.constructor_avg < (
        SELECT AVG(ps2.milliseconds)
        FROM pitStops ps2
        INNER JOIN races ra3 ON ps2.raceId = ra3.raceId
        WHERE ra3.name = 'Singapore Grand Prix'
    )
  )
  AND c.constructorId IN (
    -- Constructor competed in Singapore 2009-2015
    SELECT DISTINCT r3.constructorId
    FROM results r3
    INNER JOIN races ra4 ON r3.raceId = ra4.raceId
    WHERE ra4.name = 'Singapore Grand Prix'
      AND ra4.year BETWEEN 2009 AND 2015
  )
ORDER BY c.DB_ID DESC;