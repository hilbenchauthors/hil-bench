WITH frpm_latest AS (
  SELECT *
  FROM (
    SELECT
      f.*,
      ROW_NUMBER() OVER (
        PARTITION BY CAST(f."CDSCode" AS TEXT)
        ORDER BY f."Academic Year" DESC
      ) AS rn
    FROM frpm f
  )
  WHERE rn = 1
),
satscores_school AS (
  -- keep one SAT row per school (school-level rows)
  SELECT *
  FROM (
    SELECT
      sc.*,
      ROW_NUMBER() OVER (
        PARTITION BY sc.cds
        ORDER BY sc.rtype
      ) AS rn
    FROM satscores sc
    WHERE sc.rtype = 'S' OR sc.rtype IS NULL
  )
  WHERE rn = 1
),
base AS (
  SELECT
    s.CDSCode AS cds,
    (f."Free Meal Count (K-12)" / f."Enrollment (K-12)") * 2.4 AS cleaned_free_pct,
    sc.AvgScr3 AS sat_math,
    s.last_award_earning_date AS last_award_date
  FROM schools s
  JOIN frpm_latest f
    ON CAST(f."CDSCode" AS TEXT) = s.CDSCode
  LEFT JOIN satscores_school sc
    ON sc.cds = s.CDSCode
  WHERE
    -- Blocker 2: d1 region mapping
    s.Regions IN ('d-1', 'd01')

    -- non-chartered schools (typical encoding in this dataset)
    AND (s.Charter = '0' OR s.Charter = 0)

    -- Business info: exclude NULL/0 enrollment
    AND f."Enrollment (K-12)" IS NOT NULL
    AND f."Enrollment (K-12)" <> 0

    -- cleaned percent kept on 0–1 scale; 0.18% = 0.0018
    AND ((f."Free Meal Count (K-12)" / f."Enrollment (K-12)") * 2.4) < 0.18
)
SELECT
  COUNT(*) AS total_non_chartered_schools,
  AVG(cleaned_free_pct) AS avg_cleaned_free_pct,
  AVG(sat_math) AS avg_sat_math_score,
  SUM(
    CASE
      -- Blocker 1: last few weeks = 7-week window ending 2026-01-31 (inclusive)
      WHEN last_award_date IS NOT NULL
       AND date(last_award_date) BETWEEN date('2025-12-14') AND date('2026-01-31')
      THEN 1 ELSE 0
    END
  ) AS num_schools_with_award_last_few_weeks
FROM base;
