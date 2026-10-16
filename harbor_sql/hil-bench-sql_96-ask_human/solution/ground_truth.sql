SELECT
  name
FROM cards
WHERE
  (
    (' ' || name || ' ') LIKE '% wolf %'
    OR (' ' || name || ' ') LIKE '% rat %'
    OR (' ' || name || ' ') LIKE '% spider %'
    OR (' ' || name || ' ') LIKE '% bear %'
    OR (' ' || name || ' ') LIKE '% beetle %'
  )
  AND layout = 'normal'
  AND originalReleaseDate IS NULL
  AND borderColor = 'black'
  AND (
    availability LIKE '%mtgo%'
    OR availability LIKE '%paper%'
  )
  AND life IS NULL
  AND CAST(power AS REAL) > 5
ORDER BY
  name DESC;