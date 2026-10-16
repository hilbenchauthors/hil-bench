SELECT DISTINCT a.name, CASE WHEN a.degree IN ('High', 'Doc') THEN "Yes" ELSE "No" END as finished_highschool
FROM artists a
INNER JOIN cards c ON c.artistID = a.id
WHERE c.convertedManaCost BETWEEN 4 AND 6
  AND c.name IN ('Serrated Arrows', 'Angel of Mercy','Siege-Gang Commander','Castle', 'Josu Vess, Lich Knight', 'Clone', 'Mortal Combat', 'Blizzard Knight','Tsunami','Relentless Assault','Infused Arrows', 'Guard Dogs', 'Crusading Knight','Stronghold Discipline', 'Frozen Warrior X', 'Mausoleum Guard','Obsianus Golem', '	Syr Cadian, Knight Owl','Strands of Night','Pyre Hound', 'Ma Chao, Western Warrior','Sedris, the Traitor King','Salvage Titan','Godo, Bandit Warlord','Goblin Cannon','Fearing Knight')
  AND (' ' || c.name || ' ' LIKE '% Knight %'
   OR ' ' || c.name || ' ' LIKE '% Guard %'
   OR ' ' || c.name || ' ' LIKE '% Warrior %')
ORDER BY a.name DESC;
