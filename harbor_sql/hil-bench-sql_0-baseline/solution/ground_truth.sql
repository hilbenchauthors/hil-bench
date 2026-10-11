SELECT DISTINCT d.A2
FROM district d
JOIN client c ON c.district_id = d.district_id
JOIN disp dp ON dp.client_id = c.client_id AND dp.type = 'OWNER'
JOIN account a ON a.account_id = dp.account_id
JOIN loan l ON l.account_id = a.account_id
JOIN trans t ON t.account_id = a.account_id
WHERE c.birth_date < '1950-01-01'
  AND t.date BETWEEN '1996-01-01' AND '1996-12-31'
  AND t.k_symbol = 'CAT7'
  AND t.service_flag = 'S1'
  AND l.status = 'R3'
  AND l.outcome_group = 'G2'
  AND d.A12 > 5.0;