SELECT 
    c.name,
    (c.collector_value_1 * 2 + c.collector_value_2 * 3 + c.collector_value_3) / 6.0 AS highest_collector_value
FROM cards c
JOIN sets s ON c.setCode = s.code
WHERE 
    c.convertedManaCost = 0
    AND c.types LIKE '%Artifact%'
    AND c.isReprint = 1
    AND s.releaseDate < '2010-01-01'
    AND c.isPromo = 0
    AND c.hasFoil = 1
    AND c.rarity = 'mythic'
ORDER BY highest_collector_value DESC;
