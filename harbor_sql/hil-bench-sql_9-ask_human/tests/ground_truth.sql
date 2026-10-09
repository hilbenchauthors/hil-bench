SELECT COUNT(DISTINCT c.client_id)
FROM client c
JOIN disp d ON c.client_id = d.client_id
JOIN account a ON d.account_id = a.account_id
JOIN loan l ON a.account_id = l.account_id
JOIN district dist ON c.district_id = dist.district_id
WHERE c.birth_date < '1950-01-01'
  AND a.frequency = 'POPLATEK MESICNE'
  AND l.status = 'C'
  AND l.duration = 48
  AND dist.A17 = (SELECT A17 FROM district ORDER BY A17 DESC LIMIT 4, 1);