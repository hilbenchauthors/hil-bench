WITH
-- Normalize FRPM keys and pick most recent academic year per school
frpm_norm AS (
  SELECT
    REPLACE(CDSCode, '-', '') AS cds_norm,
    CAST(`Academic Year` AS INTEGER) AS ay,
    `Educational Option Type` AS ed_opt_type,
    `Enrollment (K-12)` AS enroll_k12
  FROM frpm
),
frpm_latest AS (
  SELECT cds_norm, MAX(ay) AS max_ay
  FROM frpm_norm
  GROUP BY cds_norm
),
frpm_latest_row AS (
  SELECT f.*
  FROM frpm_norm f
  JOIN frpm_latest l
    ON l.cds_norm = f.cds_norm
   AND l.max_ay  = f.ay
),
frpm_filtered AS (
  SELECT cds_norm
  FROM frpm_latest_row
  WHERE ed_opt_type IN (
    'Special Education School',
    'Nonpublic Special Education School',
    'District Consortia Special Education School'
  )
  AND enroll_k12 > 3000
),

-- School-level SAT rows only (rtype='S'); table treated as the latest cycle snapshot (assumed 2024)
sat_school AS (
  SELECT
    REPLACE(cds, '-', '') AS cds_norm,
    AvgScrRead
  FROM satscores
  WHERE rtype = 'S'
),

-- Normalize schools keys (handle CDSCode vs CDS_Code and hyphens)
schools_norm AS (
  SELECT
    REPLACE(COALESCE(NULLIF(CDSCode, ''), CDS_Code), '-', '') AS cds_norm,
    School AS school_name,
    Virtual,
    OpenDate
  FROM schools
)

SELECT DISTINCT
  s.school_name
FROM schools_norm s
JOIN frpm_filtered f
  ON f.cds_norm = s.cds_norm
JOIN sat_school sc
  ON sc.cds_norm = s.cds_norm
WHERE s.Virtual = 'F'
  AND s.OpenDate IS NOT NULL
  AND date(s.OpenDate) >= '2022-01-01'
  AND date(s.OpenDate) <= '2024-06-30'
  -- Blocker 3 resolution: treat the low threshold as a typo; use 450 as the intended cutoff
  AND sc.AvgScrRead < 450
ORDER BY s.school_name;
