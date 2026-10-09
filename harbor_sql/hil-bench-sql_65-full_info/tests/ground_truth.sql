SELECT 
    ROUND(
        100.0 * SUM(
            CASE 
                WHEN cards.uniqueness IN ('1', '2', 'U', 'P') THEN 1 
                ELSE 0 
            END
        ) 
        / COUNT(*), 
        2
    ) AS percentage_unique
FROM cards
WHERE cards.artist IN ('Amy Weber', 'Chris Rahn', 'Greg Staples')
AND (
    cards.name LIKE '%Dragon%' OR
    cards.name LIKE '%Colossus%' OR
    cards.name LIKE '%Cyclops%' OR
    cards.name LIKE '%Weaver%' OR
    cards.name LIKE '%Sentry%' OR
    cards.name LIKE '%Djinn%'
);