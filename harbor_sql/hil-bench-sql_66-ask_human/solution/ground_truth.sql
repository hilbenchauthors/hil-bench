WITH molecule_atoms AS (
    SELECT molecule_id, COUNT(*) AS atom_count
    FROM atom
    GROUP BY molecule_id
),
molecule_bonds AS (
    SELECT
        molecule_id,
        COUNT(DISTINCT bond_id) AS total_bonds,
        SUM(CASE WHEN bond_type = '-' THEN 1 ELSE 0 END) AS single_bonds,
        COUNT(DISTINCT bond_type) AS bond_diversity,
        CAST(SUM(CASE WHEN bond_type = '-' THEN 1 ELSE 0 END) AS REAL) / COUNT(DISTINCT bond_id) AS single_ratio
    FROM bond
    GROUP BY molecule_id
),
base_set AS (
    SELECT
        m.molecule_id,
        b.total_bonds,
        b.bond_diversity
    FROM molecule m
    JOIN molecule_atoms a ON m.molecule_id = a.molecule_id
    JOIN molecule_bonds b ON m.molecule_id = b.molecule_id
    WHERE m.label IN ('C7','M2','Q9')
      AND a.atom_count > 20
      AND b.single_ratio >= 0.80
)
SELECT ROUND(
    100.0 * SUM(CASE WHEN bond_diversity >= 2 THEN total_bonds ELSE 0 END) / SUM(total_bonds),
    3
) AS assessment_prevalence_rate
FROM base_set;