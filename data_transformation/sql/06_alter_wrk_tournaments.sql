ALTER TABLE wrk_tournaments
ADD COLUMN saison VARCHAR,
ADD COLUMN booster_name VARCHAR;

WITH valid_boosters AS (
  SELECT *
  FROM wrk_boosters
  WHERE booster_id != 'P-A'
    AND release_date IS NOT NULL
),
first_booster AS (
  SELECT *
  FROM valid_boosters
  ORDER BY release_date ASC
  LIMIT 1
),
booster_for_tournament AS (
  SELECT 
    wt.tournament_id,
    COALESCE(b.booster_id, fb.booster_id) AS saison,
    COALESCE(b.booster_name, fb.booster_name) AS booster_name
  FROM wrk_tournaments wt
  LEFT JOIN LATERAL (
    SELECT booster_id, booster_name
    FROM valid_boosters
    WHERE release_date <= wt.tournament_date
    ORDER BY release_date DESC
    LIMIT 1
  ) b ON TRUE
  CROSS JOIN first_booster fb
)
UPDATE wrk_tournaments wt
SET
  saison = bft.saison,
  booster_name = bft.booster_name
FROM booster_for_tournament bft
WHERE wt.tournament_id = bft.tournament_id;
