WITH
label_counts AS (
  SELECT
    m.label,
    COUNT(*) AS cnt
  FROM molecule m
  WHERE m.label IS NOT NULL
  GROUP BY m.label
),
primary_class AS (
  SELECT lc.label
  FROM label_counts lc
  ORDER BY lc.cnt DESC, lc.label ASC
  LIMIT 1
),
primary_toxicity_molecules AS (
  SELECT m.molecule_id
  FROM molecule m
  JOIN primary_class pc
    ON pc.label = m.label
),

atom_stats AS (
  SELECT
    a.molecule_id,
    COUNT(DISTINCT a.atom_id) AS total_atoms,
    COUNT(DISTINCT CASE
      WHEN a.element NOT IN ('c','h') THEN a.atom_id
    END) AS hetero_atoms,
    COUNT(DISTINCT CASE
      WHEN a.element IN ('f','cl','br','i','s','p') THEN a.atom_id
    END) AS halogen_like_atoms,
    (1.0 * COUNT(DISTINCT CASE
      WHEN a.element NOT IN ('c','h') THEN a.atom_id
    END) / COUNT(DISTINCT a.atom_id)) AS hetero_fraction,
    (1.0 * COUNT(DISTINCT CASE
      WHEN a.element IN ('f','cl','br','i','s','p') THEN a.atom_id
    END) / COUNT(DISTINCT a.atom_id)) AS halogen_fraction
  FROM atom a
  WHERE a.molecule_id IS NOT NULL
  GROUP BY a.molecule_id
  HAVING COUNT(DISTINCT a.atom_id) > 0
),

avg_hetero AS (
  SELECT AVG(s.hetero_fraction) AS avg_hetero_fraction
  FROM atom_stats s
),
structural_complexity_tier AS (
  SELECT s.molecule_id
  FROM atom_stats s
  CROSS JOIN avg_hetero a
  WHERE s.hetero_fraction > a.avg_hetero_fraction
),

avg_halogen AS (
  SELECT AVG(s.halogen_fraction) AS avg_halogen_fraction
  FROM atom_stats s
),
significant_halogen_profile AS (
  SELECT s.molecule_id
  FROM atom_stats s
  CROSS JOIN avg_halogen a
  WHERE s.halogen_fraction > a.avg_halogen_fraction
),

p_s_linkage_molecules AS (
  SELECT a1.molecule_id
  FROM connected c
  JOIN atom a1
    ON a1.atom_id = c.atom_id
  JOIN atom a2
    ON a2.atom_id = c.atom_id2
  WHERE c.direction_flag = 1
    AND a1.molecule_id IS NOT NULL
    AND a2.molecule_id = a1.molecule_id
    AND (
      (a1.element = 'p' AND a2.element = 's')
      OR
      (a1.element = 's' AND a2.element = 'p')
    )
  GROUP BY a1.molecule_id
  HAVING COUNT(*) BETWEEN 1 AND 2
)

SELECT DISTINCT m.molecule_id
FROM molecule m
JOIN primary_toxicity_molecules pt
  ON pt.molecule_id = m.molecule_id
JOIN structural_complexity_tier sct
  ON sct.molecule_id = m.molecule_id
JOIN significant_halogen_profile shp
  ON shp.molecule_id = m.molecule_id
JOIN p_s_linkage_molecules psl
  ON psl.molecule_id = m.molecule_id
ORDER BY m.molecule_id;