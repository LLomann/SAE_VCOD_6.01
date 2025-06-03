DROP TABLE IF EXISTS public.wrk_decklists;
DROP TABLE IF EXISTS public.wrk_matches;
DROP TABLE IF EXISTS public.wrk_cards;
DROP TABLE IF EXISTS public.wrk_boosters;
DROP TABLE IF EXISTS public.wrk_tournaments;

-- public.tournaments definition
CREATE TABLE public.wrk_tournaments (
  tournament_id VARCHAR PRIMARY KEY,
  tournament_name varchar NULL,
  tournament_date timestamp NULL,
  tournament_organizer varchar NULL,
  tournament_format varchar NULL,
  tournament_nb_players int NULL
);

CREATE TABLE public.wrk_decklists (
  tournament_id varchar NULL,
  player_id varchar NULL,
  card_type varchar NULL,
  card_name varchar NULL,
  card_url varchar NULL,
  card_count int NULL,
  PRIMARY KEY (tournament_id, player_id, card_name)
);
-- Clé étrangère sur wrk_decklists → wrk_tournaments
ALTER TABLE public.wrk_decklists
ADD CONSTRAINT fk_decklists_tournaments
FOREIGN KEY (tournament_id) REFERENCES public.wrk_tournaments(tournament_id);



-- aucune cléé primaire car on peut avoir deux joueurs que se batte deux fois dans le même tournoi
CREATE TABLE public.wrk_matches (
  tournament_id varchar NULL,
  player_id_1 varchar NULL,
  matches_score_1 int NULL,
  player_id_2 varchar NULL,
  matches_score_2 int NULL
);

-- Table boosters
CREATE TABLE public.wrk_boosters (
  booster_id VARCHAR PRIMARY KEY,
  booster_name VARCHAR NULL,
  release_date DATE NULL,
  card_count INT NULL,
  image_url TEXT NULL
);

-- Table cards
CREATE TABLE public.wrk_cards (
  booster_id VARCHAR NOT NULL,
  card_number VARCHAR NOT NULL,
  card_name VARCHAR NULL,
  card_pokemon_type VARCHAR NULL,
  card_hp VARCHAR NULL,
  card_type VARCHAR NULL,
  card_evolution VARCHAR NULL,
  card_evolves_from VARCHAR NULL,
  card_ability VARCHAR NULL,
  card_ability_label VARCHAR NULL,
  card_attack_1 VARCHAR NULL,
  card_attack_1_label TEXT NULL,
  card_attack_2 VARCHAR NULL,
  card_attack_2_label TEXT NULL,
  card_weakness VARCHAR NULL,
  card_retreat VARCHAR NULL,
  card_rule TEXT NULL,
  card_image_url TEXT NULL,
  PRIMARY KEY (booster_id, card_number)
);


-- Sur les colonnes utilisées dans les jointures
CREATE INDEX idx_cards_booster_card ON public.wrk_cards(booster_id, card_number);

-- Sur tournament_id et player_id dans wrk_decklists
CREATE INDEX idx_decklists_tournament_player ON public.wrk_decklists(tournament_id, player_id);

-- Sur card_type et card_evolution, qui sont filtrés dans la requête
CREATE INDEX idx_cards_type_evolution ON public.wrk_cards(card_type, card_evolution);



