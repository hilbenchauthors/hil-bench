WITH r_question_posters AS (
  SELECT DISTINCT p.OwnerUserId
  FROM posts p
  WHERE p.PostTypeId = 1
    AND p.Tags LIKE '%<r>%'
    AND date(p.CreaionDate) > date('2009-10-26')
),
user_total_bounty AS (
  SELECT
    u.Id AS user_id,
    u.DisplayName AS elite_contributor_display_name,
    SUM(v.BountyAmount) AS total_bounty_amount
  FROM users u
  JOIN posts p ON p.OwnerUserId = u.Id
  JOIN votes v ON v.PostId = p.Id
  WHERE u.Id IN (SELECT OwnerUserId FROM r_question_posters)
    AND u.Reputation > 5000
    AND date(u.LastAccessDate) >= date('2014-09-14', '-12 months')
    AND date(u.CreationDate) <= date('2014-09-14', '-3 months')
    AND u.Honor IN ('Mx', 'Tr')
  GROUP BY u.Id, u.DisplayName
)
SELECT DISTINCT elite_contributor_display_name
FROM user_total_bounty
WHERE total_bounty_amount > 500
ORDER BY elite_contributor_display_name;