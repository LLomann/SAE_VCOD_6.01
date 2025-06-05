![Pokemon TCG Pocket logo](https://upload.wikimedia.org/wikipedia/commons/c/c2/Pokemon_TCG_Pocket_logo.png)
# Pokemon TCG Pocket metagame analysis

[Pokémon Trading Card Game Pocket](https://en.wikipedia.org/wiki/Pok%C3%A9mon_Trading_Card_Game_Pocket) (often abbreviated as **Pokémon TCG Pocket**) is a free-to-play mobile adaptation of the [Pokémon Trading Card Game](https://en.wikipedia.org/wiki/Pok%C3%A9mon_Trading_Card_Game) (TCG), developed by [Creatures Inc.](https://en.wikipedia.org/wiki/Creatures_Inc.) and [DeNA](https://en.wikipedia.org/wiki/DeNA), and published by [The Pokémon Company](https://en.wikipedia.org/wiki/The_Pok%C3%A9mon_Company).

In this game, players build decks containing sets of cards, and battle each other online.

## Data Collection

The developers of the game do not publish publicly available data for you to consume. However, there are websites organizing tournaments, and publishing data (including decklists, and match results) about those tournaments online. One such organization is [Limitless TCG](https://play.limitlesstcg.com).

The list of completed Pokemon TCG Pocket tournaments on this website can be viewed at [this url](https://play.limitlesstcg.com/tournaments/completed?game=POCKET&format=STANDARD&platform=all&type=online&time=all).

Additional data is collected, including the different [booster](https://pocket.limitlesstcg.com/cards), as well as the cards contained in each booster.

A python script using BeautifulSoup as the html parser is provided. The output of this script is a json file for each tournament, containing decklists, pairings, booster and cards.

A sample of each data files (tournament, booster and card) in included in the directory in this repository. You will need to run this script yourself to collect all available data on the website using this method, be aware that this is time consuming, and the extraction program will likely have to run overnight.

To run the provided script, use the following commands :
```bash
cd data_collection
pip install beautifulsoup4
pip install aiohttp
pip install aiofile

python3 main.py
```

The code will begin execution by asking whether a proxy needs to be configured.  
If not, simply press Enter to skip this step.

The retrieved data is stored in the same folders as the sample data — namely, in the `booster`, `card`, and `tournament` directories.

Note: During the data collection process, each player in a tournament is assigned a unique identifier to ensure participant anonymity.

## Database

The chosen database system is portable PostgreSQL.  
It was selected because it can be easily executed from external hardware, such as a USB drive.  
For the purposes of this project, it was the most suitable solution available.

Note: You can also use a standard PostgreSQL installation if your computer is properly configured with a local database.

## Data Transformation

The purpose of the transformation step is to store the collected data into the database and prepare it for visualization by applying necessary transformations.

You will need to transform the collected data to make it usable for visualization.  
A simple Python script that ingests tournament and decklist data is provided,  
but feel free to use any ETL tool you are familiar with for this task.  
(Talend, Talaxie, or Pentaho are examples of tools you can use)

To run the provided script :
```bash
cd .. # pour ce re placer dans le bon repertoir
cd data_transformation
pip install psycopg

python3 main.py
```

If the provided library is not sufficient, you may also need to install additional dependencies.
```bash
pip install psycopg[binary]
```

Once the script is launched, several pieces of information must be entered in the terminal.  
You will need to provide the correct database connection details to ensure the script runs against the correct PostgreSQL database.

Here are the required connection parameters:
- host (default: 'localhost')
- port (default: '5432')
- dbname (default: 'postgres')
- user (default: 'postgres')
- password (no default, must be provided)

Depending on the chosen database (portable PostgreSQL or standard PostgreSQL), and the performance of your machine,  
the script may take a while to complete. In some cases, execution may take up to an hour.



## Data Analyse & Visualisation

Your final presentation to your client must feature graphs and tables that will showcase what you have learned from the data.

The tool chosen to represent our data and analyses is Power BI. We also created a number of indicators directly within the tool.

The last data refresh was performed on Tuesday, June 3, 2025.

The first page, "Overview", focuses on the boosters and the number of cards they contain. A tooltip indicates the most used Pokémon-type card in each booster. We can also see the 15 most frequently used decks in tournaments since the game's release. This page also includes two KPIs: the number of tournaments played up to the last data refresh, and the average number of players per tournament.

The second page, "Cards by Season", highlights the most used cards each season. To do this, we created the [Use Rate] indicator, which represents the usage rate of a card.
It is defined as:
Use Rate = Number of decks containing the card / Total number of decks.
We display a chart showing card usage rates by season. There are also two tables: one listing the 10 most used Trainer-type cards, and the other showing the 10 most used Pokémon cards. A season filter has been added for both tables.

The third page, "Decks by Season", focuses on the most used decks each season. We created the [Deck Use Rate] indicator, defined as:
Deck Use Rate = Number of times the deck was used in tournaments / Total number of decks used.
This indicator does not take into account the number of matches won, only the match outcomes.
It is also important to understand how the deck name was generated. We chose to use the base evolution of each Pokémon included in the deck. This approach helps group similar decks under a single representative name.

The fourth page focuses on deck win rates, based on the number of appearances and the season. It includes a table showing the number of appearances and win rate per deck, a chart displaying win rates of the most used decks by season, and a table listing the most common matchups between decks. For each matchup, we show the win rate of deck 1 against deck 2. This helps identify which decks are effective counters to others.



