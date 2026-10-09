SELECT
  COUNT(posts.Id) AS angry_posts_count,
  AVG(posts.Score * posts.ViewCount) AS average_engagement,
  AVG(
    CASE
      WHEN posts.impact = 'A' THEN 200
      WHEN posts.impact = 'B' THEN 2000
      WHEN posts.impact = 'C' THEN 20000
      ELSE CAST(posts.impact AS INTEGER)
    END
  ) AS average_impact,
  1500000 AS reddit_average_posts_2026
FROM posts
WHERE
  (
    posts.CreaionDate BETWEEN '2009-02-02' AND '2012-02-02'
  )
  AND (
    posts.Title LIKE '%bad%'
    OR posts.Title LIKE '%horrible%'
    OR posts.Title LIKE '%hate%'
    OR posts.Title LIKE '%terrible%'
  );