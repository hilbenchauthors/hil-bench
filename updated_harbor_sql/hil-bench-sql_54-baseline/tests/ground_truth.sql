SELECT DISTINCT p.player_name
FROM Player p
INNER JOIN Player_Attributes pa ON p.player_api_id = pa.player_api_id
INNER JOIN Match m ON (
    p.player_api_id IN (
        m.home_player_1, m.home_player_2, m.home_player_3, m.home_player_4, m.home_player_5,
        m.home_player_6, m.home_player_7, m.home_player_8, m.home_player_9, m.home_player_10, m.home_player_11,
        m.away_player_1, m.away_player_2, m.away_player_3, m.away_player_4, m.away_player_5,
        m.away_player_6, m.away_player_7, m.away_player_8, m.away_player_9, m.away_player_10, m.away_player_11
    )
)
INNER JOIN League l ON m.league_id = l.id
WHERE p.height < 175
  AND pa.overall_rating <= 80
  AND pa.potential BETWEEN 82 AND 90
  AND (pa.finishing + pa.heading_accuracy + pa.volleys + pa.curve) / 4.0 > 75
  AND l.name IN ('England Premier League', 'Italy Serie A', 'Spain LIGA BBVA')
  AND p.injury_prone = 'Q3'
ORDER BY p.player_name ASC;