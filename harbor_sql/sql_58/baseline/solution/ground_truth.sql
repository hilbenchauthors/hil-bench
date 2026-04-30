WITH
-- 1) Identify the 3 high-performing districts dynamically
top_districts AS (
    SELECT
        d.district_id,
        d.A2 AS district_name,
        d.A11 AS average_salary
    FROM district d
    ORDER BY d.A15 DESC
    LIMIT 3
),

-- 2) Attach current population using manual mapping
district_population AS (
    SELECT
        td.district_id,
        td.district_name,
        td.average_salary,
        CASE td.district_name
            WHEN 'Hl.m. Praha' THEN 1397880
            WHEN 'Benesov' THEN 103908
            WHEN 'Beroun' THEN 102562
            WHEN 'Kladno' THEN 171506
            WHEN 'Kolin' THEN 108281
            WHEN 'Kutna Hora' THEN 78565
            WHEN 'Melnik' THEN 114783
            WHEN 'Mlada Boleslav' THEN 137726
            WHEN 'Nymburk' THEN 107638
            WHEN 'Praha - vychod' THEN 204547
            WHEN 'Praha - zapad' THEN 161920
            WHEN 'Pribram' THEN 118285
            WHEN 'Rakovnik' THEN 56494
            WHEN 'Ceske Budejovice' THEN 202172
            WHEN 'Cesky Krumlov' THEN 61655
            WHEN 'Jindrichuv Hradec' THEN 89564
            WHEN 'Pelhrimov' THEN 72912
            WHEN 'Pisek' THEN 72912
            WHEN 'Prachatice' THEN 51061
            WHEN 'Strakonice' THEN 69773
            WHEN 'Tabor' THEN 101363
            WHEN 'Domazlice' THEN 54391
            WHEN 'Cheb' THEN 87958
            WHEN 'Karlovy Vary' THEN 110052
            WHEN 'Klatovy' THEN 84614
            WHEN 'Plzen - mesto' THEN 188407
            WHEN 'Plzen - jih' THEN 68918
            WHEN 'Plzen - sever' THEN 80666
            WHEN 'Rokycany' THEN 48770
            WHEN 'Sokolov' THEN 85200
            WHEN 'Tachov' THEN 52941
            WHEN 'Ceska Lipa' THEN 106256
            WHEN 'Decin' THEN 126294
            WHEN 'Chomutov' THEN 121480
            WHEN 'Jablonec n. Nisou' THEN 90569
            WHEN 'Liberec' THEN 170410
            WHEN 'Litomerice' THEN 117582
            WHEN 'Louny' THEN 85381
            WHEN 'Most' THEN 106773
            WHEN 'Teplice' THEN 124472
            WHEN 'Usti nad Labem' THEN 121699
            WHEN 'Havlickuv Brod' THEN 100000
            WHEN 'Hradec Kralove' THEN 160000
            WHEN 'Chrudim' THEN 100000
            WHEN 'Jicin' THEN 77368
            WHEN 'Nachod' THEN 112294
            WHEN 'Pardubice' THEN 92319
            WHEN 'Rychnov nad Kneznou' THEN 90000
            WHEN 'Semily' THEN 50000
            WHEN 'Svitavy' THEN 50000
            WHEN 'Trutnov' THEN 50000
            WHEN 'Usti nad Orlici' THEN 50000
            WHEN 'Blansko' THEN 106884
            WHEN 'Brno - mesto' THEN 371371
            WHEN 'Brno - venkov' THEN 203216
            WHEN 'Breclav' THEN 113842
            WHEN 'Hodonin' THEN 156524
            WHEN 'Jihlava' THEN 100000
            WHEN 'Kromeriz' THEN 108055
            WHEN 'Prostejov' THEN 110182
            WHEN 'Trebic' THEN 100000
            WHEN 'Uherske Hradiste' THEN 144203
            WHEN 'Vyskov' THEN 89097
            WHEN 'Zlin' THEN 192639
            WHEN 'Znojmo' THEN 100000
            WHEN 'Zdar nad Sazavou' THEN 50000
            WHEN 'Bruntal' THEN 50000
            WHEN 'Frydek - Mistek' THEN 50000
            WHEN 'Jesenik' THEN 50000
            WHEN 'Karvina' THEN 50000
            WHEN 'Novy Jicin' THEN 50000
            WHEN 'Olomouc' THEN 100000
            WHEN 'Opava' THEN 100000
            WHEN 'Ostrava - mesto' THEN 300000
            WHEN 'Prerov' THEN 50000
            WHEN 'Sumperk' THEN 50000
            WHEN 'Vsetin' THEN 50000
            ELSE NULL
        END AS current_population
    FROM top_districts td
),

-- 3) Weekly-frequency accounts in those districts
weekly_accounts AS (
    SELECT
        a.account_id,
        a.district_id
    FROM account a
    JOIN district_population dp
      ON dp.district_id = a.district_id
    WHERE a.frequency = 'T'
),

-- 4) Problematic loans issued in 1998
problematic_loans_1998 AS (
    SELECT DISTINCT
        l.account_id
    FROM loan l
    WHERE l.status = 'B'
      AND (
          substr(CAST(l.date AS TEXT), 1, 4) = '1998'
          OR substr(CAST(l.date AS TEXT), 1, 2) = '98'
      )
)

-- 5) Final aggregation per district
SELECT
    dp.district_name,
    COUNT(DISTINCT pl.account_id) AS problematic_weekly_accounts_1998,
    ROUND(
        COUNT(DISTINCT pl.account_id) * 1000.0 / dp.current_population,
        6
    ) AS accounts_per_1000_residents
FROM district_population dp
LEFT JOIN weekly_accounts wa
  ON wa.district_id = dp.district_id
LEFT JOIN problematic_loans_1998 pl
  ON pl.account_id = wa.account_id
GROUP BY
    dp.district_name,
    dp.average_salary,
    dp.current_population
ORDER BY
    dp.average_salary DESC;
