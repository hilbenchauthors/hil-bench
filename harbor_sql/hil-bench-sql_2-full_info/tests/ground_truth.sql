SELECT
    (
        SELECT
            AVG(
                CAST(cards.power AS REAL) *
                CASE
                    WHEN cards.rarity IN ('common', 'uncommon') THEN 1
                    WHEN cards.rarity IN ('rare', 'mythic') THEN 2
                    ELSE NULL
                END
            )
        FROM cards
        WHERE
            cards.info6 = 1
            AND cards.power IS NOT NULL
            AND cards.power NOT LIKE '%*%'
            AND cards.power NOT LIKE '%+%'
            AND cards.power NOT LIKE '%-%'
            AND cards.power NOT LIKE '%∞%'
            AND LOWER(cards.name) LIKE '%element%'
    ) AS avg_balanced_power_elementals,

    (
        SELECT
            AVG(
                CAST(cards.power AS REAL) *
                CASE
                    WHEN cards.rarity IN ('common', 'uncommon') THEN 1
                    WHEN cards.rarity IN ('rare', 'mythic') THEN 2
                    ELSE NULL
                END
            )
        FROM cards
        WHERE
            cards.info6 = 1
            AND cards.power IS NOT NULL
            AND cards.power NOT LIKE '%*%'
            AND cards.power NOT LIKE '%+%'
            AND cards.power NOT LIKE '%-%'
            AND cards.power NOT LIKE '%∞%'
            AND cards.name = 'Lurrus of the Dream-Den'
    ) AS avg_balanced_power_lurrus;