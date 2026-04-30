WITH prague_or_prerov_priority_owners AS (
    SELECT DISTINCT
        d.account_id
    FROM disp d
    JOIN client c
        ON c.client_id = d.client_id
    JOIN district dist
        ON dist.district_id = c.district_id
    WHERE d.type = 'OWNER'
      AND dist.A2 IN ('Hl.m. Praha', 'Prerov')
      AND c.birth_date < date('1998-12-31', '-50 years')
      AND EXISTS (
          SELECT 1
          FROM card ca
          WHERE ca.disp_id = d.disp_id
            AND ca.type = 'gold'
      )
),
eligible_accounts AS (
    SELECT a.account_id
    FROM account a
    JOIN prague_or_prerov_priority_owners ppo
        ON ppo.account_id = a.account_id
    JOIN loan l
        ON l.account_id = a.account_id
    WHERE a.frequency = 'POPLATEK MESICNE'
      AND a.date >= '1997-07-01'
      AND l.status = 'B'
),
long_term_accounts AS (
    SELECT t.account_id
    FROM trans t
    GROUP BY t.account_id
    HAVING julianday(MAX(t.date)) - julianday(MIN(t.date)) >= 365
),
filtered_accounts AS (
    SELECT ea.account_id
    FROM eligible_accounts ea
    JOIN long_term_accounts lta
        ON lta.account_id = ea.account_id
)
SELECT
    COALESCE(SUM(t.amount), 0) * 0.052416 AS total_withdrawal_usd
FROM trans t
JOIN filtered_accounts fa
    ON fa.account_id = t.account_id
WHERE t.k_symbol = 'SIPO';
