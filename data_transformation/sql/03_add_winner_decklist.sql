
ALTER TABLE wrk_matches
ADD COLUMN winner VARCHAR(50);

UPDATE wrk_matches
SET winner = CASE 
    WHEN matches_score_1 > matches_score_2 THEN player_id_1
    WHEN matches_score_2 > matches_score_1 THEN player_id_2
    ELSE NULL
END;