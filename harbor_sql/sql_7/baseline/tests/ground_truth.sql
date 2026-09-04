SELECT
    t.account_id,
    ROUND(AVG(t.balance) * 0.78, 2) AS avg_balance_eur
FROM trans t
JOIN account a ON t.account_id = a.account_id
JOIN district d ON a.district_id = d.district_id
WHERE d.A9 > 6
GROUP BY t.account_id
HAVING AVG(t.balance) > 50000 AND COUNT(*) > 250
ORDER BY t.account_id;
