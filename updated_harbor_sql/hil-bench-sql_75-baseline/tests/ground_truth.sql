WITH molecule_totals AS (
    SELECT
        atom.molecule_id,
        COUNT(*) AS total_atoms
    FROM atom
    GROUP BY atom.molecule_id
),
valid_elements AS (
    SELECT 'c' AS element UNION ALL
    SELECT 'h' UNION ALL
    SELECT 'o' UNION ALL
    SELECT 'p' UNION ALL
    SELECT 'cl' UNION ALL
    SELECT 'f' UNION ALL
    SELECT 'ca' UNION ALL
    SELECT 'i' UNION ALL
    SELECT 'pb' UNION ALL
    SELECT 'sn' UNION ALL
    SELECT 'cu' UNION ALL
    SELECT 'na'
),
element_counts AS (
    SELECT
        atom.molecule_id,
        atom.element,
        COUNT(*) AS element_count
    FROM atom
    GROUP BY atom.molecule_id, atom.element
),
balanced_per_molecule AS (
    SELECT
        molecule.molecule_id,
        valid_elements.element,
        (
            COALESCE(element_counts.element_count, 0) * 1.0
            / molecule_totals.total_atoms
        ) *
        CASE
            WHEN valid_elements.element = 'c' THEN 2
            WHEN valid_elements.element = 'o' THEN 3
            WHEN valid_elements.element = 'pb' THEN 3
            ELSE 1
        END AS balanced_value
    FROM molecule
    CROSS JOIN valid_elements
    JOIN molecule_totals
        ON molecule.molecule_id = molecule_totals.molecule_id
    LEFT JOIN element_counts
        ON molecule.molecule_id = element_counts.molecule_id
        AND valid_elements.element = element_counts.element
)
SELECT
    LOWER(balanced_per_molecule.element) AS element,
    ROUND(SUM(balanced_per_molecule.balanced_value) /
    (SELECT COUNT(*) FROM molecule), 4) AS average_balanced_chemical_proportion
FROM balanced_per_molecule
GROUP BY balanced_per_molecule.element
ORDER BY average_balanced_chemical_proportion DESC;