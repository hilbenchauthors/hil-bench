SELECT 
    u.DisplayName, 
    SUM(p.ViewCount) AS TotalViews
FROM users u
JOIN posts p ON u.Id = p.OwnerUserId
WHERE u.Age BETWEEN 18 AND 21
  AND p.LasActivityDate >= '2012-07-01'
  AND (SELECT COUNT(*) FROM posts p2 WHERE p2.OwnerUserId = u.Id) >= 5
  AND (SELECT COUNT(*) FROM badges b WHERE b.UserId = u.Id) >= 5
GROUP BY u.Id, u.DisplayName
ORDER BY TotalViews DESC, u.DisplayName ASC
LIMIT 5;
