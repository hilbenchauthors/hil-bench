WITH base AS (
  SELECT
      cards.name,
      CAST(cards.power AS INTEGER) AS power_num
  FROM cards
  JOIN sets ON sets.code = cards.setCode
  JOIN legalities ON legalities.uuid = cards.uuid
  WHERE
      sets.releaseDate BETWEEN '2015-01-01' AND '2020-12-31'
      AND cards.frameEffects LIKE '%etched%'
      AND cards.availability = 'double'
      AND legalities.format IN ('modern', 'legacy')
      AND legalities.status = 'Legal'
      AND cards.power IS NOT NULL
      AND (
        (cards.power <> '' AND cards.power NOT GLOB '*[^0-9]*')
        OR
        (cards.power GLOB '-*'
         AND length(cards.power) > 1
         AND substr(cards.power, 2) NOT GLOB '*[^0-9]*')
      )
)
SELECT name
FROM base
GROUP BY name
ORDER BY MAX(power_num) DESC, name DESC
LIMIT 10;