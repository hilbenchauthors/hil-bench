WITH peak_ratings AS (
SELECT p.player_name,
MAX(pa.overall_rating_3) AS peak_rating
FROM Player p
JOIN Player_Attributes pa
ON p.player_api_id = pa.player_api_id
WHERE p.player_name IN ('Aaron Lennon', 'Abdelaziz Barrada')
AND pa.overall_rating_3 IS NOT NULL
AND pa.potential IS NOT NULL
AND pa.overall_rating_3 >= pa.potential
GROUP BY p.player_name
)
SELECT player_name,
peak_rating * 10000 AS player_net_worth_usd,
20000000 AS julian_alvarez_net_worth_usd
FROM peak_ratings
WHERE peak_rating > 95