SELECT DISTINCT
  posts.Body
FROM posts
INNER JOIN users
  ON users.Id = posts.OwnerUserId
INNER JOIN badges
  ON badges.UserId = users.Id
INNER JOIN postHistory
  ON postHistory.PostId = posts.Id
WHERE
  users.Age BETWEEN 17 AND 19
  AND users.CreationDate <= '2023-07-31'
  AND badges.Name IN ('Analytical', 'Socratic', 'Enlightened')
  AND postHistory.State = 'Pending';