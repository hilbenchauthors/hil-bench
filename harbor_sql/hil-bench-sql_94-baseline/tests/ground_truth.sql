WITH last_available_date AS (
  -- Last available date comes ONLY from users.LastAccessDate
  SELECT MAX(LastAccessDate) AS max_date
  FROM users
),
cutoff AS (
  SELECT DATE(max_date, '-15 days') AS cutoff_date
  FROM last_available_date
),
active_users AS (
  -- Active = LastAccessDate within 15 days before that max LastAccessDate
  SELECT u.Id AS UserId
  FROM users u
  CROSS JOIN cutoff
  WHERE u.LastAccessDate IS NOT NULL
    AND u.LastAccessDate >= cutoff_date
),
post_contribution AS (
  SELECT
    OwnerUserId AS UserId,
    SUM(
      COALESCE(AnswerCount,0) +
      COALESCE(CommentCount,0) +
      COALESCE(FavoriteCount,0)
    ) AS post_contribution_sum
  FROM posts
  WHERE OwnerUserId IS NOT NULL
  GROUP BY OwnerUserId
)
SELECT
  u.AccountId AS Id,
  u."User" AS username,
  COALESCE(pi.post_contribution_sum, 0)
  + COALESCE(u.UpVotes, 0)
  + COALESCE(u.DownVotes, 0) AS num_contribution
FROM users u
JOIN active_users au
  ON au.UserId = u.Id
LEFT JOIN post_contribution pi
  ON pi.UserId = u.Id
WHERE
  u.Age BETWEEN 14 AND 25
  AND (
    u.Reputation
    + (CAST(u.UpVotes AS REAL)
       / CASE WHEN u.DownVotes IS NULL OR u.DownVotes = 0 THEN 1 ELSE u.DownVotes END)
  ) >= 300
ORDER BY num_contribution DESC, username;
