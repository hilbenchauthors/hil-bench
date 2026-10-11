WITH

front_runner_roster AS (
  SELECT constructorId
  FROM constructors
  WHERE constructorRef IN (
    'mclaren',
    'williams',
    'renault',
    'ferrari',
    'red_bull',
    'jordan',
    'footwork'
  )
),

opener_circuits AS (
  SELECT circuitId, COUNT(*) AS opener_cnt
  FROM races
  WHERE round = 1
  GROUP BY circuitId
),
premier_circuits AS (
  SELECT circuitId
  FROM opener_circuits
  WHERE opener_cnt >= 5
),
constructors_in_premier AS (
  SELECT res.constructorId
  FROM results res
  JOIN races r ON r.raceId = res.raceId
  WHERE r.circuitId IN (SELECT circuitId FROM premier_circuits)
  GROUP BY res.constructorId
  HAVING COUNT(DISTINCT r.circuitId) >= 3
),

eligible_attrition AS (
  SELECT constructorId
  FROM results
  GROUP BY constructorId
  HAVING COUNT(*) >= 100
),
attrition_rates AS (
  SELECT
    res.constructorId,
    SUM(
      CASE
        WHEN st.status = 'Finished' THEN 0
        WHEN st.status LIKE '+% Lap' OR st.status LIKE '+% Laps' THEN 0
        ELSE 1
      END
    ) * 1.0 / COUNT(*) AS attrition_rate
  FROM results res
  JOIN status st ON st.statusId = res.statusId
  WHERE res.constructorId IN (SELECT constructorId FROM eligible_attrition)
  GROUP BY res.constructorId
),
attrition_ranked AS (
  SELECT
    ar.constructorId,
    ar.attrition_rate,
    ROW_NUMBER() OVER (ORDER BY ar.attrition_rate ASC, ar.constructorId ASC) AS rn,
    COUNT(*) OVER () AS n
  FROM attrition_rates ar
),
attrition_median AS (
  SELECT attrition_rate AS median_rate
  FROM attrition_ranked
  WHERE rn = ((n + 1) / 2)
  LIMIT 1
),
attrition_pattern_constructors AS (
  SELECT ar.constructorId
  FROM attrition_ranked ar
  CROSS JOIN attrition_median m
  WHERE ar.attrition_rate <= m.median_rate
),

qual_score AS (
  SELECT
    q.constructorId,
    SUM(CASE WHEN q.position IS NOT NULL AND q.position <= 3 THEN 1 ELSE 0 END) * 1.0
      / COUNT(*) AS dominance_score,
    COUNT(*) AS n_q
  FROM qualifying q
  GROUP BY q.constructorId
  HAVING COUNT(*) >= 40
),
qual_ranked AS (
  SELECT
    qs.constructorId,
    qs.dominance_score,
    ROW_NUMBER() OVER (ORDER BY qs.dominance_score ASC, qs.constructorId ASC) AS rn,
    COUNT(*) OVER () AS n
  FROM qual_score qs
),
qual_q3 AS (
  SELECT dominance_score AS q3_score
  FROM qual_ranked
  WHERE rn = ((3 * n + 3) / 4)
  LIMIT 1
),
qual_dominant_constructors AS (
  SELECT qr.constructorId
  FROM qual_ranked qr
  CROSS JOIN qual_q3 q
  WHERE qr.dominance_score >= q.q3_score
),

visibility_counts AS (
  SELECT c.visibility_code, COUNT(*) AS cnt
  FROM constructors c
  WHERE c.visibility_code IS NOT NULL AND TRIM(c.visibility_code) <> ''
  GROUP BY c.visibility_code
),
visibility_max AS (
  SELECT MAX(cnt) AS mx_cnt
  FROM visibility_counts
),
top_visibility_codes AS (
  SELECT vc.visibility_code
  FROM visibility_counts vc
  CROSS JOIN visibility_max m
  WHERE vc.cnt = m.mx_cnt
),
visibility_eligible_constructors AS (
  SELECT c.constructorId
  FROM constructors c
  WHERE c.visibility_code IN (SELECT visibility_code FROM top_visibility_codes)
)

SELECT DISTINCT c.constructorId
FROM constructors c
JOIN front_runner_roster fr                 ON fr.constructorId = c.constructorId
JOIN constructors_in_premier cp             ON cp.constructorId = c.constructorId
JOIN attrition_pattern_constructors ap      ON ap.constructorId = c.constructorId
JOIN qual_dominant_constructors qd          ON qd.constructorId = c.constructorId
JOIN visibility_eligible_constructors ve    ON ve.constructorId = c.constructorId
ORDER BY c.constructorId ASC;