WITH competitive_cards AS (
    SELECT 
        c.id,
        c.frameEffects,
        c.setCode,
        c.variations_standard,
        c.variations_premium,
        c.variations_base
    FROM cards c
    WHERE (c.rarity = 'mythic' OR c.rarity = 'rare')
        AND c.convertedManaCost >= 4 AND c.convertedManaCost <= 5
),
cards_with_special_effects AS (
    SELECT 
        cc.id,
        cc.setCode,
        cc.variations_standard,
        cc.variations_premium,
        cc.variations_base
    FROM competitive_cards cc
    WHERE cc.frameEffects LIKE '%extendedart%' OR cc.frameEffects LIKE '%etched%'
),
cards_from_spring_1994 AS (
    SELECT 
        cse.id,
        (CAST(cse.variations_standard AS REAL) * 2 + CAST(cse.variations_premium AS REAL) * 3 + CAST(cse.variations_base AS REAL)) / 6.0 AS design_variations
    FROM cards_with_special_effects cse
    JOIN sets s ON cse.setCode = s.code
    WHERE s.releaseDate >= '1994-03-01' AND s.releaseDate < '1994-06-01'
)
SELECT 
    id
FROM cards_from_spring_1994
ORDER BY design_variations DESC
LIMIT 5;
