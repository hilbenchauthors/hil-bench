WITH debut AS (
    SELECT drv.driverId,
        drv.forename,
        drv.surname,
        drv.dob,
        (
            SELECT races.raceId
            FROM results
                JOIN races ON results.raceId = races.raceId
            WHERE results.driverId = drv.driverId
            ORDER BY races.date ASC
            LIMIT 1
        ) AS debutRaceId
    FROM drivers AS drv
    WHERE drv.dob IS NOT NULL
),
eligible AS (
    SELECT debut.*
    FROM debut
    WHERE debut.debutRaceId IS NOT NULL
        AND EXISTS (
            SELECT 1
            FROM pitStops AS ps
            WHERE ps.driverId = debut.driverId
                AND ps.raceId = debut.debutRaceId
                AND ps.stop_condition IN ('3', '6')
        )
),
youngest AS (
    SELECT *
    FROM eligible
    ORDER BY dob DESC
    LIMIT 1
), race_info AS (
    SELECT youngest.driverId,
        youngest.forename,
        youngest.surname,
        youngest.debutRaceId,
        races.year,
        races.name AS raceName,
        races.date,
        races.time
    FROM youngest
        JOIN races ON races.raceId = youngest.debutRaceId
),
quick_routine AS (
    SELECT COUNT(*) AS quick_routine_stops
    FROM pitStops AS ps
        JOIN race_info AS ri ON ps.raceId = ri.debutRaceId
        AND ps.driverId = ri.driverId
    WHERE ps.stop_condition IN ('3', '6')
        AND ps.milliseconds <= 26000
),
fastest_lap AS (
    SELECT lt.time AS fastestLapTime
    FROM lapTimes AS lt
        JOIN race_info AS ri ON lt.raceId = ri.debutRaceId
        AND lt.driverId = ri.driverId
    ORDER BY lt.milliseconds ASC
    LIMIT 1
)
SELECT ri.forename || ' ' || ri.surname AS driverName,
    ri.year,
    ri.raceName,
    ri.date,
    ri.time,
    qr.quick_routine_stops,
    fl.fastestLapTime
FROM race_info AS ri
    CROSS JOIN quick_routine AS qr
    CROSS JOIN fastest_lap AS fl;