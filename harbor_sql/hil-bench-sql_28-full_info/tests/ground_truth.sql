SELECT 
    u.DisplayName AS author,
    uas.reply_level AS avg_activity_percentage
FROM users u
JOIN badges b ON b.UserId = u.Id AND b.Name IN ('Custodian', 'Citizen Patrol', 'Organizer')
JOIN posts p ON p.OwnerUserId = u.Id
    AND p.CreaionDate >= '2009-01-01' AND p.CreaionDate < '2011-01-01'
    AND p.FavoriteCount >= 2
    AND LENGTH(p.Body) > 2500
JOIN user_activity_stats uas ON uas.UserId = u.Id
GROUP BY u.Id, u.DisplayName