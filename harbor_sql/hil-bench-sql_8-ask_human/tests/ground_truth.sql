WITH senior AS (
  SELECT OwnerUserId AS user_id
  FROM posts
  GROUP BY OwnerUserId
  HAVING COUNT(*) >= 100
),
verified AS (
  SELECT DISTINCT UserId AS user_id
  FROM badges
  WHERE Name = 'Custodian'
),
matching_questions AS (
  SELECT Id AS question_id
  FROM posts
  WHERE ParentId IS NULL
    AND (
      Tags LIKE '%<time-series>%'
      OR Tags LIKE '%<forecasting>%'
      OR Tags LIKE '%<arima>%'
    )
),
matching_posts_raw AS (
  SELECT p.Id AS post_id, p.OwnerUserId AS user_id
  FROM posts p
  WHERE p.Id IN (SELECT question_id FROM matching_questions)
  UNION ALL
  SELECT a.Id AS post_id, a.OwnerUserId AS user_id
  FROM posts a
  WHERE a.PostTypeId = 2
    AND a.ParentId IN (SELECT question_id FROM matching_questions)
),
matching_posts AS (
  SELECT DISTINCT post_id, user_id
  FROM matching_posts_raw
  WHERE user_id IS NOT NULL
),
bounty_per_post AS (
  SELECT PostId AS post_id, SUM(BountyAmount) AS bounty_eur
  FROM votes
  WHERE BountyAmount IS NOT NULL
  GROUP BY PostId
),
user_stats AS (
  SELECT
    mp.user_id,
    COUNT(*) AS matching_post_count,
    COALESCE(SUM(bpp.bounty_eur), 0) AS total_bounty_eur
  FROM matching_posts mp
  LEFT JOIN bounty_per_post bpp ON bpp.post_id = mp.post_id
  GROUP BY mp.user_id
)
SELECT
  u.DisplayName AS display_name,
  us.matching_post_count,
  ROUND(us.total_bounty_eur * 1.1806, 2) AS total_bounty_usd
FROM users u
JOIN senior s       ON s.user_id = u.Id
JOIN verified v     ON v.user_id = u.Id
JOIN user_stats us  ON us.user_id = u.Id
ORDER BY us.matching_post_count DESC, display_name ASC
LIMIT 10;