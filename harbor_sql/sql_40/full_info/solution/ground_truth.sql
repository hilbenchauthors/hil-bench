WITH eligible_accounts AS (
    SELECT account.account_id
    FROM account
    JOIN district
        ON account.district_id = district.district_id
    WHERE account.date > '1995-12-31'
      AND district.A10 < 70
      AND district.A15 < 5000
      AND (
          SELECT COUNT(*)
          FROM loan
          WHERE loan.account_id = account.account_id
      ) >= 1
),
accounts_that_could_buy AS (
    SELECT eligible_accounts.account_id
    FROM eligible_accounts
    JOIN loan
        ON eligible_accounts.account_id = loan.account_id
    GROUP BY eligible_accounts.account_id
    HAVING SUM(loan.amount) >= 70000
)
SELECT
    ROUND(
        100.0 * (
            SELECT COUNT(*)
            FROM accounts_that_could_buy
        ) /
        (
            SELECT COUNT(*)
            FROM eligible_accounts
        ),
        2
    ) AS percentage_of_accounts_that_could_buy;