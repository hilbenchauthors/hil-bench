SELECT COUNT(*)
FROM satscores
INNER JOIN schools ON satscores.cds = schools.CDSCode
WHERE schools.Virtual = 'F' 
  AND satscores.enroll12 <= 30 
  AND schools.OpenDate >= '1990-01-01' 
  AND (CAST(satscores.NumTstTakr AS REAL) / NULLIF(satscores.enroll12, 0)) < 0.8 
  AND satscores.AvgScrMath < 550;