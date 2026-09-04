SELECT DISTINCT s.School
FROM schools s
INNER JOIN satscores sat ON s.CDSCode = sat.cds
WHERE s.AdmEmail1 LIKE '%.k12.ca.us'
AND ((sat.AvgScrRead / 2.0) + sat.AvgScrWrite) > 750
AND s.Virtual IN ('B', 'C', 'D')
AND s.School IS NOT NULL
ORDER BY s.School
LIMIT 5
