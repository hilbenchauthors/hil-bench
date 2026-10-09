-- Players who are clinical in front of goal (Finishing >= 83 AND Shot Power >= 80)
-- playing for Champions League teams (Napoli, Inter, Atalanta, Juventus)
-- with a disciplined playstyle (defencePressureClass = 'Medium', defenceDefenderLineClass = 'Cover',
--   buildUpPlaySpeedClass = 'Balanced', defencePressure <= 50, buildUpPlayPassing >= 45)
-- at eligible match venues (venue_ops_tier = 'K')
-- in Serie A's 2011/2012 season (128th season resolution)
-- Returns: player_name, team_long_name, venue_ops_tier

SELECT DISTINCT
    pl.player_name,
    t.team_long_name,
    m.venue_ops_tier
FROM Player pl
JOIN Player_Attributes pa
    ON pl.player_api_id = pa.player_api_id
    AND pa.date >= '2011-08-01' AND pa.date <= '2012-06-01'
    AND pa.finishing >= 83
    AND pa.shot_power >= 80
JOIN Match m
    ON m.league_id = (SELECT id FROM League WHERE name = 'Italy Serie A')
    AND m.season = '2011/2012'
    AND m.venue_ops_tier = 'K'
JOIN Team t
    ON t.team_api_id IN (m.home_team_api_id, m.away_team_api_id)
    AND t.team_long_name IN ('Napoli', 'Inter', 'Atalanta', 'Juventus')
JOIN Team_Attributes ta
    ON ta.team_api_id = t.team_api_id
    AND ta.date >= '2011-08-01' AND ta.date <= '2012-06-01'
    AND ta.defencePressureClass = 'Medium'
    AND ta.defenceDefenderLineClass = 'Cover'
    AND ta.buildUpPlaySpeedClass = 'Balanced'
    AND ta.defencePressure <= 50
    AND ta.buildUpPlayPassing >= 45
WHERE (
    (t.team_api_id = m.home_team_api_id
     AND pl.player_api_id IN (
         m.home_player_1, m.home_player_2, m.home_player_3,
         m.home_player_4, m.home_player_5, m.home_player_6,
         m.home_player_7, m.home_player_8, m.home_player_9,
         m.home_player_10, m.home_player_11))
    OR
    (t.team_api_id = m.away_team_api_id
     AND pl.player_api_id IN (
         m.away_player_1, m.away_player_2, m.away_player_3,
         m.away_player_4, m.away_player_5, m.away_player_6,
         m.away_player_7, m.away_player_8, m.away_player_9,
         m.away_player_10, m.away_player_11))
)
ORDER BY pl.player_name;

