WITH
-- Undirected adjacency from the connected table
adj AS (
    SELECT atom_id AS a1, atom_id2 AS a2 FROM connected
    UNION
    SELECT atom_id2 AS a1, atom_id AS a2 FROM connected
),

-- Blocker 5: Phosphorus-containing carcinogenic molecules
-- element = 'p' present AND molecule.label = '-'
phosphorus_mols AS (
    SELECT DISTINCT a.molecule_id
    FROM atom AS a
    JOIN molecule AS m ON m.molecule_id = a.molecule_id
    WHERE a.element = 'p'
      AND m.label = '-'
),

-- Blocker 2: Anhydrous hydrate molecules
-- Hydrate = at least one oxygen atom; Anhydrous = no O-H bonds
has_oxygen AS (
    SELECT DISTINCT molecule_id
    FROM atom
    WHERE element = 'o'
),
has_oh_bonds AS (
    SELECT DISTINCT a_o.molecule_id
    FROM adj
    JOIN atom AS a_o ON a_o.atom_id = adj.a1
    JOIN atom AS a_h ON a_h.atom_id = adj.a2
        AND a_h.molecule_id = a_o.molecule_id
    WHERE a_o.element = 'o'
      AND a_h.element = 'h'
),
anhydrous_hydrates AS (
    SELECT molecule_id
    FROM has_oxygen
    WHERE molecule_id NOT IN (SELECT molecule_id FROM has_oh_bonds)
),

-- Blocker 3: Substantial atomic framework (>= 20 bonds)
substantial AS (
    SELECT molecule_id
    FROM bond
    GROUP BY molecule_id
    HAVING COUNT(*) >= 20
),

-- Eligible molecules = phosphorus + anhydrous hydrate + substantial
eligible_molecules AS (
    SELECT pm.molecule_id
    FROM phosphorus_mols AS pm
    JOIN anhydrous_hydrates AS ah ON ah.molecule_id = pm.molecule_id
    JOIN substantial AS sf ON sf.molecule_id = pm.molecule_id
),

-- Canonical bond endpoints (one row per bond)
bond_atoms AS (
    SELECT bond_id,
           MIN(atom_id, atom_id2) AS endpoint1,
           MAX(atom_id, atom_id2) AS endpoint2
    FROM connected
    GROUP BY bond_id
),

-- Blocker 1: Only bonds between non-hydrogen atoms (fractional participation)
eligible_bonds AS (
    SELECT b.bond_id, b.molecule_id, b.bond_type,
           at1.element AS e1, at2.element AS e2
    FROM bond AS b
    JOIN eligible_molecules AS em ON em.molecule_id = b.molecule_id
    JOIN bond_atoms AS ba ON ba.bond_id = b.bond_id
    JOIN atom AS at1 ON at1.atom_id = ba.endpoint1
    JOIN atom AS at2 ON at2.atom_id = ba.endpoint2
    WHERE at1.element <> 'h'
      AND at2.element <> 'h'
)

-- Blocker 4: Double bonds between carbon and oxygen (C=O)
SELECT
    ROUND(
        100.0 * SUM(CASE WHEN bond_type = '=' AND ((e1 = 'c' AND e2 = 'o') OR (e1 = 'o' AND e2 = 'c')) THEN 1 ELSE 0 END)
             / COUNT(*),
        4
    ) AS percentage
FROM eligible_bonds;
