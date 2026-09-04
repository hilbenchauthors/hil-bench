SELECT 
  100.0 * SUM(CASE WHEN c.rarity IN ('rare', 'mythic') THEN 1 ELSE 0 END)
  / NULLIF(COUNT(DISTINCT c.uuid), 0) AS percentage
FROM cards c
JOIN sets s ON c.setCode = s.code
JOIN legalities l ON c.uuid = l.uuid
WHERE s.code = '9ED'
  AND s.certification_status = 'CS2'
  AND c.edhrecRank <= 5000
  AND l.format = 'commander'
  AND l.status = 'Legal';