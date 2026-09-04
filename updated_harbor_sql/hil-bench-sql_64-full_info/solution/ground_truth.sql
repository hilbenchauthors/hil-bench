SELECT 
    AVG(s.test_taker_audited) AS avg_test_takers
FROM satscores s
JOIN schools sc
    ON s.cds = sc.CDSCode
WHERE sc.City IN (
    'Fresno',
    'Clovis',
    'Sanger',
    'Madera',
    'Reedley'
)
AND sc.OpenDate BETWEEN '1980-01-01' AND '1980-12-31'
AND s.test_taker_audited >= 182;
