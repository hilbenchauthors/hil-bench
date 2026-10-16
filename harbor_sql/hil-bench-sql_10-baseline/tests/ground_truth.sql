SELECT DISTINCT c.name
FROM cards c
INNER JOIN legalities l ON c.uuid = l.uuid
INNER JOIN rulings r ON c.uuid = r.uuid
INNER JOIN market_classification mc ON c.uuid = mc.card_uuid
WHERE r.text = 'This is a triggered mana ability.'
  AND l.format = 'premodern'
  AND l.status = 'Legal'
  AND c.isReprint = 0
  AND mc.investment_tier >= 4
  AND c.frameVersion = '1993'
ORDER BY c.name DESC;

