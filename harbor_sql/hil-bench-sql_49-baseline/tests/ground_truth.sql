SELECT 
    schools.CDSCode
FROM schools
JOIN frpm ON schools.CDSCode = frpm.CDSCode
JOIN satscores ON schools.CDSCode = satscores.cds
WHERE 
    frpm."High Grade" GLOB '[0-9]*' 
    AND frpm."Low Grade" GLOB '[0-9]*'
    AND ((CAST(frpm."High Grade" AS REAL) + CAST(frpm."Low Grade" AS REAL)) / 2.0) > 8

    AND (satscores.AvgScr3 = 'OOC' OR satscores.AvgScr3 > 450)

    AND (frpm."Enrollment (K-12)" + frpm."Enrollment (Ages 5-17)") > 897;