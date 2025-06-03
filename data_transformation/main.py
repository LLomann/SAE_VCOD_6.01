import psycopg
import os
import json
from datetime import datetime

boosters_directory = "../data_collection/booster"
boosters_directory = os.path.join(os.path.dirname(__file__), boosters_directory)
cards_directory = "../data_collection/card"
cards_directory = os.path.join(os.path.dirname(__file__), cards_directory)
tournament_directory = "../data_collection/tournament"
tournament_directory = os.path.join(os.path.dirname(__file__), tournament_directory)

def get_connection():
    return psycopg. connect(
        host="localhost",
        port="5432",
        dbname="postgres",
        user="postgres",
        password=""
    )

def execute_sql_script(path: str):
    full_path = os.path.join(os.path.dirname(__file__), path)
    with get_connection() as conn:
        with conn.cursor() as cur:
            with open(full_path, "r", encoding="utf-8") as f:
                sql = f.read()
                statements = [s.strip() for s in sql.split(';') if s.strip()]
                for stmt in statements:
                    cur.execute(stmt)
        conn.commit()

    
def insert_wrk_tournaments():
    tournament_data = []
    for file in os.listdir(tournament_directory):
        with open(f"{tournament_directory}/{file}") as f:
            tournament = json.load(f)
            tournament_data.append((
                tournament['id'], 
                tournament['name'], 
                datetime.strptime(tournament['date'], '%Y-%m-%dT%H:%M:%S.000Z'),
                tournament['organizer'], 
                tournament['format'], 
                int(tournament['nb_players'])
            ))

    tournament_data = tournament_data[:100000]  # Limiting to 100,000 entries for performance reasons

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO public.wrk_tournaments values (%s, %s, %s, %s, %s, %s)",
                tournament_data
            )
        conn.commit()

def insert_wrk_decklists():
    decklist_data = []
    for file in os.listdir(tournament_directory):
        with open(f"{tournament_directory}/{file}") as f:
            tournament = json.load(f)
            tournament_id = tournament['id']
            for player in tournament['players']:
                player_id = player['id']
                for card in player['decklist']:
                    decklist_data.append((
                        tournament_id,
                        player_id,
                        card['type'],
                        card['name'],
                        card['url'],
                        int(card['count']),
                    ))

    decklist_data = decklist_data[:100000]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO public.wrk_decklists values (%s, %s, %s, %s, %s, %s)",
                decklist_data
            )
        conn.commit()

def insert_wrk_matches():
    match_data = []
    for file in os.listdir(tournament_directory):
        with open(f"{tournament_directory}/{file}") as f:
            tournament = json.load(f)
            tournament_id = tournament['id']
            for match in tournament['matches']:
                results = match['match_results']
                if len(results) == 2:
                    player1 = results[0]
                    player2 = results[1]
                    match_data.append((
                        tournament_id,
                        player1['player_id'],
                        int(player1['score']),
                        player2['player_id'],
                        int(player2['score']),
                    ))

    match_data = match_data[:100000]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO public.wrk_matches values (%s, %s, %s, %s, %s)",
                match_data
            )
        conn.commit()


def insert_wrk_boosters():
    booster_data = []
    for filename in os.listdir(boosters_directory):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(boosters_directory, filename), encoding="utf-8") as f:
            boosters = json.load(f)
            for b in boosters:
                raw_card_count = b.get('card_count')
                try:
                    card_count = int(raw_card_count) if raw_card_count is not None else None
                except (ValueError, TypeError):
                    card_count = None  # ou log l'erreur si tu veux savoir quoi filtrer

                booster_data.append((
                    b.get('code') or b.get('booster_id'),
                    b.get('name') or b.get('booster_name'),
                    datetime.strptime(b.get('release_date'), "%d %b %y").date() if b.get('release_date') else None,
                    card_count,
                    b.get('image_url')
                ))

    booster_data = booster_data[:100000]  # Limiting to 100,000 entries for performance reasons

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO public.wrk_boosters (
                    booster_id, booster_name, release_date, card_count, image_url
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (booster_id) DO UPDATE 
                    SET booster_name = EXCLUDED.booster_name,
                        release_date = EXCLUDED.release_date,
                        card_count = EXCLUDED.card_count,
                        image_url = EXCLUDED.image_url
                """,
                booster_data
            )
        conn.commit()

def insert_wrk_cards():
    card_data = []
    for filename in os.listdir(cards_directory):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(cards_directory, filename), encoding="utf-8") as f:
            cards = json.load(f)
            # cards est une liste de cartes pour un booster
            for c in cards:
                card_data.append((
                    c.get('booster'),
                    c.get('number'),
                    c.get('name'),
                    c.get('type'),
                    c.get('hp'),
                    c.get('card_type'),
                    c.get('evolution'),
                    c.get('evolves_from'),
                    c.get('ability'),
                    c.get('ability_text'),
                    c.get('attack_1'),
                    c.get('attack_1_text'),
                    c.get('attack_2'),
                    c.get('attack_2_text'),
                    c.get('weakness'),
                    c.get('retreat'),
                    c.get('rule'),
                    c.get('image_url')
                ))

    card_data = card_data[:100000]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO public.wrk_cards (
                    booster_id,
                    card_number,
                    card_name,
                    card_pokemon_type,
                    card_hp,
                    card_type,
                    card_evolution,
                    card_evolves_from,
                    card_ability,
                    card_ability_label,
                    card_attack_1,
                    card_attack_1_label,
                    card_attack_2,
                    card_attack_2_label,
                    card_weakness,
                    card_retreat,
                    card_rule,
                    card_image_url
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
                """,
                card_data
            )
        conn.commit()


print("creating work tables")
execute_sql_script("sql/00_create_wrk_tables.sql")

print("insert raw tournament data")
insert_wrk_tournaments()

print("insert raw decklist data")
insert_wrk_decklists()

print("construct card database")
execute_sql_script("sql/01_dwh_cards.sql")
