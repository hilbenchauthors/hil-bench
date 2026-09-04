SELECT 
    q.City,
    q.qualifying_schools,
    IFNULL(m.active_magnet_schools, 0) AS active_magnet_schools
FROM (
    SELECT s.City, COUNT(DISTINCT f.CDSCode) AS qualifying_schools
    FROM frpm f
    JOIN schools s ON f.CDSCode = s.CDSCode
    WHERE f.[Percent (%) Eligible FRPM (K-12)] >= 0.5
      AND f.[Percent (%) Eligible FRPM (Ages 5-17)] >= 0.5
      AND s.GSserved = 'P'
    GROUP BY s.City
) q
LEFT JOIN (
    SELECT s.City, COUNT(DISTINCT s.CDSCode) AS active_magnet_schools
    FROM schools s
    JOIN frpm f ON s.CDSCode = f.CDSCode
    WHERE s.Magnet = 1
      AND s.StatusType = 'Active'
      AND f.[Academic Year] = '2015-2016'
    GROUP BY s.City
) m ON q.City = m.City
ORDER BY q.City;