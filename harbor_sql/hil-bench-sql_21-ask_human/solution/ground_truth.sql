WITH coastal_teams AS (
    SELECT team_api_id
    FROM Team
    WHERE team_long_name IN (
        'Portsmouth',
        'Plymouth Argyle',
        'Southampton',
        'Liverpool',
        'Manchester City',
        'Manchester United',
        'Brighton & Hove Albion'
    )
),
coastal_players AS (
    SELECT DISTINCT player_api_id
    FROM (
        SELECT home_player_1  AS player_api_id, home_team_api_id AS team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT home_player_2,  home_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT home_player_3,  home_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT home_player_4,  home_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT home_player_5,  home_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT home_player_6,  home_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT home_player_7,  home_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT home_player_8,  home_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT home_player_9,  home_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT home_player_10, home_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT home_player_11, home_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT away_player_1,  away_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT away_player_2,  away_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT away_player_3,  away_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT away_player_4,  away_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT away_player_5,  away_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT away_player_6,  away_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT away_player_7,  away_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT away_player_8,  away_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT away_player_9,  away_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT away_player_10, away_team_api_id FROM Match WHERE league_id = 1729 UNION ALL
        SELECT away_player_11, away_team_api_id FROM Match WHERE league_id = 1729
    ) match_players
    JOIN coastal_teams ct ON match_players.team_api_id = ct.team_api_id
    WHERE match_players.player_api_id IS NOT NULL
)
SELECT AVG(pa.agility) AS avg_agility
FROM coastal_players cp
JOIN Player p             ON p.player_api_id  = cp.player_api_id
JOIN Player_Attributes pa ON pa.player_api_id = p.player_api_id
WHERE p.favorite_language = 'E'
  AND p.height < 173
  AND STRFTIME('%Y', pa.date) = '2014'
  AND pa.agility IS NOT NULL;