
ALTER TABLE wrk_decklists
ADD COLUMN booster_id VARCHAR(10),
ADD COLUMN card_number VARCHAR(10);


UPDATE wrk_decklists
SET
  booster_id = split_part(card_url, '/', 5),
  card_number = split_part(card_url, '/', 6);

-- Clé étrangère sur wrk_decklists → wrk_cards
ALTER TABLE public.wrk_decklists
ADD CONSTRAINT fk_decklists_cards
FOREIGN KEY (booster_id, card_number) REFERENCES public.wrk_cards(booster_id, card_number);

CREATE INDEX idx_decklists_booster_card ON public.wrk_decklists(booster_id, card_number);