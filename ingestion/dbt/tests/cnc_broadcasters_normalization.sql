-- Cas métier indépendants du contenu courant de la source CNC.
WITH cases (id, paid, free, expected, unknown_tokens) AS (
    VALUES
        (1, 'C+ Ciné+', 'F2 F3', 'Canal+, Ciné+, France2, France3', ''),
        (2, 'CANAL+/CINE+', 'M6 W9', 'Canal+, Ciné+, M6, W9', ''),
        (3, 'C+ C+ TPS', 'F2 / FR2; France 2', 'Canal+, France2, TPS', ''),
        (4, 'Orange TV Prime Video TV5 Monde', 'France TV', 'AmazonPrime, FranceTV, OrangeTV, TV5', ''),
        (5, 'CinéCinéma Disney +', 'F3 France.tv', 'Ciné+, Disney+, France3, FranceTV', ''),
        (6, 'CANAL J 13ème Rue', 'RMC Story DIRECT 8', '13èmeRue, CanalJ, Direct8, RMC Story', ''),
        (7, NULL, 'France Ô F2 F5', 'France2, FranceTV', ''),
        (8, NULL, 'FÔ France O', '', ''),
        (9, NULL, NULL, '', ''),
        (10, '', '   ', '', ''),
        (11, 'ÉtrangeTV', 'F2', 'France2, ÉtrangeTV', 'ÉtrangeTV'),
        (12, 'MAXIMUM', 'F20', 'F20, MAXIMUM', 'F20, MAXIMUM'),
        (13, 'C+' || CHR(160) || 'Ciné+', 'France' || CHR(8239) || '4', 'Canal+, Ciné+, France4', ''),
        (14, 'Amazon Prime Vidéo Netflix Netlfix', 'ARTE', 'AmazonPrime, Arte, Netflix', ''),
        (15, 'TV5 Monde5 Universcine Paramount', '0', '0, Paramount+, TV5, UniversCiné', '0'),
        (16, 'OCS, Ciné+;C+', 'TF1/TFX TMC', 'Canal+, Ciné+, OCS, TF1, TFX, TMC', '')
),
tokenized AS (
    SELECT cases.id, tokens.*
    FROM cases
    CROSS JOIN LATERAL (VALUES (paid), (free)) AS inputs(source_value)
    CROSS JOIN LATERAL (
        {{ cnc_broadcaster_tokens('inputs.source_value') }}
    ) AS tokens
),
actual AS (
    SELECT
        cases.id,
        cases.expected,
        cases.unknown_tokens,
        COALESCE(STRING_AGG(DISTINCT broadcaster_name, ', ' ORDER BY broadcaster_name)
            FILTER (WHERE NOT is_excluded), '') AS actual,
        COALESCE(STRING_AGG(DISTINCT token, ', ' ORDER BY token)
            FILTER (WHERE NOT is_recognized), '') AS actual_unknowns
    FROM cases
    LEFT JOIN tokenized USING (id)
    GROUP BY cases.id, cases.expected, cases.unknown_tokens
)
SELECT * FROM actual
WHERE actual IS DISTINCT FROM expected
    OR actual_unknowns IS DISTINCT FROM unknown_tokens
