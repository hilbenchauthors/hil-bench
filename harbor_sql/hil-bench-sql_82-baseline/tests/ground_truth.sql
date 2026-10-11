WITH home_standings AS (
  SELECT 
    m.home_team_api_id AS team_api_id,
    SUM(CASE 
      WHEN m.home_team_goal > m.away_team_goal THEN 3
      WHEN m.home_team_goal = m.away_team_goal THEN 1
      ELSE 0 
    END) AS points,
    SUM(m.home_team_goal) AS goals_for,
    SUM(m.away_team_goal) AS goals_against,
    SUM(m.home_team_goal) - SUM(m.away_team_goal) AS goal_difference
  FROM Match m
  WHERE m.league_id = (SELECT id FROM League WHERE name = 'England Premier League')
    AND m.season = '2015/2016'
  GROUP BY m.home_team_api_id
),
ranked_teams AS (
  SELECT 
      hs.team_api_id,
      RANK() OVER (
          ORDER BY 
              hs.points DESC,           -- primary: points
              hs.goal_difference DESC,  -- secondary: goal difference
              hs.goals_for DESC,        -- tertiary: goals scored
              t.team_long_name ASC      -- last: alphabetical
      ) AS position
  FROM home_standings hs
  JOIN Team t ON t.team_api_id = hs.team_api_id
  WHERE hs.goals_for >= 35
)
SELECT 
  t.team_long_name AS team_name,
  rt.position AS table_position
FROM ranked_teams rt
JOIN Team t ON t.team_api_id = rt.team_api_id
WHERE rt.position <= 3
ORDER BY rt.position;
