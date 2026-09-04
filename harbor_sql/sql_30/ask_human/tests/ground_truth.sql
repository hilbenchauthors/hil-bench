SELECT
  Player.player_name,
  (Team.team_info_3 || ' ' || Team.team_info_4 || ' ' || Team.team_info_2) AS team_full_name
FROM
  Player
  JOIN Match ON Player.player_api_id = Match.home_player_1
  JOIN Team ON Match.home_team_api_id = Team.team_api_id
WHERE
  strftime ('%Y', Player.birthday) BETWEEN '1980' AND '1990'
  AND strftime ('%Y', Team.last_press_conference_date) = '2025'
GROUP BY
  Player.id
ORDER BY
  (Player.height * 20 + Player.weight * 80) / 100 DESC,
  Player.player_name DESC
LIMIT
  10;