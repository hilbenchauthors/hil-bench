SELECT
    TRIM(
        COALESCE(schools.AdmFName1 || ' ' || schools.AdmLName1, '')
        || CASE 
            WHEN schools.AdmFName2 IS NOT NULL THEN '.' || schools.AdmFName2 || ' ' || schools.AdmLName2
            ELSE ''
        END
        || CASE 
            WHEN schools.AdmFName3 IS NOT NULL THEN '.' || schools.AdmFName3 || ' ' || schools.AdmLName3
            ELSE ''
        END,
        '.'
    ) AS administrators,
    schools.Zip || ': ' || schools.State || ', ' || schools.School AS legislative_name
FROM satscores
JOIN schools
    ON satscores.cds = schools.CDSCode
WHERE
    schools.Latitude > 37.7
    AND schools.StatusType IN ('3', 'J', 'S', 'T')
    AND schools.School IS NOT NULL
    AND schools.Zip IS NOT NULL
    AND schools.State IS NOT NULL
ORDER BY
    satscores.AvgScrMath DESC
LIMIT 5;