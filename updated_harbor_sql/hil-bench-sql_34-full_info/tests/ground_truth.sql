WITH TeamSeasonPerformance AS (
    SELECT 
        team_api_id,
        SUM(win_flag) AS total_wins,
        SUM(conceded) AS total_goals_received,
        -- Calculate average effective goals: (TotalHomeGoals*30 + TotalAwayGoals*70) / 100 / TotalMatches
        (CAST(SUM(home_goals_scored) * 0.3 + SUM(away_goals_scored) * 0.7 AS REAL) ) / COUNT(*) AS avg_effective_goals
    FROM (
        SELECT 
            Match.home_team_api_id AS team_api_id,
            CASE WHEN Match.home_team_goal > Match.away_team_goal THEN 1 ELSE 0 END AS win_flag,
            Match.away_team_goal AS conceded,
            Match.home_team_goal AS home_goals_scored,
            0 AS away_goals_scored
        FROM Match
        JOIN Country ON Match.country_id = Country.id
        WHERE Match.season = '2014/2015'
          AND Country.name IN ('Poland', 'Scotland', 'Switzerland', 'Netherlands', 'Germany')
        
        UNION ALL
        
        SELECT 
            Match.away_team_api_id AS team_api_id,
            CASE WHEN Match.away_team_goal > Match.home_team_goal THEN 1 ELSE 0 END AS win_flag,
            Match.home_team_goal AS conceded,
            0 AS home_goals_scored,
            Match.away_team_goal AS away_goals_scored
        FROM Match
        JOIN Country ON Match.country_id = Country.id
        WHERE Match.season = '2014/2015'
          AND Country.name IN ('Poland', 'Scotland', 'Switzerland', 'Netherlands', 'Germany')
    ) 
    GROUP BY team_api_id
)
SELECT 
    Team.team_long_name,
    Team.important_date
FROM Team
JOIN TeamSeasonPerformance ON Team.team_api_id = TeamSeasonPerformance.team_api_id
WHERE TeamSeasonPerformance.total_wins BETWEEN 10 AND 12
  AND TeamSeasonPerformance.avg_effective_goals > 0.5
ORDER BY TeamSeasonPerformance.total_goals_received ASC, Team.team_long_name DESC
LIMIT 10;