SELECT Title
FROM posts p
WHERE (
        LOWER(Body) LIKE '%clustering%' 
     OR LOWER(Body) LIKE '%cluster analysis%' 
     OR LOWER(Body) LIKE '%unsupervised learning%' 
     OR LOWER(Body) LIKE '%grouping%'
      )
  AND CreatedDate >= '2014-04-01'
  AND CreatedDate <= '2014-08-31'
  AND NOT EXISTS (
        SELECT 1
        FROM postLinks pl
        WHERE pl.PostId = p.Id
           OR pl.RelatedPostId = p.Id
      )
ORDER BY ViewCount DESC
LIMIT 1;