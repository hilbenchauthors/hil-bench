WITH MoleculeMetrics AS (
    SELECT 
        m.molecule_id,
        m.label,
        -- 
        (SELECT COUNT(DISTINCT a.atom_id) 
         FROM atom a 
         WHERE a.molecule_id = m.molecule_id) AS atom_count,
         
        -- 
        (SELECT COUNT(DISTINCT b.bond_id) 
         FROM bond b 
         WHERE b.molecule_id = m.molecule_id AND b.bond_type = '=') AS double_bond_count,
         
        -- 
        (SELECT COUNT(DISTINCT c.atom_id) 
         FROM atom a
         JOIN connected c ON a.atom_id = c.atom_id
         WHERE a.molecule_id = m.molecule_id) AS connection_count
         
    FROM molecule m
    WHERE m.label = '+'  -- 
)
SELECT 
    molecule_id,
    label AS hazard_indicator,
    double_bond_count
FROM 
    MoleculeMetrics
WHERE 
    atom_count >= 34
    AND connection_count >= 6
    AND double_bond_count >= 11;