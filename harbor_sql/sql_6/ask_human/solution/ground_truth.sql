SELECT
(
    (
        SELECT 
            COUNT(*) * 100.0 /
            (
                SELECT COUNT(DISTINCT u2.Id)
                FROM users u2
                JOIN posts p2 ON u2.Id = p2.OwnerUserId
                WHERE strftime('%Y', p2.CreaionDate) = '2010'
            )
        FROM (
            SELECT u.Id
            FROM users u
            JOIN posts p ON u.Id = p.OwnerUserId
            WHERE strftime('%Y', p.CreaionDate) = '2010'
            AND u.Reputation >= 15
            GROUP BY u.Id
            HAVING SUM(p.Score) > 1200
        )
    )
    -
    (
        SELECT 
            COUNT(*) * 100.0 /
            (
                SELECT COUNT(DISTINCT u2.Id)
                FROM users u2
                JOIN posts p2 ON u2.Id = p2.OwnerUserId
                WHERE strftime('%Y', p2.CreaionDate) = '2011'
            )
        FROM (
            SELECT u.Id
            FROM users u
            JOIN posts p ON u.Id = p.OwnerUserId
            WHERE strftime('%Y', p.CreaionDate) = '2011'
            AND u.Reputation >= 15
            GROUP BY u.Id
            HAVING SUM(p.Score) > 1200
        )
    )
) AS percentage_difference;
