SELECT 
    atom.molecule_id, 
    CASE 
        WHEN molecule.tox_grade IN ('L1', 'L2', 'L3') THEN 'Yes' 
        ELSE 'No' 
    END AS "Safe"
FROM atom
JOIN molecule ON atom.molecule_id = molecule.molecule_id
GROUP BY atom.molecule_id
HAVING 
    (CAST(SUM(CASE WHEN atom.element IN ('na', 'sn', 'pb', 'zn', 'cl', 'br', 'i') THEN 1 ELSE 0 END) AS FLOAT) / 
     SUM(CASE WHEN atom.element IN ('c', 'h', 'o', 'n', 's', 'p', 'f') THEN 1 ELSE 0 END)) > 0.6
ORDER BY atom.molecule_id DESC;