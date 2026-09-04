SELECT s.School, s.Phone
FROM schools s
INNER JOIN satscores sat ON s.CDSCode = sat.cds
WHERE s.OpenDate BETWEEN '2000-01-01' AND '2004-12-31'
  AND s.StatusType = '1'
  AND sat.AvgScrRead IS NOT NULL
ORDER BY sat.AvgScrRead ASC
LIMIT 5;