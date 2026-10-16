SELECT
  cards.V1BorderColor,
  CASE
    WHEN cards.hasFoil = 0 THEN 'common'
    WHEN cards.rarity = 'common' THEN 'uncommon'
    WHEN cards.rarity = 'uncommon' THEN 'rare'
    WHEN cards.rarity = 'rare' THEN 'mythic'
    WHEN cards.rarity = 'mythic' THEN 'ultra-mythic'
    ELSE cards.rarity
  END AS full_rarity
FROM cards
JOIN sets ON cards.setCode = sets.code
WHERE
  cards.colorIndicator LIKE '%B%'
  AND (
    CAST(cards.power AS REAL) >= 5
    OR cards.power = '∞'
  )
ORDER BY
  sets.releaseDate ASC
LIMIT 10;