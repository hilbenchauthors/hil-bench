WITH frpm_one AS (
  SELECT *
  FROM (
    SELECT
      f.*,
      ROW_NUMBER() OVER (
        PARTITION BY f.CDSCode
        ORDER BY f."Academic Year" DESC, f.rowid DESC
      ) AS rn
    FROM frpm f
  )
  WHERE rn = 1
),
sat_one AS (
  SELECT *
  FROM (
    SELECT
      s.*,
      ROW_NUMBER() OVER (
        PARTITION BY s.cds
        ORDER BY s.rowid DESC
      ) AS rn
    FROM satscores s
    WHERE s.rtype = 'S'
  )
  WHERE rn = 1
),
candidates AS (
  SELECT
    sch.CDSCode,
    sch.School AS school_name,
    NULLIF(sch.code3, '') AS charter_number,
    f."Enrollment (K-12)" AS enrollment_k12,
    f."Percent (%) Eligible FRPM (Ages 5-17)" AS frpm_rate,
    sa.AvgScrMath,
    sa.AvgScrRead,
    sa.AvgScrWrite
  FROM schools sch
  JOIN frpm_one f
    ON f.CDSCode = sch.CDSCode
  JOIN sat_one sa
    ON sa.cds = sch.CDSCode
  WHERE
    sch.Latitude > 37.7
    AND f."Enrollment (Ages 5-17)" > 200
),
best AS (
  SELECT MAX(frpm_rate) AS max_frpm_rate
  FROM candidates
)
SELECT
  c.school_name,
  c.charter_number,
  (c.AvgScrMath * 50 + c.AvgScrRead * 25 + c.AvgScrWrite * 25) / 100.0
    AS corrected_sat_score,
  CASE WHEN c.enrollment_k12 < 250 THEN TRUE ELSE FALSE END
    AS has_less_than_250_total_students
FROM candidates c
CROSS JOIN best b
WHERE c.frpm_rate = b.max_frpm_rate
ORDER BY c.school_name;
