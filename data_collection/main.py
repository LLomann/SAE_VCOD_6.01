from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass, asdict
import aiohttp
import aiofile
import asyncio
import os
import json
import re
import glob
from pathlib import Path

proxy = "" # "http://193.52.32.156:3128" ou "http://ocytohe.univ-ubs.fr:3128"
base_url = "https://play.limitlesstcg.com"
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36'}

# Dataclasses used for json generation
@dataclass
class DeckListItem:
  type:str
  url: str
  name: str
  count: int

@dataclass
class Player:
  id: str
  name: str
  placing: str
  country: str
  decklist: list[DeckListItem]

@dataclass
class MatchResult:
  player_id: str
  score: int

@dataclass
class Match:
  match_results: list[MatchResult]

@dataclass
class Tournament:
  id: str
  name: str
  date: str
  organizer: str
  format: str
  nb_players: str
  players: list[Player]
  matches:list[Match]

@dataclass
class BoosterSet:
    code: str
    name: str
    release_date: str
    card_count: int
    image_url: str

@dataclass
class Card:
    booster: str
    number: str
    name: str
    type: str
    hp: str
    card_type: str
    evolution: str
    evolves_from: str
    ability: str
    ability_text: str
    attack_1: str
    attack_1_text: str
    attack_2: str
    attack_2_text: str
    weakness: str
    retreat: str
    rule: str
    image_url: str


# Extract the tr tags from a table, omiting the first header
def extract_trs(soup: BeautifulSoup, table_class: str):
  trs = soup.find(class_=table_class).find_all("tr")
  trs.pop(0) # Remove header
  return trs

# Urls helpers
def construct_standings_url(tournament_id: str):
  return f"/tournament/{tournament_id}/standings?players"

def construct_pairings_url(tournament_id: str):
  return f"/tournament/{tournament_id}/pairings?players"

def construct_decklist_url(tournament_id: str, player_id: str):
  return f"/tournament/{tournament_id}/player/{player_id}/decklist"

# Extract the previous pairing pages urls
# This function assumes that the provided pairings page is the last of the tournament
def extract_previous_pairings_urls(pairings: BeautifulSoup):
  pairing_urls = pairings.find(class_="mini-nav")
  
  # If there is only one round, return empty array
  if pairing_urls is None:
    return []
  
  pairing_urls = pairing_urls.find_all("a")
  
  # Pop the last item in array because it's the current page
  pairing_urls.pop(-1)

  pairing_urls = [a.attrs["href"] for a in pairing_urls]
  
  return pairing_urls

# Check if the pairing page is a bracket (single elimination)
def is_bracket_pairing(pairings: BeautifulSoup):
  return pairings.find("div", class_="live-bracket") is not None

# Check if the pairing page is a table (swiss rounds)
regex_tournament_id = re.compile(r'[a-zA-Z0-9_\-]*')
def is_table_pairing(pairings: BeautifulSoup):
  pairings = pairings.find("div", class_="pairings")
  if pairings is not None:
    table = pairings.find("table", {'data-tournament': regex_tournament_id})
    if table is not None:
      return True

  return False

# Return a list of matches from a bracket style pairing page
def extract_matches_from_bracket_pairings(pairings: BeautifulSoup):
  
  matches = []
  
  matches_div = pairings.find("div", class_="live-bracket").find_all("div", class_="bracket-match")
  for match in matches_div:
    
    # We don't extract the match if one of the players is a bye
    if match.find("a", class_="bye") is not None:
      continue

    players_div = match.find_all("div", class_="live-bracket-player")
    match_results = []
    for index in range(len(players_div)):
      player = players_div[index]
      match_results.append(MatchResult(
        player.attrs["data-id"],
        int(player.find("div", class_="score").attrs["data-score"])
      ))

    matches.append(Match(match_results))
  
  return matches

# Return a list of matches from a table style pairing page
def extract_matches_from_table_pairings(pairings: BeautifulSoup):
  
  matches = []
  
  matches_tr = pairings.find_all("tr", {'data-completed': '1'})

  for match in matches_tr:
    p1 = match.find("td", class_="p1")
    p2 = match.find("td", class_="p2")

    if (p1 is not None and p2 is not None):
      matches.append(Match([
        MatchResult(p1.attrs["data-id"], int(p1.attrs["data-count"])),
        MatchResult(p2.attrs["data-id"], int(p2.attrs["data-count"]))
      ]))

  return matches

# Return a list of DeckListItems from a player decklist page
regex_card_url = re.compile(r'pocket\.limitlesstcg\.com/cards/.*')
def extract_decklist(decklist: BeautifulSoup) -> list[DeckListItem]:
  decklist_div = decklist.find("div", class_="decklist")
  cards = []
  if decklist_div is not None:
    cards_a = decklist_div.find_all("a", {'href': regex_card_url})
    for card in cards_a:
      cards.append(DeckListItem(
        card.parent.parent.find("div", class_="heading").text.split(" ")[0],
        card.attrs["href"],
        card.text[2:],
        int(card.text[0])
      ))

  return cards

# Extract a beautiful soup object from a url
async def async_soup_from_url(session: aiohttp.ClientSession, sem: asyncio.Semaphore, url: str, use_cache: bool = True):
    if url is None:
        return None

    # Répertoire du script courant
    script_dir = Path(__file__).resolve().parent
    cache_dir = script_dir / "cache"

    # Créer le dossier cache s'il n'existe pas
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Nettoyer le nom de fichier
    safe_filename = ''.join(x for x in url if x.isalnum() or x in ('-', '_'))
    cache_filename = cache_dir / f"{safe_filename}.html"

    html = ""

    if use_cache and cache_filename.is_file():
        async with sem:
            async with aiofile.async_open(cache_filename, "r") as file:
                html = await file.read()
    else:
        async with session.get(url) as resp:
            html = await resp.text()

        async with sem:
            async with aiofile.async_open(cache_filename, "w") as file:
                await file.write(html)

    return BeautifulSoup(html, 'html.parser')

async def extract_players(
  session: aiohttp.ClientSession,
  sem: asyncio.Semaphore,
  standings_page: BeautifulSoup,
  tournament_id: str) -> list[Player]:

  players = []
  player_trs = extract_trs(standings_page, "striped")
  player_ids = [player_tr.find("a", {'href': regex_player_id}).attrs["href"].split('/')[4] for player_tr in player_trs]
  has_decklist = [player_tr.find("a", {'href': regex_decklist_url}) is not None for player_tr in player_trs]
  player_names = [("__nul__" if player_tr.attrs['data-name'] == "Nul" else player_tr.attrs['data-name']) for player_tr in player_trs]
  player_placings=[player_tr.attrs.get("data-placing", -1) for player_tr in player_trs]
  player_countries=[player_tr.attrs.get("data-country", None) for player_tr in player_trs]

  decklist_urls = []
  for i in range(len(player_ids)):
    safe_player_id = "__nul__" if player_ids[i].lower() == "nul" else player_ids[i]
    decklist_urls.append(construct_decklist_url(tournament_id, safe_player_id) if has_decklist[i] else None)


  player_decklists = await asyncio.gather(*[async_soup_from_url(session, sem, url, True) for url in decklist_urls])

  players = []
  for i in range(len(player_ids)):
    if player_decklists[i] is None:
      continue

    players.append(Player(
      player_ids[i],
      player_names[i],
      player_placings[i],
      player_countries[i],
      extract_decklist(player_decklists[i])
    ))

  return players

async def extract_matches(
  session: aiohttp.ClientSession,
  sem: asyncio.Semaphore,
  tournament_id: str) -> list[Match]:

  matches = []
  last_pairings = await async_soup_from_url(session, sem, construct_pairings_url(tournament_id))
  previous_pairings_urls = extract_previous_pairings_urls(last_pairings)
  pairings = await asyncio.gather(*[async_soup_from_url(session, sem, url) for url in previous_pairings_urls])
  pairings.append(last_pairings)

  for pairing in pairings:
    if is_bracket_pairing(pairing):
      matches = matches + extract_matches_from_bracket_pairings(pairing)
    elif is_table_pairing(pairing):
      matches = matches + extract_matches_from_table_pairings(pairing)
    else:
      raise Exception("Unrecognized pairing type")
    
  return matches

regex_player_id = re.compile(r'/tournament/[a-zA-Z0-9_\-]*/player/[a-zA-Z0-9_]*')
regex_decklist_url = re.compile(r'/tournament/[a-zA-Z0-9_\-]*/player/[a-zA-Z0-9_]*/decklist')

async def handle_tournament_standings_page(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    standings_page: BeautifulSoup,
    tournament_id: str, 
    tournament_name: str,
    tournament_date: str,
    tournament_organizer: str,
    tournament_format: str,
    tournament_nb_players: int):
  
  tournament_dir = Path(__file__).parent / "tournament"
  tournament_dir.mkdir(exist_ok=True)

  tournament_file = tournament_dir / f"{tournament_id}.json"
  
  print(f"extracting tournament {tournament_id}", end="... ")

  if os.path.isfile(tournament_file):
    print("skipping because tournament is already in tournament")
    return
  else:
    directory = os.path.dirname(tournament_file)
    if not os.path.exists(directory):
        os.makedirs(directory)

  players = await extract_players(session, sem, standings_page, tournament_id)
  if len(players) == 0:
    print("skipping because no decklist was detected")
    return
  
  nb_decklists = sum(1 for player in players if len(player.decklist) > 0)
  matches = await extract_matches(session, sem, tournament_id)

  player_id_pattern = re.compile(r'"player_(\d+)"')

  max_player_num = 0
  json_files = tournament_dir.glob("*.json")

  for json_file in json_files:
    try:
      with open(json_file, "r") as f:
        content = f.read()
        matches_ids = player_id_pattern.findall(content)
        if matches_ids:
          max_in_file = max(int(num) for num in matches_ids)
          if max_in_file > max_player_num:
            max_player_num = max_in_file
    except Exception as e:
      print(f"Warning: could not parse {json_file}: {e}")

  player_id_to_anon = {}
  for idx, player in enumerate(players, start=max_player_num + 1):
    player_id_to_anon[player.id] = f"player_{idx}"

  anonymized_players = []
  for player in players:
    anonymized_players.append(Player(
      id=player_id_to_anon.get(player.id, player.id),
      name=player.name,
      placing=player.placing,
      country=player.country,
      decklist=player.decklist
    ))

  anonymized_matches = []
  for match in matches:
    anonymized_results = []
    for mr in match.match_results:
      anonymized_id = player_id_to_anon.get(mr.player_id, mr.player_id)
      anonymized_results.append(MatchResult(anonymized_id, mr.score))
    anonymized_matches.append(Match(anonymized_results))

  tournament = Tournament(
    tournament_id,
    tournament_name,
    tournament_date,
    tournament_organizer,
    tournament_format,
    tournament_nb_players,
    anonymized_players,
    anonymized_matches
  )

  print(f"{len(players)} players, {nb_decklists} decklists, {len(matches)} matches, player numbering starting from {max_player_num + 1}")
  
  with open(tournament_file, "w") as f:
    json.dump(asdict(tournament), f, indent=2)


first_tournament_page = "/tournaments/completed?game=POCKET&format=STANDARD&platform=all&type=online&time=all"
regex_standings_url = re.compile(r'/tournament/[a-zA-Z0-9_\-]*/standings')
async def handle_tournament_list_page(session: aiohttp.ClientSession, sem: asyncio.Semaphore, url: str):
  soup = await async_soup_from_url(session, sem, url, False)
  
  current_page = int(soup.find("ul", class_="pagination").attrs["data-current"])
  max_page = int(soup.find("ul", class_="pagination").attrs["data-max"])
  
  print(f"extracting completed tournaments page {current_page}")

  tournament_trs = extract_trs(soup, "completed-tournaments")
  tournament_ids = [tournament_tr.find("a", {'href': regex_standings_url}).attrs["href"].split('/')[2] for tournament_tr in tournament_trs]
  tournament_names=[tournament_tr.attrs['data-name']for tournament_tr in tournament_trs]
  tournament_dates=[tournament_tr.attrs['data-date']for tournament_tr in tournament_trs]
  tournament_organizers=[tournament_tr.attrs['data-organizer']for tournament_tr in tournament_trs]
  tournament_formats=[tournament_tr.attrs['data-format']for tournament_tr in tournament_trs]
  tournament_nb_players=[tournament_tr.attrs['data-players']for tournament_tr in tournament_trs]
  
  standings_urls = [construct_standings_url(tournament_id) for tournament_id in tournament_ids]
  
  # Get all standings page asynchroneously
  standings = await asyncio.gather(*[async_soup_from_url(session, sem, url) for url in standings_urls])

  for i in range(len(tournament_ids)):
    await handle_tournament_standings_page(session, sem, standings[i], tournament_ids[i], tournament_names[i], tournament_dates[i], tournament_organizers[i], tournament_formats[i], tournament_nb_players[i])

# _________________________________________________________________________________________________________________ 
    # Pour commencer par la dernière page
  # if current_page > 1:
  #   await handle_tournament_list_page(session, sem, f"{first_tournament_page}&page={current_page-1}")

  if current_page < max_page:
    await handle_tournament_list_page(session, sem, f"{first_tournament_page}&page={current_page+1}")
# _________________________________________________________________________________________________________________


def extract_booster_sets(soup: BeautifulSoup) -> list[BoosterSet]:
    table = soup.find("table", class_="data-table sets-table striped")
    if not table:
        return []

    sets = []
    rows = table.find_all("tr")

    for row in rows:
        cols = row.find_all("td")
        if not cols or len(cols) < 3:
            continue  # skip headings or invalid rows

        link = cols[0].find("a")
        if not link:
            continue

        name = link.text.strip().split('\n')[0].strip()
        code_span = link.find("span", class_="code")
        code = code_span.text.strip() if code_span else ""

        image = link.find("img", class_="set")
        image_url = image["src"] if image else ""

        release_date = cols[1].text.strip() if cols[1].text else ""
        card_count = int(cols[2].text.strip())

        sets.append(BoosterSet(
            code=code,
            name=name,
            release_date=release_date,
            card_count=card_count,
            image_url=image_url
        ))

    return sets

async def scrape_booster_sets(session: aiohttp.ClientSession, sem: asyncio.Semaphore):
    url = "https://pocket.limitlesstcg.com/cards"

    soup = await async_soup_from_url(session, sem, url, True)
    sets = extract_booster_sets(soup)


    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    BOOSTER_DIR = os.path.join(SCRIPT_DIR, "booster")
    os.makedirs(BOOSTER_DIR, exist_ok=True)
    output_path = os.path.join(BOOSTER_DIR, "booster_sets.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([asdict(s) for s in sets], f, indent=2, ensure_ascii=False)
    print(f"{len(sets)} booster sets saved to {output_path}")

def extract_cards_from_booster_html(soup: BeautifulSoup, booster_code: str) -> list[Card]:
    cards = []
    card_divs = soup.select("div.card-classic")

    for card_div in card_divs:
        # Nom, type, HP
        title = card_div.select_one(".card-text-name")
        name = title.text.strip() if title else ""

        type_hp_text = card_div.select_one(".card-text-title")
        type_, hp = "", ""
        if type_hp_text:
            txt = type_hp_text.get_text(" ", strip=True)
            parts = [p.strip() for p in txt.split("-") if p.strip()]
            if len(parts) >= 2:
                type_ = parts[-2]
                hp = parts[-1].replace("HP", "").strip()

        # Card Type, Evolution, Evolves from
        card_type_div = card_div.select_one(".card-text-type")
        card_type = ""
        evolution = ""
        evolves_from = ""

        if card_type_div:
            # Récupérer texte avec saut de ligne
            raw_text = card_type_div.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

            if len(lines) > 0:
                card_type = lines[0]
            if len(lines) > 1:
                evolution = lines[1].lstrip("- ").strip()

            evolves_link = card_type_div.select_one("a")
            if evolves_link:
                evolves_from = evolves_link.text.strip()

        # Ability
        ability = card_div.select_one(".card-text-ability-info")
        ability_name = ability.get_text(" ", strip=True).replace("Ability:", "").strip() if ability else ""

        ability_text = card_div.select_one(".card-text-ability-effect")
        ability_text = ability_text.get_text(" ", strip=True) if ability_text else ""

        # Attacks
        attacks = card_div.select("div.card-text-attack")
        attack_1 = attack_1_text = attack_2 = attack_2_text = ""
        if len(attacks) > 0:
            info1 = attacks[0].select_one(".card-text-attack-info")
            text1 = attacks[0].select_one(".card-text-attack-effect")
            attack_1 = info1.get_text(" ", strip=True) if info1 else ""
            attack_1_text = text1.get_text(" ", strip=True) if text1 else ""
        if len(attacks) > 1:
            info2 = attacks[1].select_one(".card-text-attack-info")
            text2 = attacks[1].select_one(".card-text-attack-effect")
            attack_2 = info2.get_text(" ", strip=True) if info2 else ""
            attack_2_text = text2.get_text(" ", strip=True) if text2 else ""

        # Weakness / Retreat
        weakness = retreat = ""
        wrr_blocks = card_div.select("p.card-text-wrr")
        if len(wrr_blocks) >= 1:
            lines = wrr_blocks[0].get_text("\n", strip=True).split("\n")
            for line in lines:
                if "Weakness" in line:
                    weakness = line.replace("Weakness:", "").strip()
                if "Retreat" in line:
                    retreat = line.replace("Retreat:", "").strip()

        # Rule
        rule = ""
        if len(wrr_blocks) > 1:
            rule = wrr_blocks[1].get_text(" ", strip=True)

        # Card Number
        number_text = card_div.select_one(".card-set-info")
        number = number_text.text.strip().split("#")[-1] if number_text else ""

        # Image URL
        img = card_div.select_one("img.card")
        image_url = img["src"] if img else ""

        card = Card(
            booster=booster_code,
            number=number,
            name=name,
            type=type_,
            hp=hp,
            card_type=card_type,
            evolution=evolution,
            evolves_from=evolves_from,
            ability=ability_name,
            ability_text=ability_text,
            attack_1=attack_1,
            attack_1_text=attack_1_text,
            attack_2=attack_2,
            attack_2_text=attack_2_text,
            weakness=weakness,
            retreat=retreat,
            rule=rule,
            image_url=image_url
        )

        cards.append(card)

    return cards


async def scrape_cards_from_boosters(session: aiohttp.ClientSession, sem: asyncio.Semaphore, booster_sets: list[BoosterSet]):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "card")
    os.makedirs(output_dir, exist_ok=True)

    for booster in booster_sets:
        print(f"Scraping cards for booster {booster.code}")
        url = f"https://pocket.limitlesstcg.com/cards/{booster.code}?display=compact"
        soup = await async_soup_from_url(session, sem, url, use_cache=True)

        cards = extract_cards_from_booster_html(soup, booster.code)
        json_path = os.path.join(output_dir, f"{booster.code}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in cards], f, indent=2, ensure_ascii=False)

        print(f" {len(cards)} cards saved to {json_path}")


def load_booster_sets() -> list[BoosterSet]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    booster_path = os.path.join(script_dir, "booster", "booster_sets.json")

    if not os.path.exists(booster_path):
        print(" Booster set file not found. Run scrape_booster_sets() first.")
        return []

    with open(booster_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [BoosterSet(**item) for item in data]


async def main():
  # Limit number of concurent http calls
  connector = aiohttp.TCPConnector(limit=20)

  # Limit number of concurent open files
  sem = asyncio.Semaphore(50)


# _________________________________________________________________________________________________________________
    # Pour commencer par la dernière page
  if proxy is not None:
    async with aiohttp.ClientSession(base_url=base_url, connector=connector, proxy=proxy) as session: 
      await scrape_booster_sets(session, sem)
      booster_sets = load_booster_sets()
      await scrape_cards_from_boosters(session, sem, booster_sets)
      await handle_tournament_list_page(session, sem, first_tournament_page)
  else:
    async with aiohttp.ClientSession(base_url=base_url, connector=connector ) as session: 
      await scrape_booster_sets(session, sem)
      booster_sets = load_booster_sets()
      await scrape_cards_from_boosters(session, sem, booster_sets)
      await handle_tournament_list_page(session, sem, first_tournament_page)

  # async with aiohttp.ClientSession(base_url=base_url, connector=connector) as session:
  #   soup = await async_soup_from_url(session, sem, first_tournament_page, False)
  #   max_page = int(soup.find("ul", class_="pagination").attrs["data-max"])
  #   await handle_tournament_list_page(session, sem, f"{first_tournament_page}&page={max_page}")
# _________________________________________________________________________________________________________________
    
asyncio.run(main())