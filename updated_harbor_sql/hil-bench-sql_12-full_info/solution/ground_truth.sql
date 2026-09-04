SELECT p.player_name, MAX(pa.Rating2) AS overall__adjusted_rating
FROM Player p
INNER JOIN Player_Attributes pa ON p.player_api_id = pa.player_api_id
INNER JOIN Match m ON (p.player_api_id IN (m.home_player_1, m.home_player_2, m.home_player_3, m.home_player_4, m.home_player_5, m.home_player_6, m.home_player_7, m.home_player_8, m.home_player_9, m.home_player_10, m.home_player_11, m.away_player_1, m.away_player_2, m.away_player_3, m.away_player_4, m.away_player_5, m.away_player_6, m.away_player_7, m.away_player_8, m.away_player_9, m.away_player_10, m.away_player_11))
INNER JOIN League l ON m.league_id = l.id
INNER JOIN Country c ON l.country_id = c.id
WHERE p.height < 173
  AND c.name IN ('Spain', 'Italy', 'France', 'Portugal')
  AND pa.volleys > 75
  AND pa.dribbling > 77
GROUP BY p.player_name
ORDER BY overall__adjusted_rating DESC;