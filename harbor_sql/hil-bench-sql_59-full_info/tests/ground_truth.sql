SELECT COUNT(DISTINCT c.bond_id) AS linkage_count
FROM connected c
JOIN bond b ON c.bond_id = b.bond_id
JOIN atom a2 ON c.atom_id2 = a2.atom_id
JOIN atom a1 ON c.atom_id = a1.atom_id
JOIN molecule m ON a1.molecule_id = m.molecule_id
WHERE c.atom_id LIKE 'TR%_19'
AND m.risk_level > 60
AND m.registration_date BETWEEN '2010-01-01' AND '2011-12-31'
AND a2.element IN ('n', 'o', 's')
AND b.bond_type = '-'
;
