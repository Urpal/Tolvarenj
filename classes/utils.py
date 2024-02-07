import pandas as pd


def highlight_row_equalto(s, value, column):
    is_max = pd.Series(data=False, index=s.index)
    is_max[column] = s.loc[column] == value
    return ["background-color: red" if is_max.any() else "" for v in is_max]

def get_pickled_obj(path: str):
    try:
        # stored_obj = db.storage.binary.get(path)
        with open(path, 'rb') as file:
            stored_obj = pickle.load(file)
        return stored_obj #pickle.loads(stored_obj)
    except:
        st.write(f"Could not load any pickled data with path: {path}")
        return None

def store_pickled_obj(path: str, data):
    with open(path, 'wb') as file:
        pickle.dump(data, file)


def bookies():
    """
    The bookies function returns a list of bookies that are used in the analysis.
        
    
    :return: A list of bookies
    :doc-author: Trelent
    """
    update_df_objbookies = [
        "Unibet",
        "Norsk Tipping",
        "Betfair",
        # "Betfair Sportsbook",
        "Bet365",
        "Pinnacle",
        "Paddy Power",
        "William Hill",
        "Marathon Bet",
        "Bet Victor",
        "Sky Bet",
        "Betclic",
        "888sport",
        "Casumo",
        "LiveScore Bet",
        "Virgin Bet",
        "Mr Green",
        "LeoVegas",
        "Coral",
        "Ladbrokes",
    ]
    return bookies


# Defining dataclasses
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict


@dataclass
class Game:
    game_nr: Optional[int] = None
    game_str: Optional[str] = None
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    arrangement_name: Optional[str] = None
    event_time: Optional[str] = None
    sport_name: Optional[str] = None
    status: Optional[str] = None

    dist: Optional[List[int]] = None
    dist_original: Optional[List[int]] = None
    dist_diff: Optional[List[int]] = None

    odds: Optional[List[int]] = None
    odds_original: Optional[List[int]] = None
    odds_diff: Optional[List[int]] = None

    result: Optional[str] = None
    outcome: Optional[str] = None

    def update(self, other_game: "Game"):
        if not isinstance(other_game, Game):
            raise ValueError("Input must be a game")
        else:
            # Do I need try except IF game at index is not defined or something?

            # Update distribution with the new values
            self.dist_diff = [
                a_i - b_i
                for a_i, b_i in zip(
                    other_game.dist,
                    self.dist_original,
                )
            ]

            # Update original distribution
            self.dist = other_game.dist

    def update_odds(self, odds: [int, int, int]):
        # Maybe add check if odds is empty too?
        if self.odds == None:
            # print("Odds is null. Set this odds!")
            self.odds = odds
            self.odds_original = odds
            self.odds_diff = [0, 0, 0]
        else:
            # print("Odds is NOT null. Update odds!")
            # Update odds with the new values
            self.odds_diff = [
                a_i - b_i
                for a_i, b_i in zip(
                    odds,
                    self.odds_original,
                )
            ]
            # Update new odds
            self.odds = odds

    def to_dict(self):
        return asdict(self)


@dataclass
class Gameday:
    day_nr: Optional[int] = None
    day_str: Optional[str] = None
    sale_stop: Optional[str] = None
    last_game_time: Optional[str] = None
    sale_amount_full: Optional[int] = None
    sale_amount_half: Optional[int] = None
    bonus: Optional[int] = None
    games: Optional[Dict[str, Game]] = None

    payout_total_full: Optional[int] = None
    payout_total_half: Optional[int] = None
    prizes_halftime: Optional[Dict[str, Dict[int, int]]] = None
    prizes_fulltime: Optional[Dict[str, Dict[int, int]]] = None

    def compute_total_payout(self):
        self.payout_total_full = 0
        self.payout_total_half = 0
        for outer_key, inner_dict in self.prizes_fulltime.items():
            # for inner_key, value in inner_dict.items():
            part_calc = inner_dict["amount"] * inner_dict["numberOfWinners"]
            inner_dict["total"] = part_calc
            self.payout_total_full += part_calc
        for outer_key, inner_dict in self.prizes_halftime.items():
            # for inner_key, value in inner_dict.items():
            part_calc = inner_dict["amount"] * inner_dict["numberOfWinners"]
            inner_dict["total"] = part_calc
            self.payout_total_half += part_calc

    def to_dict(self):
        json_dict = asdict(self)
        try:
            json_dict["games"] = {
                key: game.to_dict() for key, game in self.games.items()
            }
        except AttributeError:
            print("Gameday has no games, return None")
        return json_dict


country_mapping = {
    "Frankrike": "France",
    "Østerrike": "Austria",
    "Kroatia": "Croatia",
    "Danmark": "Denmark",
    "Polen": "Poland",
    "Nederland": "Netherlands",
    "Litauen": "Lithuania",
    "Færøyene": "Faroe Islands",
    "Aserbajdsjan": "Azerbaijan",
    "Tyskland": "Germany",
    "Ungarn": "Hungary",
    "Belgia": "Belgium",
    "Norge": "Norway",
    "Spania": "Spain",
    "Sveits": "Switzerland",
    "Tsjekkia": "Czech Republic",
    "Skottland": "Scotland",
    "Kypros": "Cyprus",
    "Hellas": "Greece",
    "Kasakhstan": "Kazakhstan",
    "Tyrkia": "Turkey",
    "Liechtenstein": "Liechtenstein",
    "Ukraina": "Ukraine",
    "Irland": "Republic of Ireland",
    "Sverige": "Sweden",
}

# Add a list of stop words that makes it hard to connect NT team names to their respective full names..
stopwords = [
    "fc",
    "fk",
    "athletic",
    "city",
    "united",
    "bk",
    "hotspur",
    "albion",
]  # Will this actually help?

# Get active sport keys from NT arrangement values. # TODO: Check the rest of the keys
NT_to_theOdds_mapping = {
    "nations league": "soccer_uefa_nations_league",  # CHECKED
    # "norsk tipping" : nan,
    # "postnord" : nan,
    # "toppserien" : nan,
    "eliteserien": "soccer_norway_eliteserien",  # CHECKED
    # "obos" : nan,
    "premier league": "soccer_epl",  # CHECKED
    "championship": "soccer_efl_champ",  # CHECKED
    "league 1": "soccer_england_league1",
    "league 2": "soccer_england_league2",
    "fa-cup": "soccer_fa_cup",
    "ligacup": "soccer_england_efl_cup",
    "laliga": "soccer_spain_la_liga",
    "laliga 2": "soccer_spain_segunda_division",
    "bundesliga": "soccer_germany_bundesliga",
    "2. bundesliga": "soccer_germany_bundesliga2",
    "serie a": "soccer_italy_serie_a",
    "serie b": "soccer_italy_serie_b",
    "ligue 1": "soccer_france_league_one",
    "ligue 2": "soccer_france_league_two",
    "allsvenskan": "soccer_sweden_allsvenskan",
    "superettan": "soccer_sweden_superettan",
    "superliga": "soccer_denmark_superliga",
    "eredivise": "soccer_netherlands_eredivisie",
    "vm": "soccer_fifa_world_cup",
    "premiership": "soccer_spl",
    "primeira": "soccer_portugal_primeira_liga",
    "champions league": "soccer_uefa_champs_league",
    "europa league": "soccer_uefa_europa_league",
    # "europa conference league": "soccer_uefa_europa_conference_league",
    "TYR S": "soccer_turkey_super_league"
    # "conference league" : nan
}
# https://the-odds-api.com/sports-odds-data/sports-apis.html









#### Update DF ####
# Not sure if this is really needed. Should probably move over to tabular storage with ACID properties rather than objects in a bucket
import datetime
import json

# import databutton as db
import pandas as pd
from dateutil import parser
from utils import Gameday
import pickle
import streamlit as st


# Update the matchday view dataframe
#@st.cache_data
def update_df_obj():
    ######################################
    #   Load active GD
    ######################################
    try:
        # with open(pickle_file_path, "rb") as file:
        #    gd = pickle.load(file)
        activegd_obj = db.storage.binary.get("active-gd-pkl")
        gd = pickle.loads(activegd_obj)
        print("Active GD available-> update DF")
    except FileNotFoundError:
        print("File does not exist.")
        gd = Gameday()
        # activeGD = {} # db.storage.json.get("gameDayInfo.json")
    except pickle.PickleError as e:
        print(f"An error occurred with the pickle file: {e}")

    columns = [
        "GameNr",
        "Game",
        "H_folk",
        "U_folk",
        "B_folk",
        "H_folk_change",
        "U_folk_change",
        "B_folk_change",
        "H_mean",
        "U_mean",
        "B_mean",
        "H_mean_change",
        "U_mean_change",
        "B_mean_change",
        "H_valu",
        "U_valu",
        "B_valu",
        "tip",
    ]

    data = []
    # game_counter = 0
    for gameName, game in gd.games.items():
        h_mean, h_imp, u_mean, u_imp, b_mean, b_imp, h_diff, u_diff, b_diff = [
            0
        ] * 9  # Init datafram variables to zero.

        h_mean = (
            game.odds[0] if game.odds != None else 1
        )  # if len(game.odds) != 0 else 1
        h_imp = (1 / h_mean) * 100
        u_mean = game.odds[1] if game.odds != None else 1
        u_imp = (1 / u_mean) * 100
        b_mean = game.odds[2] if game.odds != None else 1
        b_imp = (1 / b_mean) * 100

        # h_mean_old = game.odds_original[0]
        h_diff = (
            game.odds_diff[0] if game.odds_diff != None else 1
        )  # if len(game.odds_diff) != 0 else 1
        # u_mean_old = game.odds_original[1]
        u_diff = game.odds_diff[1] if game.odds_diff != None else 1
        # b_mean_old = game.odds_original[2]
        b_diff = game.odds_diff[2] if game.odds_diff != None else 1

        # Add a check to see if there are None values and handle them to set it as zero?
        # print(f"Could not get mean for Game: {gameName}")
        # h_imp = game["dist"][0]
        # u_imp = game["dist"][1]
        # b_imp = game["dist"][2]

        # Get values:
        h_valu = h_imp - game.dist[0] if h_imp != 100 else 1
        u_valu = u_imp - game.dist[1] if u_imp != 100 else 1
        b_valu = b_imp - game.dist[2] if h_imp != 100 else 1

        # Calculate tip TODO: This was just something quick and dirty :P This should be properly defined in a formula ;)
        if b_valu >= 10 and b_mean <= 3:
            tip = "B"
        elif u_valu >= 10 and u_mean <= 3.65:
            tip = "U"
        elif h_valu >= 10 and h_mean <= 3:
            tip = "H"
        else:
            tip = "B"
            best_valu = b_valu
            if u_valu > best_valu:
                tip = "U"
                best_valu = u_valu
            if h_valu > best_valu:
                tip = "H"

        # Check status of match.
        if game.status in ["Avlyst", "Strøket"]:  # Or not "Ikke startet" ?
            tip = "-"

        # data[game_counter] = [game["gameNr"], game["game"], game.dist[0], game.dist[1], game.dist[2],
        #                     h_mean, u_mean, b_mean, h_imp-game.dist[0], u_imp-game.dist[1], b_imp-game.dist[2]]
        data.append(
            [
                game.game_nr,
                game.game_str,
                game.dist[0],
                game.dist[1],
                game.dist[2],
                game.dist_diff[0],
                game.dist_diff[1],
                game.dist_diff[2],
                h_mean,
                u_mean,
                b_mean,
                h_diff,
                u_diff,
                b_diff,
                h_valu,
                u_valu,
                b_valu,
                tip,
            ]
        )
    df = pd.DataFrame(data=data, columns=columns)  # , index = "GameNr")
    df.sort_index(inplace=True)
    df[
        [
            "H_mean",
            "U_mean",
            "B_mean",
            "H_mean_change",
            "U_mean_change",
            "B_mean_change",
            "H_valu",
            "U_valu",
            "B_valu",
        ]
    ] = df[
        [
            "H_mean",
            "U_mean",
            "B_mean",
            "H_mean_change",
            "U_mean_change",
            "B_mean_change",
            "H_valu",
            "U_valu",
            "B_valu",
        ]
    ].round(
        2
    )
    # print(df.head(12))
    # Put dataframe in databutton storage
    # db.storage.dataframes.put("MATCHDAY_DF", df)
    db.storage.dataframes.put(key="MATCHDAY_DF_obj", value=df)


def update_df():
    ## Add trusted bookies since some of the bookies (or probably THE ODDS API) is slow with updating their odds..
    trusted_bookies = ["Betfair Sportsbook", "Unibet"]

    ######################################
    #   Load frame
    ######################################
    gameday_dict = db.storage.json.get("gameDayInfo.json")

    closest_matchday = "MIDWEEK"
    time_diff = 60 * 60 * 24 * 7
    time_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    for game_day in gameday_dict:
        difference = (
            parser.parse(gameday_dict[game_day]["saleStop"]) - time_now
        ).total_seconds()
        # print(f"time Diff: {difference}")
        if (
            difference < time_diff
            and parser.parse(gameday_dict[game_day]["saleStop"]) > time_now
        ):
            closest_matchday = game_day
            time_diff = difference

    columns = [
        "GameNr",
        "Game",
        "H_folk",
        "U_folk",
        "B_folk",
        "H_folk_change",
        "U_folk_change",
        "B_folk_change",
        "H_mean",
        "U_mean",
        "B_mean",
        "H_mean_change",
        "U_mean_change",
        "B_mean_change",
        "H_valu",
        "U_valu",
        "B_valu",
        "tip",
    ]

    data = []
    # game_counter = 0
    for gameName, game in gameday_dict[closest_matchday]["games"].items():
        h_mean, h_imp, u_mean, u_imp, b_mean, b_imp, h_diff, u_diff, b_diff = [
            0
        ] * 9  # Init datafram variables to zero.

        # Get new accumulated odds
        h_acc, u_acc, b_acc, h_acc_old, u_acc_old, b_acc_old = [0] * 6

        number_of_bookies = 0
        for bookie in game["odds"]:
            if bookie in trusted_bookies:
                h_acc += game["odds"][bookie][0]
                u_acc += game["odds"][bookie][1]
                b_acc += game["odds"][bookie][2]

                # # Do two loops since the number of bookies could actually change (even though it should not..)
                # for bookie in game["odds_original"]:
                h_acc_old += game["odds_original"][bookie][0]
                u_acc_old += game["odds_original"][bookie][1]
                b_acc_old += game["odds_original"][bookie][2]

                number_of_bookies += 1

        # Find the mean and implied value of the entries
        if len(game["odds"]) != 0 and (
            "Betfair Sportsbook" in game["odds"] or "Unibet" in game["odds"]
        ):
            print(f"Get mean odds for Game: {gameName}")
            h_mean = h_acc / number_of_bookies  # len(game["odds"])
            h_imp = (1 / h_mean) * 100
            u_mean = u_acc / number_of_bookies
            u_imp = (1 / u_mean) * 100
            b_mean = b_acc / number_of_bookies
            b_imp = (1 / b_mean) * 100

            h_mean_old = h_acc_old / number_of_bookies  # len(game["odds_original"])
            h_diff = h_mean - h_mean_old
            u_mean_old = u_acc_old / number_of_bookies
            u_diff = u_mean - u_mean_old
            b_mean_old = b_acc_old / number_of_bookies
            b_diff = b_mean - b_mean_old

        else:
            print(f"Could not get mean for Game: {gameName}")
            h_imp = game["dist"][0]
            u_imp = game["dist"][1]
            b_imp = game["dist"][2]

        # Get values:
        h_valu = h_imp - game["dist"][0]
        u_valu = u_imp - game["dist"][1]
        b_valu = b_imp - game["dist"][2]

        # Calculate tip TODO: This was just something quick and dirty :P This should be properly defined in a formula ;)
        if b_valu >= 10 and b_mean <= 3:
            tip = "B"
        elif u_valu >= 10 and u_mean <= 3.65:
            tip = "U"
        elif h_valu >= 10 and h_mean <= 3:
            tip = "H"
        else:
            tip = "B"
            best_valu = b_valu
            if u_valu > best_valu:
                tip = "U"
                best_valu = u_valu
            if h_valu > best_valu:
                tip = "H"

        # Check status of match.
        if game["status"] in ["Avlyst", "Strøket"]:  # Or not "Ikke startet" ?
            tip = "-"

        # data[game_counter] = [game["gameNr"], game["game"], game["dist"][0], game["dist"][1], game["dist"][2],
        #                     h_mean, u_mean, b_mean, h_imp-game["dist"][0], u_imp-game["dist"][1], b_imp-game["dist"][2]]
        data.append(
            [
                game["gameNr"],
                game["game"],
                game["dist"][0],
                game["dist"][1],
                game["dist"][2],
                game["diff"][0],
                game["diff"][1],
                game["diff"][2],
                h_mean,
                u_mean,
                b_mean,
                h_diff,
                u_diff,
                b_diff,
                h_valu,
                u_valu,
                b_valu,
                tip,
            ]
        )
    df = pd.DataFrame(data=data, columns=columns)  # , index = "GameNr")
    df.sort_index(inplace=True)
    df[
        [
            "H_mean",
            "U_mean",
            "B_mean",
            "H_mean_change",
            "U_mean_change",
            "B_mean_change",
            "H_valu",
            "U_valu",
            "B_valu",
        ]
    ] = df[
        [
            "H_mean",
            "U_mean",
            "B_mean",
            "H_mean_change",
            "U_mean_change",
            "B_mean_change",
            "H_valu",
            "U_valu",
            "B_valu",
        ]
    ].round(
        2
    )
    print(df.head(12))
    # Put dataframe in databutton storage
    # db.storage.dataframes.put("MATCHDAY_DF", df)
    db.storage.dataframes.put(key="MATCHDAY_DF", value=df)


# def update_betfair_df():
#     import databutton as db
#     import json
#     import pandas as pd
#     import numpy as np
#     import datetime
#     from dateutil import parser
#     # import pprint

#     ######################################
#     #   Load data from json and get closest match day TODO: Move this to a variable?
#     ######################################
#     gameday_dict = db.storage.json.get('gameDayInfo.json')

#     closest_matchday = "MIDWEEK"
#     time_diff = 60*60*24*7
#     time_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
#     for game_day in gameday_dict:
#         difference = (parser.parse(gameday_dict[game_day]["saleStop"]) - time_now).total_seconds()
#         # print(f"time Diff: {difference}")
#         if difference < time_diff and parser.parse(gameday_dict[game_day]["saleStop"]) > time_now:
#             closest_matchday = game_day
#             time_diff = difference

#     columns=["GameNr","Game", "H_folk", "U_folk", "B_folk","H_folk_change", "U_folk_change", "B_folk_change",
#             "H_mean", "U_mean", "B_mean", "H_mean_change", "U_mean_change", "B_mean_change" , "H_valu", "U_valu", "B_valu",
#             "tip"]

#     data = []
#     # game_counter = 0
#     for gameName, game in gameday_dict[closest_matchday]["games"].items():

#         h_mean, h_imp,  u_mean, u_imp, b_mean, b_imp, h_diff, u_diff, b_diff = [0] * 9 #Init datafram variables to zero.

#         # Check if there is any odds at all.
#         if 'odds' in game.keys():

#             # Find the mean and implied value of the entries
#             h_mean = game['odds'][0]
#             h_imp = (1/h_mean)*100
#             u_mean = game['odds'][1]
#             u_imp = (1/u_mean)*100
#             b_mean = game['odds'][2]
#             b_imp = (1/b_mean)*100

#             h_mean_old = game['odds_original'][0]
#             h_diff = h_mean - h_mean_old
#             u_mean_old = game['odds_original'][1]
#             u_diff = u_mean - u_mean_old
#             b_mean_old = game['odds_original'][2]
#             b_diff = b_mean - b_mean_old

#         # If no odds is available, then set implied values equal to the distribution of the people.
#         else:
#             h_imp = game["dist"][0]
#             u_imp = game["dist"][1]
#             b_imp = game["dist"][2]

#         # Get values:
#         h_valu = h_imp-game["dist"][0]
#         u_valu = u_imp-game["dist"][1]
#         b_valu = b_imp-game["dist"][2]

#         # Calculate tip TODO: This was just something quick and dirty :P This should be properly defined in a formula ;)
#         if b_valu >= 10 and b_mean <= 3:
#             tip = "B"
#         elif u_valu >= 10 and u_mean <= 3.65:
#             tip = "U"
#         elif h_valu >= 10 and h_mean <= 3:
#             tip = "H"
#         else:
#             tip = "B"
#             best_valu = b_valu
#             if u_valu > best_valu:
#                 tip = "U"
#                 best_valu = u_valu
#             if h_valu > best_valu:
#                 tip = "H"

#         # data[game_counter] = [game["gameNr"], game["game"], game["dist"][0], game["dist"][1], game["dist"][2],
#         #                     h_mean, u_mean, b_mean, h_imp-game["dist"][0], u_imp-game["dist"][1], b_imp-game["dist"][2]]
#         data.append([game["gameNr"], game["game"], game["dist"][0], game["dist"][1], game["dist"][2],
#                     game["diff"][0], game["diff"][1], game["diff"][2], h_mean, u_mean, b_mean,
#                     h_diff, u_diff, b_diff, h_valu, u_valu, b_valu, tip])
#     df = pd.DataFrame(data=data,columns=columns)#, index = "GameNr")
#     # print(df)#Put dataframe in databutton storage
#     db.storage.dataframes.put(df, "MATCHDAY_DF")






#### Handle the odds ####
# Need something similar but maybe rather a function that returns this shit 
    
import datetime
import difflib
import json
import statistics

# import databutton as db
import pandas as pd
from dateutil import parser


def handle_the_odds():
    ######################################
    #   Load frames
    ######################################
    gameday_dict = db.storage.json.get("gameDayInfo.json")

    odds = db.storage.json.get("odds.json")

    # Some chosen country name mappings where the norwegian names does NOT correspond with the english ones.
    # TODO: Find something that is usable directly. Also move this to utils or something
    country_mapping = {
        "Frankrike": "France",
        "Østerrike": "Austria",
        "Kroatia": "Croatia",
        "Danmark": "Denmark",
        "Polen": "Poland",
        "Nederland": "Netherlands",
        "Litauen": "Lithuania",
        "Færøyene": "Faroe Islands",
        "Aserbajdsjan": "Azerbaijan",
        "Tyskland": "Germany",
        "Ungarn": "Hungary",
        "Belgia": "Belgium",
        "Norge": "Norway",
        "Spania": "Spain",
        "Sveits": "Switzerland",
        "Tsjekkia": "Czech Republic",
        "Skottland": "Scotland",
        "Kypros": "Cyprus",
        "Hellas": "Greece",
        "Kasakhstan": "Kazakhstan",
        "Tyrkia": "Turkey",
        "Liechtenstein": "Liechtenstein",
        "Ukraina": "Ukraine",
        "Irland": "Republic of Ireland",
        "Sverige": "Sweden",
    }

    # Add a list of stop words that makes it hard to connect NT team names to their respective full names..
    stopwords = [
        "fc",
        "fk",
        "athletic",
        "city",
        "united",
        "bk",
        "hotspur",
        "albion",
    ]  # Will this actually help?

    ######################################
    #  Get closest game_day since that is the only one we care about atm
    ######################################
    closest_matchday = "MIDWEEK"
    time_diff = 60 * 60 * 24 * 7
    time_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    for game_day in gameday_dict:
        difference = (
            parser.parse(gameday_dict[game_day]["saleStop"]) - time_now
        ).total_seconds()
        # print(f"time Diff: {difference}")
        if (
            difference < time_diff
            and parser.parse(gameday_dict[game_day]["saleStop"]) > time_now
        ):
            closest_matchday = game_day
            time_diff = difference
    # print(f"Gameday: {closest_matchday}")

    ######################################
    #   Update data json with new odds data.
    ######################################
    # Find related odds to the matches.
    # days = ["MIDWEEK", "SATURDAY", "SUNDAY"]
    for gameName, game in gameday_dict[closest_matchday]["games"].items():

        # Check if game is international, then change from Norwegian to english if necessary in order to pinpoint better the correct match!
        ##### IF INTERNATIONAL GAME ##################
        heime = game["home"]
        borte = game["away"]
        # TODO: Check this for the World cup!
        if (
            ("nations league" in game["arrangementName"].lower())
            or ("mesterskap" in game["arrangementName"].lower())
            or ("vm" in game["arrangementName"].lower())
        ):
            if game["home"] in country_mapping:
                heime = country_mapping[game["home"]]
            if game["away"] in country_mapping:
                borte = country_mapping[game["away"]]
        ###############################################

        # Loop through the odds matches and try to find the correct fit (Norwegian to english if internationak games at least..)
        for market in odds:
            for match in market:
                # Map home and away since this is directly linked to the odds placement from the API calls
                home = 0
                away = 1
                if match["teams"][0] != match["home_team"]:
                    home = 1
                    away = 0

                # Strip known football club namings like fk, fc, united and so on since these are missing at NT...
                heime_words = heime.split()
                heime_stripped_list = [
                    word for word in heime_words if word.lower() not in stopwords
                ]
                heime_team_stripped = " ".join(heime_stripped_list)

                borte_words = borte.split()
                borte_stripped_list = [
                    word for word in borte_words if word.lower() not in stopwords
                ]
                borte_team_stripped = " ".join(borte_stripped_list)

                home_words = match["teams"][home].split()
                home_stripped_list = [
                    word for word in home_words if word.lower() not in stopwords
                ]
                home_team_stripped = " ".join(home_stripped_list)

                away_words = match["teams"][away].split()
                away_stripped_list = [
                    word for word in away_words if word.lower() not in stopwords
                ]
                away_team_stripped = " ".join(away_stripped_list)

                odds_game = home_team_stripped + " - " + away_team_stripped
                NT_game = heime_team_stripped + " - " + borte_team_stripped

                ratios = [
                    difflib.SequenceMatcher(
                        None, odds_game.lower(), NT_game.lower()
                    ).ratio(),
                    difflib.SequenceMatcher(
                        None, home_team_stripped.lower(), heime_team_stripped.lower()
                    ).ratio(),
                    difflib.SequenceMatcher(
                        None, away_team_stripped.lower(), borte_team_stripped.lower()
                    ).ratio(),
                ]
                ratio = statistics.mean(ratios)

                # odds_game = match["teams"][home] + " - " + match["teams"][away]
                # NT_game = heime + " - " + borte
                # ratios = [difflib.SequenceMatcher(None, odds_game.lower(), NT_game.lower()).ratio(),
                #                 difflib.SequenceMatcher(None, match["teams"][home].lower(), heime.lower()).ratio(),
                #                 difflib.SequenceMatcher(None, match["teams"][away].lower(), borte.lower()).ratio()]
                # ratio = statistics.mean(ratios)

                if ratio > 0.72:
                    # print(
                    #     f"Ratio: {ratio} for Odds game: {odds_game} and NT game: {NT_game}, add odds to dict!"
                    # )
                    for site in match["sites"]:
                        # TODO: Check if it is better to ust use Unibet and a couple other ones instead of all since that could be a source to wrong odds info..
                        # If there is no Odds entries in game at all, add empty keys that can be filled.
                        if "odds" not in game:
                            game["odds"] = {}
                            game["odds_original"] = {}
                            game["odds_diff"] = {}

                        if site["site_nice"] not in game["odds"]:
                            game["odds"][site["site_nice"]] = [
                                site["odds"]["h2h"][home],
                                site["odds"]["h2h"][2],
                                site["odds"]["h2h"][away],
                            ]
                            game["odds_original"][site["site_nice"]] = [
                                site["odds"]["h2h"][home],
                                site["odds"]["h2h"][2],
                                site["odds"]["h2h"][away],
                            ]
                            game["odds_diff"][site["site_nice"]] = [0, 0, 0]
                        else:
                            # print(f"Update odds for site: {site['site_nice']}")

                            game["odds"][site["site_nice"]] = [
                                site["odds"]["h2h"][home],
                                site["odds"]["h2h"][2],
                                site["odds"]["h2h"][away],
                            ]
                            game["odds_diff"][site["site_nice"]] = [
                                a_i - b_i
                                for a_i, b_i in zip(
                                    game["odds"][site["site_nice"]],
                                    game["odds_original"][site["site_nice"]],
                                )
                            ]

                        # print(
                        #     f'HUB: {site["odds"]["h2h"][home]} {site["odds"]["h2h"][2]} {site["odds"]["h2h"][away]}'
                        # )

                        # gameday_dict[gameDay]["games"][game]["diff"] = [a_i - b_i for a_i, b_i in zip(newGames[game]["dist"], gameday_dict[gameDay]["games"][game]["dist_original"])]
                        # gameday_dict[gameDay]["games"][game]["dist"] = newGames[game]["dist"]

                    # These values are better of in the actual front-end right? Better placed there such that missing values can be added similar as above
                    # Can then have a spinning script updating the values in the background depending on the updated values either from odds or the NT distributions
                    # pprint.pprint(game["odds"])
                    break  # Break if the correct match has been found.

    ######################################
    #   Store updated data
    ######################################
    db.storage.json.put("gameDayInfo.json", gameday_dict)


# def handle_betfair_odds():
#     import pandas as pd
#     import json
#     import pprint
#     import difflib
#     import statistics
#     import databutton as db

#     ######################################
#     #   Load frames
#     ######################################
#     gameday_dict = db.storage.json.get('gameDayInfo.json')

#     odds = db.storage.json.get('odds_events.json')

#     # Some chosen country name mappings where the norwegian names does NOT correspond with the english ones.
#     # TODO: Find something that is usable directly. Also move this to utils or something
#     country_mapping = {
#     "Frankrike" : "France",
#     "Østerrike" : "Austria",
#     "Kroatia" : "Croatia",
#     "Danmark" : "Denmark",
#     "Polen" : "Poland",
#     "Nederland": "Netherlands",
#     "Litauen" : "Lithuania",
#     "Færøyene" : "Faroe Islands",
#     "Aserbajdsjan" : "Azerbaijan",
#     "Tyskland" : "Germany",
#     "Ungarn" : "Hungary",
#     "Belgia" : "Belgium",
#     "Norge" : "Norway",
#     "Spania" : "Spain",
#     "Sveits" : "Switzerland",
#     "Tsjekkia" : "Czech Republic" ,
#     "Skottland" : "Scotland",
#     "Kypros" : "Cyprus",
#     "Hellas" : "Greece",
#     "Kasakhstan": "Kazakhstan",
#     "Tyrkia": "Turkey",
#     "Liechtenstein": "Liechtenstein",
#     "Ukraina" : "Ukraine",
#     "Irland" : "Republic of Ireland",
#     "Sverige": "Sweden"
#     }

#     # Add a list of stop words that makes it hard to connect NT team names to their respective full names..
#     stopwords = ["fc", "fk", "athletic", "city", "united", "bk", "hotspur", "albion", "milano"] # Will this actually help?

#     ######################################
#     #  Get closest game_day since that is the only one we care about atm
#     ######################################
#     closest_matchday = "MIDWEEK"
#     time_diff = 60*60*24*7
#     time_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
#     for game_day in gameday_dict:
#     difference = (parser.parse(gameday_dict[game_day]["saleStop"]) - time_now).total_seconds()
#     # print(f"time Diff: {difference}")
#     if difference < time_diff and parser.parse(gameday_dict[game_day]["saleStop"]) > time_now:
#         closest_matchday = game_day
#         time_diff = difference

#     ######################################
#     #   Update data json with new odds data.
#     ######################################
#     for gameName, game in gameday_dict[closest_matchday]["games"].items():

#     # Check if game is international, then change from Norwegian to english if necessary in order to pinpoint better the correct match!
#     ##### IF INTERNATIONAL GAME ##################
#     heime = game["home"]
#     borte = game["away"]
#     print(f"{heime} - {borte}")
#     if ("nations league" in game["arrangementName"].lower()) or ("mesterskap" in game["arrangementName"].lower()): #TODO: Check this for the World cup!
#         if (game["home"] in country_mapping):
#             heime = country_mapping[game["home"]]
#         if (game["away"] in country_mapping):
#             borte = country_mapping[game["away"]]
#     ###############################################

#     # Strip and refine NT game
#     heime_words = heime.split()
#     heime_stripped_list  = [word for word in heime_words if word.lower() not in stopwords]
#     heime_team_stripped = ' '.join(heime_stripped_list)

#     borte_words = borte.split()
#     borte_stripped_list  = [word for word in borte_words if word.lower() not in stopwords]
#     borte_team_stripped = ' '.join(borte_stripped_list)
#     NT_game = heime_team_stripped + " - " + borte_team_stripped

#     # Loop through the odds matches and try to find the correct fit (Norwegian to english if internationak games at least..)
#     for match in odds: # TODO: Refine this cuz now it sucks.

#         #Strip and refine odds game
#         home_words = odds[match]['home']['name'].split()
#         home_stripped_list  = [word for word in home_words if word.lower() not in stopwords]
#         home_team_stripped = ' '.join(home_stripped_list)

#         away_words = odds[match]['away']['name'].split()
#         away_stripped_list  = [word for word in away_words if word.lower() not in stopwords]
#         away_team_stripped = ' '.join(away_stripped_list)

#         odds_game = home_team_stripped + " - " + away_team_stripped

#         ratios = [difflib.SequenceMatcher(None, odds_game.lower(), NT_game.lower()).ratio(),
#                         difflib.SequenceMatcher(None, home_team_stripped.lower(), heime_team_stripped.lower()).ratio(),
#                         difflib.SequenceMatcher(None, away_team_stripped.lower(), borte_team_stripped.lower()).ratio()]
#         ratio = statistics.mean(ratios)

#         if (ratio > 0.65):
#             # print(f"Odds game: {odds_game} and NT game: {NT_game} with ratio: {ratio}")

#             if "odds" not in game:
#                 game["odds"] = [odds[match]['home']['odds'],odds[match]['draw']['odds'],odds[match]['away']['odds']]
#                 game["odds_original"] = [odds[match]['home']['odds'],odds[match]['draw']['odds'],odds[match]['away']['odds']]
#                 game["odds_diff"] = [0,0,0]

#             else:
#                 game["odds"] = [odds[match]['home']['odds'],odds[match]['draw']['odds'],odds[match]['away']['odds']]
#                 game["odds_diff"] = [a_i - b_i for a_i, b_i in zip(game["odds"], game["odds_original"])]

#             # These values are better of in the actual front-end right? Better placed there such that missing values can be added similar as above
#             # Can then have a spinning script updating the values in the background depending on the updated values either from odds or the NT distributions
#             # pprint.pprint(game["odds"])
#             break #Break if the correct match has been found.
#             # print("----")

#     ######################################
#     #   Save the updated data
#     ######################################
#     # pprint.pprint(gameday_dict)
#     ######################################
#     #   Store updated data
#     ######################################
#     db.storage.json.put('odds_events.json', event_dict)
