WITH ranked_loans AS (
  SELECT
    c.client_id,
    c.gender,
    l.loan_id,
    l.account_id,
    l.payments,
    l.amount,
    CAST(l.amount AS REAL) / d.A11 AS loan_risk_ratio,
    ROW_NUMBER() OVER (
      PARTITION BY c.client_id 
      ORDER BY l.payments DESC, l.amount DESC, l.loan_id DESC
    ) AS rn
  FROM loan l
  JOIN disp dp ON l.account_id = dp.account_id
  JOIN client c ON dp.client_id = c.client_id
  JOIN district d ON c.district_id = d.district_id
  WHERE l.status IN ('B', 'D')
    AND c.gender IN ('A', 'B')
    AND dp.type IN ('OWNER', 'DISPONENT')
)
SELECT
  client_id,
  loan_risk_ratio
FROM ranked_loans
WHERE rn = 1
ORDER BY payments DESC
LIMIT 20;