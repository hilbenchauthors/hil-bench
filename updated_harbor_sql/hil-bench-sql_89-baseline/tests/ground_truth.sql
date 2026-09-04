WITH zlatan AS (
    SELECT player_api_id
    FROM Player
    WHERE player_name = 'Zlatan Ibrahimovic'
),

pl_matches AS (
    SELECT
        m.season,
        m.date
    FROM Match m
    JOIN League l
        ON m.league_id = l.id
    JOIN zlatan z
        ON z.player_api_id IN (
            m.home_player_1, m.home_player_2, m.home_player_3, m.home_player_4,
            m.home_player_5, m.home_player_6, m.home_player_7, m.home_player_8,
            m.home_player_9, m.home_player_10, m.home_player_11,
            m.away_player_1, m.away_player_2, m.away_player_3, m.away_player_4,
            m.away_player_5, m.away_player_6, m.away_player_7, m.away_player_8,
            m.away_player_9, m.away_player_10, m.away_player_11
        )
    WHERE l.name LIKE '%Premier League%'
      AND m.season IN ('2016/2017', '2017/2018')
),

season_ranges AS (
    SELECT
        season,
        MIN(date) AS start_date,
        MAX(date) AS end_date
    FROM pl_matches
    GROUP BY season
),

attrs_in_season AS (
    SELECT
        sr.season,
        pa.attr_16 AS agility
    FROM season_ranges sr
    JOIN Player_Attributes pa
        ON pa.player_api_id = (SELECT player_api_id FROM zlatan)
       AND pa.date >= sr.start_date
       AND pa.date <= sr.end_date
    WHERE pa.attr_16 IS NOT NULL
),

ranked AS (
    SELECT
        season,
        agility,
        ROW_NUMBER() OVER (PARTITION BY season ORDER BY agility) AS rn,
        COUNT(*)    OVER (PARTITION BY season)               AS n
    FROM attrs_in_season
),

trim_params AS (
    SELECT DISTINCT
        season,
        n,
        CASE
            WHEN n < 10 THEN 1
            ELSE CAST(n * 0.10 AS INTEGER)
        END AS trim_n
    FROM ranked
),

trimmed AS (
    SELECT
        r.season,
        r.agility
    FROM ranked r
    JOIN trim_params tp
        ON tp.season = r.season
    WHERE r.rn > tp.trim_n
      AND r.rn <= (tp.n - tp.trim_n)
)

SELECT
    season,
    AVG(CAST(agility AS REAL)) AS robust_agility_score
FROM trimmed
GROUP BY season
ORDER BY season;
