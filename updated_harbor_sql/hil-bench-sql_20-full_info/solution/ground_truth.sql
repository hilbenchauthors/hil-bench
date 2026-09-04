SELECT DISTINCT m.molecule_id
FROM molecule m
JOIN atom a ON m.molecule_id = a.molecule_id
WHERE m.label = 'SC_071'
AND a.element IN ('cl', 'br', 'f')
AND m.registration_date BETWEEN '2016-01-01' AND '2018-12-31'
ORDER BY m.molecule_id;
