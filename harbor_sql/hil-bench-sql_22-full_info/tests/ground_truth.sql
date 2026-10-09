WITH active_users AS (
    SELECT UserId, COUNT(*) AS action_count
    FROM postHistory
    WHERE UserId IS NOT NULL AND UserId > 0
    GROUP BY UserId
),
top_active AS (
    SELECT au.UserId, au.action_count
    FROM active_users au
    JOIN users u ON u.Id = au.UserId
    WHERE u.LastAccessDate >= '2014-08-25 00:00:00.0'
      AND u.LastAccessDate <= '2014-09-07 23:59:59.0'
    ORDER BY au.action_count DESC
    LIMIT 5
),
post_comment_counts AS (
    SELECT p.OwnerUserId AS UserId,
           p.Id AS PostId,
           COALESCE(p.VerifiedCommentCount, 0) AS comment_count
    FROM posts p
),
ranked_posts AS (
    SELECT t.UserId,
           t.action_count,
           pc.PostId,
           pc.comment_count,
           ROW_NUMBER() OVER (
               PARTITION BY t.UserId
               ORDER BY pc.comment_count DESC, pc.PostId
           ) AS rn
    FROM top_active t
    JOIN post_comment_counts pc
         ON pc.UserId = t.UserId
)
SELECT UserId, PostId
FROM ranked_posts
WHERE rn = 1
ORDER BY action_count DESC;