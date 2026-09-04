SELECT DISTINCT
    p.ID,
    p.SEX,
    p.Birthday
FROM Patient p
JOIN Laboratory l
    ON p.ID = l.ID
WHERE
    l.UN = 29
    AND (julianday(l.Date) - julianday(p.Birthday)) / 365.25 < 30
    AND (julianday(l.Date) - julianday(p."First Date")) >= 180
    AND p.ID IN (
        SELECT ID
        FROM Laboratory
        GROUP BY ID
        HAVING COUNT(*) > 1
    )
    AND l.Date >= '1994-01-01'
    AND l.Date <  '1995-01-01';
