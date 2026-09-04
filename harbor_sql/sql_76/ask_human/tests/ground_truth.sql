SELECT ROUND(100.0 * COUNT(DISTINCT CASE WHEN m.biohazard_score > 62 THEN m.molecule_id END) / COUNT(DISTINCT m.molecule_id), 2) AS percentage
FROM molecule m
JOIN (SELECT molecule_id, COUNT(atom_id) AS atom_count FROM atom GROUP BY molecule_id) a 
ON m.molecule_id = a.molecule_id
WHERE (m.description LIKE '%Halogenated%'
OR m.description LIKE '%Halogen-bearing%'
OR m.description LIKE '%Chlorinated%')
AND a.atom_count > 28;