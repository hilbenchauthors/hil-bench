SELECT DISTINCT p.ID
FROM Patient p
INNER JOIN Laboratory l ON p.ID = l.ID
INNER JOIN Examination e ON p.ID = e.ID
WHERE 
    -- Positive CRP
    (l.CRP LIKE '%+%' OR l.CRP = 'POS')
    -- High-risk thrombosis
    AND e.Thrombosis = 1
    AND l.PT >= 14
    AND l.APTT >= 45
    -- SLE or BEHCET diagnosis
    AND (p.DX3 = 1 OR p.DX6 = 1)
ORDER BY p.ID;