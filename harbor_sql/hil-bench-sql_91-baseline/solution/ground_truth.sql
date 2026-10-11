SELECT DISTINCT T1.account_id 
FROM trans AS T1 
INNER JOIN account AS T2 ON T1.account_id = T2.account_id
INNER JOIN district AS D ON T2.district_id = D.district_id
INNER JOIN disp AS DP ON DP.account_id = T1.account_id
WHERE STRFTIME('%Y', T1.date) = '1998' 
AND T1.operation = 'VYBER KARTOU' 
AND (T1.amount * 0.8614) < (
    SELECT AVG(amount) * 0.8614
    FROM trans 
    WHERE STRFTIME('%Y', date) = '1998' 
    AND operation = 'VYBER KARTOU'
)
AND D.A13 > 5
AND DP.type = 'OWNER'
