SELECT COUNT(DISTINCT c.client_id) 
FROM client c
INNER JOIN disp d ON c.client_id = d.client_id
INNER JOIN account a ON d.account_id = a.account_id
INNER JOIN district dist ON a.district_id = dist.district_id
INNER JOIN loan l ON a.account_id = l.account_id
INNER JOIN card cr ON d.disp_id = cr.disp_id
INNER JOIN (
    SELECT account_id, COUNT(*) as trans_count
    FROM trans
    GROUP BY account_id
    HAVING COUNT(*) > 50
) t ON a.account_id = t.account_id
WHERE cr.type = 'gold'
  AND c.birth_date > '1983-01-01'
  AND l.status = 'C'
  AND dist.A10 >= 70;
