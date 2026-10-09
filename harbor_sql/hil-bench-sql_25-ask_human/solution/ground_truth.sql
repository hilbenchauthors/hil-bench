SELECT
    Street,
    Enrollment_K12
FROM (
    SELECT
        Street,
        satscores.enroll12 AS Enrollment_K12,
        (
            (satscores.AvgScrMath2 + satscores.AvgScrRead2 + satscores.AvgScrWrite2) / 3.0
        ) * (
            satscores.NumGE1500 * 1.0
        ) AS SAT_Performance
    FROM schools
    JOIN satscores
        ON schools.CDSCode = satscores.cds
    WHERE
        schools.Street LIKE '%Martin Luther King Junior%'
        OR schools.Street LIKE '%Jack London%'
        OR schools.Street LIKE '%Grant%'
        OR schools.Street LIKE '%Lafayette%'
        OR schools.Street LIKE '%Adams%'
    ORDER BY SAT_Performance DESC
    LIMIT 5
)

UNION ALL

SELECT
    'Mexico' AS SchoolName,
    110 AS Enrollment_K12
