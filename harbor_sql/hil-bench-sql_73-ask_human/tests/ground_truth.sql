SELECT 
    COUNT(*) AS match_count,
    ROUND(SUM(m.home_team_goal) * 100.0 / (SUM(m.home_team_goal) + SUM(m.away_team_goal)), 1) AS home_dominance_ratio
FROM Match m
JOIN Team t1 ON m.home_team_api_id = t1.team_api_id
JOIN Team t2 ON m.away_team_api_id = t2.team_api_id
JOIN Team_Attributes ta ON t1.team_api_id = ta.team_api_id
WHERE m.league_id = 1 
AND m.season = '2008/2009'
AND SUBSTR(m.date, 6, 2) IN ('03', '04', '05')
AND (m.home_team_goal + m.away_team_goal) >= 4
AND m.B365H < m.B365A
AND ta.defenceAggressionClass = 'Double'
AND t1.team_long_name IN (
    'Club Brugge KV', 'RSC Anderlecht', 'KAA Gent', 'KRC Genk', 
    'Standard de Liège', 'Sporting Charleroi', 'KV Mechelen', 
    'SV Zulte-Waregem', 'KVC Westerlo', 'KSV Cercle Brugge', 
    'Oud-Heverlee Leuven', 'Sint-Truidense VV', 'FCV Dender EH'
)
AND t2.team_long_name IN (
    'Club Brugge KV', 'RSC Anderlecht', 'KAA Gent', 'KRC Genk', 
    'Standard de Liège', 'Sporting Charleroi', 'KV Mechelen', 
    'SV Zulte-Waregem', 'KVC Westerlo', 'KSV Cercle Brugge', 
    'Oud-Heverlee Leuven', 'Sint-Truidense VV', 'FCV Dender EH'
);