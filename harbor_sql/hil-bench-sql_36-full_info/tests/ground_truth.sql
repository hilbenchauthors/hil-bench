SELECT
  cards.id,
  cards.color_id_verified
FROM cards
WHERE
  cards.setCode = (
    SELECT
      sets.code
    FROM sets
    WHERE
      sets.type = 'duel_deck'
    ORDER BY
      sets.releaseDate ASC
    LIMIT 1
  )
  AND (
    (
      cards.tcgplayerProductId IS NOT NULL
      AND TRIM(cards.tcgplayerProductId) <> ''
    )
    OR (
      cards.cardKingdomId IS NOT NULL
      AND TRIM(cards.cardKingdomId) <> ''
    )
    OR (
      cards.cardKingdomFoilId IS NOT NULL
      AND TRIM(cards.cardKingdomFoilId) <> ''
    )
    OR (
      cards.mcmId IS NOT NULL
      AND TRIM(cards.mcmId) <> ''
    )
  )
  AND cards.uuid IN (
    SELECT
      legalities.uuid
    FROM legalities
    WHERE
      legalities.status = 'Legal'
      AND legalities.format IN ('standard', 'pioneer', 'modern')
  )
ORDER BY
  cards.id DESC;