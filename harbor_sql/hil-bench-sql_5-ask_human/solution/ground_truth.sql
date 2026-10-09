SELECT COUNT(DISTINCT u.Id)
FROM users u
JOIN badges b ON u.Id = b.UserId
JOIN user_status us ON u.Id = us.Id
JOIN posts p ON u.Id = p.OwnerUserId
WHERE (u.Location LIKE '%San Francisco%'
    OR u.Location LIKE '%Bay Area%'
    OR u.Location LIKE '%New York%'
    OR u.Location LIKE '%NYC%'
    OR u.Location LIKE '%Seattle%'
    OR u.Location LIKE '%Austin%'
    OR u.Location LIKE '%Boston%'
    OR u.Location LIKE '%Los Angeles%'
    OR u.Location LIKE '%Chicago%'
    OR u.Location LIKE '%Toronto%'
    OR u.Location LIKE '%Vancouver%'
    OR u.Location LIKE '%Portland%')
AND us.activity_level = 'Frequent'
AND b.Date >= '2011-01-01' AND b.Date < '2011-03-01'
AND u.Id IN (
    SELECT DISTINCT UserId 
    FROM badges 
    WHERE Name IN ('Teacher', 'Enlightened', 'Guru')
)
AND (p.Tags LIKE '%<regression>%'
    OR p.Tags LIKE '%<hypothesis-testing>%'
    OR p.Tags LIKE '%<bayesian>%'
    OR p.Tags LIKE '%<mathematical-statistics>%'
    OR p.Tags LIKE '%<statistical-significance>%');