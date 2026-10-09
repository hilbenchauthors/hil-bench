WITH S1_FirstQuestions AS (
    SELECT *
    FROM (
        SELECT 
            u.Id AS UserId,
            p.Id AS PostId,
            p.CreaionDate AS PostDate,
            ROW_NUMBER() OVER (
                PARTITION BY u.Id 
                ORDER BY p.CreaionDate
            ) AS rn
        FROM users u
        JOIN posts p ON u.Id = p.OwnerUserId
        WHERE u.S_status = 'S_3'
          AND u.CreationDate BETWEEN '2014-01-01' AND '2014-12-31 23:59:59'
          AND p.PostTypeId = 1
    )
    WHERE rn = 1
),
SOP_Evaluation AS (
   
    SELECT 
        fq.PostId,
        CASE 
            
            WHEN MIN(r.CreaionDate) IS NULL 
                 OR (julianday(MIN(r.CreaionDate)) - julianday(fq.PostDate)) * 24 > 72 
            THEN 'Ignored (No response + Late > 72h)'
            ELSE 'Attended (SOP Compliant)'
        END AS SOP_Status
    FROM S1_FirstQuestions fq
    LEFT JOIN posts r ON fq.PostId = r.ParentId AND r.PostTypeId = 2
    GROUP BY fq.PostId
)
SELECT 
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM SOP_Evaluation), 2) AS Percentage
FROM SOP_Evaluation
WHERE SOP_Status LIKE 'Ignored%';