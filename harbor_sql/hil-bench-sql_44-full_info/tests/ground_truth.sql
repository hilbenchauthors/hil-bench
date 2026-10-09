WITH
latest_us_epa_tri AS (
  SELECT a.molecule_id
  FROM atom a
  GROUP BY a.molecule_id
  HAVING SUM(CASE WHEN a.element IN ('pb','n','cl','f', 's') THEN 1 ELSE 0 END) > 0
),

halogen_only_hydrocarbons AS (
  SELECT a.molecule_id
  FROM atom a
  GROUP BY a.molecule_id
  HAVING SUM(CASE WHEN a.element = 'h' THEN 1 ELSE 0 END) > 0
  AND SUM(CASE WHEN a.element = 'c' THEN 1 ELSE 0 END) > 0
  AND SUM(CASE WHEN a.element IN ('f','cl','br','i') THEN 1 ELSE 0 END) > 0
  AND SUM(CASE WHEN a.element NOT IN ('h','c','f','cl','br','i') THEN 1 ELSE 0 END) = 0
),

bond_counts AS (
  SELECT
    b.molecule_id,
    SUM(CASE WHEN b.bond_type = '=' THEN 1 ELSE 0 END) AS n_double,
    SUM(CASE WHEN b.bond_type = '#' THEN 1 ELSE 0 END) AS n_triple
  FROM bond b
  GROUP BY b.molecule_id
),
complexity_scores AS (
  SELECT
    m.molecule_id,
    (2 * COALESCE(bc.n_double, 0) + 6 * COALESCE(bc.n_triple, 0)) AS complexity_score
  FROM molecule m
  LEFT JOIN bond_counts bc
    ON bc.molecule_id = m.molecule_id
),
complexity_ranked AS (
  SELECT
    cs.molecule_id,
    cs.complexity_score,
    ROW_NUMBER() OVER (ORDER BY cs.complexity_score ASC, cs.molecule_id ASC) AS rn,
    COUNT(*) OVER () AS total
  FROM complexity_scores cs
),
median_complexity AS (
  SELECT complexity_score AS median_score
  FROM complexity_ranked
  WHERE rn = (total + 1) / 2
),
advanced_tier AS (
  SELECT cs.molecule_id
  FROM complexity_scores cs
  CROSS JOIN median_complexity mc
  WHERE cs.complexity_score > mc.median_score
),

hazard_ranked AS (
  SELECT
    m.molecule_id,
    m.hazard_index,
    ROW_NUMBER() OVER (ORDER BY m.hazard_index ASC, m.molecule_id ASC) AS rn,
    COUNT(*) OVER () AS total
  FROM molecule m
),
hazard_q3 AS (
  SELECT hazard_index AS q3_value
  FROM hazard_ranked
  WHERE rn = (3 * total + 3) / 4
),
high_hazard AS (
  SELECT m.molecule_id
  FROM molecule m
  CROSS JOIN hazard_q3 q
  WHERE m.hazard_index >= q.q3_value
)

SELECT aw.molecule_id
FROM latest_us_epa_tri aw
JOIN halogen_only_hydrocarbons hoh
  ON hoh.molecule_id = aw.molecule_id
JOIN advanced_tier at
  ON at.molecule_id = aw.molecule_id
JOIN high_hazard hh
  ON hh.molecule_id = aw.molecule_id
ORDER BY aw.molecule_id ASC;