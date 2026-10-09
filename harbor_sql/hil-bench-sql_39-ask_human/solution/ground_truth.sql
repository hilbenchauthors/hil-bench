SELECT p.player_name, AVG(CAST(pa.long_passing AS REAL)) AS avg_long_passing
FROM Player_Attributes pa
JOIN Player p ON pa.player_api_id = p.player_api_id
WHERE pa.attacking_work_rate IN ('high', 'high_output')
AND (pa.vision + pa.short_passing + pa.long_passing) / 3.0 > 80
AND pa.date >= '2015-01-01' AND pa.date < '2017-01-01'
AND p.roster_tag = 'Q'
GROUP BY p.player_name
ORDER BY avg_long_passing DESC, p.player_name ASC
LIMIT 5;