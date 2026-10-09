SELECT COUNT(DISTINCT c.uuid) AS count
FROM cards c
JOIN sets s ON c.setCode = s.code
JOIN tournament_registry tr ON c.uuid = tr.card_uuid
WHERE tr.cert_level = 'sanctioned'
  AND tr.play_tier = 2
  AND tr.competition_rank = 4
  AND tr.tournament_grade = 3
  AND s.releaseDate BETWEEN '2019-01-01' AND '2020-12-31'
  AND c.borderColor = 'black';