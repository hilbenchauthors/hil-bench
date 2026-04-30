SELECT DISTINCT disp.type
FROM disp
JOIN account
    ON disp.account_id = account.account_id
JOIN loan
    ON account.account_id = loan.account_id
JOIN district
    ON account.district_id = district.district_id
WHERE disp.type = 'OWNER'
  AND district.Longitude > 13.88
  AND district.A13 IN ('A', 'F', 'J', 'Q')
  AND loan.status IN ('B', 'C', 'D')
  AND loan.date >= '1997-02-10'
ORDER BY disp.type DESC;