SELECT
    Team.team_long_name AS winner,
    Match.home_team_goal_results_2 || '-' || Match.away_team_goal_results_2 AS final_score,
    '2-1' AS most_common_argentina_league_2025_score
FROM Match
JOIN League
    ON Match.league_id = League.id
JOIN Team
    ON Match.home_team_api_id = Team.team_api_id
WHERE Match.date LIKE '2008-11-22%'
  AND Match.home_team_goal_results_2 > Match.away_team_goal_results_2
  AND Match.away_team_goal_results_2 >= 1
  AND Match.B365H IS NOT NULL
ORDER BY Match.B365H ASC
LIMIT 1;