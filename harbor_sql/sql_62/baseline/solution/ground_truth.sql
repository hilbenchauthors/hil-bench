WITH last_period_rulings AS (
  SELECT r.uuid, r.date, r.text
  FROM rulings r
  WHERE r.date >= '2021-01-01' AND r.date < '2022-01-01'
)
SELECT
  c.name,
  c.layout,
  lpr.date AS ruling_date,
  lpr.text AS ruling_text
FROM cards c
JOIN last_period_rulings lpr
  ON lpr.uuid = c.uuid
WHERE c.AlternativeDeckLimitMarker IN (17, 27, 37)
  AND c.layout = 'modal_dfc'
  AND c.hasFoil = 1
  AND c.hasNonFoil = 0
ORDER BY lpr.date DESC, c.name;
