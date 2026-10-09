SELECT
    AVG(loan.apprvd_amount_provider_T) AS average_priority_loan_amount
FROM loan
JOIN account
    ON loan.account_id = account.account_id
JOIN district
    ON account.district_id = district.district_id
WHERE
    loan.status IN ('C')
    AND strftime('%Y', loan.date) = '1997'
    AND account.frequency = 'POPLATEK MESICNE'
    AND district.longitude > 12.9;