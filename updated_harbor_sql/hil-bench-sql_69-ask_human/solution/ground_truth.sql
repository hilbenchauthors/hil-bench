WITH user_bounties AS (
SELECT
u.Id,
u.DisplayName,
u.CreationDate,
COALESCE(SUM(v.BountyAmount), 0) as TotalBountyEUR,
(COALESCE(u.DownVotes, 0) * 100.0) / (COALESCE(u.UpVotes, 0) + 1.0) as ControversyCoefficient
FROM users u
LEFT JOIN votes v ON u.Id = v.UserId AND v.VoteTypeId = 2
WHERE strftime('%Y-%m', u.CreationDate) > '2012-01'
AND u.Age >= 21
AND u.Age < 35
GROUP BY u.Id, u.DisplayName, u.CreationDate, u.UpVotes, u.DownVotes
)
SELECT
DisplayName,
ROUND(TotalBountyEUR * 1.18, 2) as TotalBountyValueUSD
FROM user_bounties
ORDER BY ControversyCoefficient DESC, CreationDate ASC
LIMIT 5;