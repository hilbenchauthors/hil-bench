WITH locally_funded_disparities AS (
  SELECT
    s.CDSCode,
    s.School AS school_name,
    (1.0 * emc.K12_Enrollment) / emc.Ages_5_17_Enrollment AS disparity
  FROM schools s
  JOIN enrollment_metrics_certified emc
    ON emc.CDSCode = s.CDSCode
  WHERE s.FundingType = 'Locally funded'
    AND s.School IS NOT NULL
    AND emc.K12_Enrollment IS NOT NULL
    AND emc.Ages_5_17_Enrollment IS NOT NULL
    AND emc.Ages_5_17_Enrollment <> 0
),
avg_disparity AS (
  SELECT AVG(disparity) AS avg_disparity
  FROM locally_funded_disparities
),
closest_below AS (
  SELECT MAX(disparity) AS closest_below_disparity
  FROM locally_funded_disparities lfd
  CROSS JOIN avg_disparity a
  WHERE lfd.disparity < a.avg_disparity
)
SELECT lfd.school_name
FROM locally_funded_disparities lfd
CROSS JOIN avg_disparity a
CROSS JOIN closest_below cb
WHERE lfd.disparity > a.avg_disparity
   OR (
        cb.closest_below_disparity IS NOT NULL
        AND lfd.disparity = cb.closest_below_disparity
      )
ORDER BY lfd.school_name ASC;
