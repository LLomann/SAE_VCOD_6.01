
DROP TABLE IF EXISTS public.dwh_deck_play_win;

CREATE TABLE public.dwh_deck_play_win AS
SELECT
  total.deck_name_general,
  total.total_games,
  COALESCE(wins.game_win, 0) AS game_win,
  ROUND(COALESCE(wins.game_win::decimal, 0) / NULLIF(total.total_games, 0), 4) AS win_rate
FROM (
  -- Total de parties jouées par deck
  SELECT 
    deck_name_general, 
    SUM(game_count) AS total_games
  FROM (
    SELECT dds.deck_name_general, COUNT(*) AS game_count
    FROM dwh_decks_summary dds
    LEFT JOIN wrk_matches wm ON dds.player_id = wm.player_id_1
    GROUP BY dds.deck_name_general

    UNION ALL

    SELECT dds.deck_name_general, COUNT(*) AS game_count
    FROM dwh_decks_summary dds
    LEFT JOIN wrk_matches wm ON dds.player_id = wm.player_id_2
    GROUP BY dds.deck_name_general
  ) sub
  GROUP BY deck_name_general
) total

LEFT JOIN (
  -- Nombre de victoires par deck
  SELECT dds.deck_name_general, COUNT(*) AS game_win
  FROM dwh_decks_summary dds
  LEFT JOIN wrk_matches wm ON dds.player_id = wm.winner
  GROUP BY dds.deck_name_general
) wins
ON total.deck_name_general = wins.deck_name_general

ORDER BY win_rate DESC;


