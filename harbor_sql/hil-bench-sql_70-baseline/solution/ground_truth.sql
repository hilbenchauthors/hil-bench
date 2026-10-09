SELECT DISTINCT d.A2 AS district_name
FROM account a
INNER JOIN disp dp ON a.account_id = dp.account_id
INNER JOIN client c ON dp.client_id = c.client_id
INNER JOIN district d ON a.district_id = d.district_id
WHERE c.gender = 'F'
  AND a.requested_date IN ('1997-02-01', '1997-02-02')