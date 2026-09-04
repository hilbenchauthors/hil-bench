SELECT
    100.0 * COUNT(DISTINCT t.ID) / COUNT(DISTINCT b.ID) AS percentage_value
FROM
    (
        SELECT DISTINCT
            p.ID
        FROM Patient p
        JOIN Examination e
            ON e.ID = p.ID
        WHERE
            p.Admission_2 = '-'
            AND (
                COALESCE(e.antibody_2, 0) > 0
                OR COALESCE(e.antibody_3, 0) > 0
            )
            AND e.Symptoms = 'pain in leg'
    ) b
LEFT JOIN Examination t
    ON t.ID = b.ID
   AND t.Thrombosis = 'K';

