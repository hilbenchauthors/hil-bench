WITH ta_2015_2016 AS (
  SELECT
    ta.team_api_id,
    ta.defenceAggressionClass,
    ta.buildUpPlaySpeedClass,
    ta.buildUpPlayDribblingClass,
    ta.date,
    ROW_NUMBER() OVER (
      PARTITION BY ta.team_api_id
      ORDER BY ta.date DESC
    ) AS rn
  FROM Team_Attributes ta
  WHERE strftime('%Y', ta.date) IN ('2015','2016')
),

measured_build_up_teams AS (
  -- one (latest) tactical snapshot per team for 2015/2016
  SELECT
    team_api_id,
    defenceAggressionClass
  FROM ta_2015_2016
  WHERE rn = 1
    AND buildUpPlaySpeedClass = 'Balanced'
    AND buildUpPlayDribblingClass = 'Little'
),

team_goal_rows AS (
  SELECT
    m.home_team_api_id AS team_api_id,
    SUM(m.home_team_goal) AS goals_scored,
    COUNT(*) AS matches_played
  FROM Match m
  WHERE m.season IN ('2012/2013','2013/2014','2014/2015','2015/2016')
  GROUP BY m.home_team_api_id

  UNION ALL

  SELECT
    m.away_team_api_id AS team_api_id,
    SUM(m.away_team_goal) AS goals_scored,
    COUNT(*) AS matches_played
  FROM Match m
  WHERE m.season IN ('2012/2013','2013/2014','2014/2015','2015/2016')
  GROUP BY m.away_team_api_id
),

team_gpm AS (
  SELECT
    team_api_id,
    (SUM(goals_scored) * 1.0) / NULLIF(SUM(matches_played), 0) AS goals_per_match
  FROM team_goal_rows
  GROUP BY team_api_id
)

SELECT DISTINCT
  t.team_long_name AS team_name,
  mb.defenceAggressionClass AS defensive_classification
FROM team_gpm g
JOIN measured_build_up_teams mb
  ON mb.team_api_id = g.team_api_id
JOIN Team t
  ON t.team_api_id = g.team_api_id
WHERE g.goals_per_match > 1.5
ORDER BY team_name;