SELECT ROUND(AVG(l.ALP), 4) as avg_core_enzymatic_indicator
FROM Laboratory l
JOIN Patient p ON l.ID = p.ID
WHERE l.TP > 8.5
  AND l.ALB BETWEEN 3.5 AND 5.5
  AND p."Referral Date" BETWEEN '1991-01-01' AND '1995-12-31'
  AND l.ID IN (
    SELECT ID FROM Laboratory GROUP BY ID HAVING COUNT(*) >= 68
  );
