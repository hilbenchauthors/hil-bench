SELECT COUNT(DISTINCT p.ID)
FROM Patient p
JOIN Examination e ON p.ID = e.ID
WHERE
    -- Patients who were at the hospital during 1990–1993 (using First Date)
    p."First Date" BETWEEN '1990-01-01' AND '1993-12-31'

    -- Underage or close to 18 at time of examination
    AND e."Examination Date" < DATE(p.Birthday, '+18 years')
    AND e."Examination Date" >= DATE(p.Birthday, '+17 years', '+9 months')

    -- Latest examination has no thrombosis
    AND p.ID IN (
        SELECT e2.ID
        FROM Examination e2
        GROUP BY e2.ID
        HAVING MAX(e2."Examination Date") = MAX(
            CASE WHEN e2.Thrombosis = 0 THEN e2."Examination Date" END
        )
    )

    -- Severe thrombosis occurred in any exam
    AND p.ID IN (
        SELECT e3.ID
        FROM Examination e3
        WHERE e3.Thrombosis IN (1, 2)
    );