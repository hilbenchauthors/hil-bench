SELECT s.School, 
       (sat.AvgScrRead + sat.AvgScrMath + sat.AvgScrWrite) / 3.0 AS high_academic_performance
FROM schools s
JOIN satscores sat ON s.CDSCode = sat.cds
WHERE s.County = 'Mariposa'
  AND s.Virtual = 'C'
ORDER BY s.OpenDate ASC
LIMIT 3