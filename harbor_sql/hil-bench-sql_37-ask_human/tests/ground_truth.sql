WITH has_ch_bond AS (
  SELECT DISTINCT m.molecule_id
  FROM molecule m
  JOIN bond b ON b.molecule_id = m.molecule_id
  JOIN connected c ON c.bond_id = b.bond_id
  JOIN atom a1 ON a1.atom_id = c.atom_id
  JOIN atom a2 ON a2.atom_id = c.atom_id2
  WHERE (LOWER(a1.element) = 'c' AND LOWER(a2.element) = 'h')
     OR (LOWER(a2.element) = 'c' AND LOWER(a1.element) = 'h')
),
hydrocarbon_only AS (
  SELECT DISTINCT m.molecule_id
  FROM molecule m
  WHERE NOT EXISTS (
    SELECT 1 FROM atom a
    WHERE a.molecule_id = m.molecule_id
    AND LOWER(a.element) NOT IN ('c', 'h')
  )
)
SELECT COUNT(DISTINCT m.molecule_id) AS compounds_quantity
FROM molecule m
JOIN has_ch_bond ch ON ch.molecule_id = m.molecule_id
JOIN hydrocarbon_only hc ON hc.molecule_id = m.molecule_id
WHERE m.label = '+';