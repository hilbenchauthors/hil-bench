SELECT a.element
FROM atom a
INNER JOIN molecule m ON a.molecule_id = m.molecule_id
WHERE m.tier_code = 'T2'
  AND m.classification_year >= 2011
GROUP BY a.element
ORDER BY COUNT(DISTINCT a.molecule_id) ASC, a.element ASC
LIMIT 1;

