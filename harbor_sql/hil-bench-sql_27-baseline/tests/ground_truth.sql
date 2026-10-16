WITH
target_drivers AS (
  SELECT d.driverId, d.forename, d.surname
  FROM drivers d
  WHERE d.dob IS NOT NULL
    AND CAST(STRFTIME('%Y', d.dob) AS INTEGER) BETWEEN 1980 AND 1985
),

relevant_races AS (
  SELECT ps.raceId
  FROM pitStops ps
  GROUP BY ps.raceId
  HAVING COUNT(DISTINCT ps.driverId) >= 10
),

rep_pitstops AS (
  SELECT
    ps.ROWID AS pit_rowid,
    ps.raceId,
    ps.driverId,
    ps.stop,
    CASE
      WHEN ps.duration IS NULL THEN NULL

      WHEN INSTR(ps.duration, ':') > 0 THEN
        CASE
          WHEN
            -- minutes part: only digits
            SUBSTR(ps.duration, 1, INSTR(ps.duration, ':') - 1) <> ''
            AND SUBSTR(ps.duration, 1, INSTR(ps.duration, ':') - 1) NOT GLOB '*[^0-9]*'
            -- seconds part: digits with optional single '.'
            AND SUBSTR(ps.duration, INSTR(ps.duration, ':') + 1) <> ''
            AND SUBSTR(ps.duration, INSTR(ps.duration, ':') + 1) NOT GLOB '*[^0-9.]*'
            AND SUBSTR(ps.duration, INSTR(ps.duration, ':') + 1) NOT LIKE '%.%.%'
            AND SUBSTR(ps.duration, INSTR(ps.duration, ':') + 1) <> '.'
          THEN
            60.0 * CAST(SUBSTR(ps.duration, 1, INSTR(ps.duration, ':') - 1) AS REAL)
            + CAST(SUBSTR(ps.duration, INSTR(ps.duration, ':') + 1) AS REAL)
          ELSE NULL
        END

      ELSE
        CASE
          WHEN
            ps.duration <> ''
            AND ps.duration NOT GLOB '*[^0-9.]*'
            AND ps.duration NOT LIKE '%.%.%'
            AND ps.duration <> '.'
          THEN CAST(ps.duration AS REAL)
          ELSE NULL
        END
    END AS duration_seconds
  FROM pitStops ps
  JOIN relevant_races rr
    ON rr.raceId = ps.raceId
  JOIN results r
    ON r.raceId = ps.raceId
   AND r.driverId = ps.driverId
  JOIN target_drivers td
    ON td.driverId = ps.driverId
  WHERE r.position IS NOT NULL
    AND r.milliseconds IS NOT NULL
),

race_avg AS (
  SELECT
    raceId,
    AVG(duration_seconds) AS race_avg_seconds
  FROM rep_pitstops
  WHERE duration_seconds IS NOT NULL
  GROUP BY raceId
),

picked AS (
  SELECT
    rps.raceId,
    rps.driverId,
    rps.duration_seconds,
    ROW_NUMBER() OVER (
      PARTITION BY rps.raceId, rps.driverId
      ORDER BY
        ABS(rps.duration_seconds - ra.race_avg_seconds) ASC,
        rps.stop ASC,
        rps.pit_rowid ASC
    ) AS rn
  FROM rep_pitstops rps
  JOIN race_avg ra
    ON ra.raceId = rps.raceId
  WHERE rps.duration_seconds IS NOT NULL
),

driver_avg AS (
  SELECT
    driverId,
    AVG(duration_seconds) AS avg_duration_seconds
  FROM picked
  WHERE rn = 1
  GROUP BY driverId
)

SELECT
  td.forename,
  td.surname
FROM driver_avg da
JOIN target_drivers td
  ON td.driverId = da.driverId
ORDER BY
  da.avg_duration_seconds ASC,
  td.driverId ASC
LIMIT 3;
