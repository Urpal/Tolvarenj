# import databutton as db

import datetime
from dateutil import parser

import json
import re

import pandas as pd
import requests
# from bs4 import BeautifulSoup as bs
# import beautifulSoup as bs

import pickle

from classes.utils import Gameday, Game, country_mapping, stopwords, NT_to_theOdds_mapping
import os
import difflib
import statistics


# data_folder = os.path.join(os.path.dirname(__file__), "..", "data")
# os.makedirs(data_folder, exist_ok=True)
# pickle_file_path = os.path.join(data_folder, 'saved_data.pkl')


def get_nt():
    # Try getting the info directly through the API instead of using the JS based HTML
    url = (
        "https://api.norsk-tipping.no/SportGameInfo/v1/api/tipping/gameinfo?gameDay=ALL"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    }
    r = requests.get(url, headers=headers)
    data = json.loads(r.text)
    # print(data)

    ######################################
    #   Load dynamic game day dict
    ######################################
    # Reload the pickled file and unpickle the dictionary
    # pickle_file_path = os.path.join(data_folder, "GDS.pkl")
    try:
        # with open(pickle_file_path, "rb") as file:
        #    gameday_dict = pickle.load(file)
        gds_obj = db.storage.binary.get("gds-pkl")
        gameday_dict = pickle.loads(gds_obj)
        print("Successfully loaded GD dict")
    except FileNotFoundError:
        print("File does not exist.")
        gameday_dict = {}  # db.storage.json.get("gameDayInfo.json")
    except pickle.PickleError as e:
        print(f"An error occurred with the pickle file: {e}")

    # print("TEST")
    # tgd = gameday_dict["MIDWEEK"]
    # gaymes = tgd.games
    # for idx, game in gaymes.items():
    #    print(game.odds)

    # Returns a list of the three game days
    sports_data_list = data["gameList"]
    for game_day in sports_data_list:
        # Initiate gameday object
        gd = Gameday(day_str=game_day["gameDay"], day_nr=game_day["gameDayNo"])

        # Use the saleStop information as a trigger to check if there is any data available for the gameday
        try:
            # saleStop = game_day["betObject"]["saleStop"]
            gd.sale_stop = game_day["betObject"]["saleStop"]
        except KeyError as e:
            # Catch the error and just break the for loop for this day, hence keeping the old information.
            print(f"There is no data for day: {game_day['gameDay']}")
            break

        # Set current sale amounts etc for the gameday
        gd.sale_amount_half = game_day["betObject"]["saleAmount"]["halfTime"]
        gd.sale_amount_full = game_day["betObject"]["saleAmount"]["fullTime"]
        try:
            gd.bonus = game_day["bonusPot"][0]
        except:
            gd.bonus = "No bonus found."
        # TODO: Add jackpot ??

        # Get betting distribution for each game, does not matter if the games are new or old.
        # TODO: What happens if this is empty? Will it throw an error?
        for dists in game_day["betObject"]["tips"]["fullTime"]:
            if dists["tipType"] == "PEOPLE":
                people_tip_dict = dists["distribution"]
        # This could be accessed directly by game_day["betObject"]["tips"]["fullTime"]["tiptype"] == "PEOPLE"

        # Get games of for the GD
        newGames = {}
        game_counter = 1
        for event in game_day["betObject"]["events"]:
            # cet_timezone = pytz.timezone('Europe/Paris')  # CET timezone
            # parsed_date_cet = parsed_date.replace(tzinfo=pytz.utc).astimezone(cet_timezone)

            # Check game time and add the latest starting game to the gameday
            if gd.last_game_time == None:
                gd.last_game_time = event["eventTime"]
            else:
                latest_game_time = max(
                    [
                        datetime.datetime.strptime(
                            gd.last_game_time, "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        datetime.datetime.strptime(
                            event["eventTime"], "%Y-%m-%dT%H:%M:%SZ"
                        ),
                    ]
                )
                if latest_game_time == datetime.datetime.strptime(
                    event["eventTime"], "%Y-%m-%dT%H:%M:%SZ"
                ):
                    gd.last_game_time = event["eventTime"]

            # Create Game object for each game
            game = Game(
                game_nr=event["eventNo"],
                game_str=event["eventName"],
                arrangement_name=event["arrangementName"],
                home_team=event["teamNames"]["home"]["name"],
                away_team=event["teamNames"]["away"]["name"],
                event_time=event["eventTime"],
                sport_name=event["sportName"],
                dist=people_tip_dict[str(game_counter)],
                dist_diff=[0, 0, 0],
                dist_original=people_tip_dict[str(game_counter)],
                # odds=[],
                # odds_original=[],
                # odds_diff=[],
                status=event["matchStatus"]["statusForClient"],
            )
            newGames[event["eventName"]] = game
            game_counter += 1

        # Insert the games into this gameday
        gd.games = newGames

        # Check if gameday is already inside of dictionary
        if gd.day_str in gameday_dict:
            # print(f"GD {gd.day_str} is already in dictionary")
            # Gameday already in dictionary, get original gameday and games
            original_gd = gameday_dict[gd.day_str]
            original_games = original_gd.games

            # If the sale stop time is equal for this day vs the new gd, then update the data
            if gd.sale_stop == original_gd.sale_stop:
                # print("Salestop is the same. Keep old but update distributions")
                # print("Sale stop is the same, hence update only the distributions.")
                for idx, game in newGames.items():
                    # Could this whole thing be done all together directly? Something like:
                    # selected_new_game = game
                    # print(f"Old game odds: {original_games[idx].odds}")
                    # selected_old_game = original_games[idx]
                    # print(f"New game odds: {game.odds}")
                    original_games[idx].update(game)

                    ## Update distributions
                    # selected_old_game.update(selected_new_game)
                    # original_games[game] = selected_old_game

                gd.games = original_games
                # print("Overwrite gdd with new gd but original games")
                gameday_dict[gd.day_str] = gd

            # If sale stop is different, then this is actually a new gameday
            else:
                # print(
                #     "Sale stop is actually new, save old gameweek and insert the new one!"
                # )
                # Save the old GD temporarily until results can be retrieved
                oldGD = original_gd
                # pickle_file_path = os.path.join(data_folder, "oldGD.pkl")
                ## TODO: Do I need to read and check if it already exist here?
                # with open(pickle_file_path, "wb") as file:
                #    pickle.dump(oldGD, file)
                pickled = pickle.dumps(oldGD)
                db.storage.binary.put("old-gd-pkl", pickled)

                # Place new GD into GDS
                gameday_dict[gd.day_str] = gd
        # If gameday (i.e. wednesday, saturday or sunday) is not in dictionary at all, then add the GD. This is basically just run the first time this code is running.
        else:
            gameday_dict[gd.day_str] = gd

    #### Save the gamedays ####
    # pickle_file_path = os.path.join(data_folder, "GDS.pkl")
    # with open(pickle_file_path, "wb") as file:
    #    pickle.dump(gameday_dict, file)
    pickled = pickle.dumps(gameday_dict)
    db.storage.binary.put("gds-pkl", pickled)

    # Get a proper JSON object to save it as json for readability!
    gd_dict = {}
    for key, gd in gameday_dict.items():
        gd_dict[key] = gd.to_dict()
    db.storage.json.put("gds.json", gd_dict)

    #  Get closest game_day to todays date to update the active GD which is used in the front end.
    closest_matchday = "MIDWEEK"
    time_diff = 60 * 60 * 24 * 7
    time_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    for game_day, game in gameday_dict.items():
        difference = (
            parser.parse(gameday_dict[game_day].sale_stop) - time_now
        ).total_seconds()
        if (
            difference < time_diff
            and parser.parse(gameday_dict[game_day].sale_stop) > time_now
        ):
            closest_matchday = game_day
            time_diff = difference

    # print("Closest matchday set as the active GD")
    # print(gameday_dict[closest_matchday])
    activeGD = gameday_dict[closest_matchday]
    # pickle_file_path = os.path.join(data_folder, "activeGD.pkl")
    ## TODO: Do I need to read and check if it already exist here?
    # with open(pickle_file_path, "wb") as file:
    #    pickle.dump(
    #        activeGD, file
    #    )  # I guess it does not make sense to update this one every time this is triggered or what? The distributions should normally be updated though!
    pickled = pickle.dumps(activeGD)
    db.storage.binary.put("active-gd-pkl", pickled)
    db.storage.json.put("active-gd.json", activeGD.to_dict())


def get_the_odds():
    ######################################
    #   Load active
    ######################################
    # pickle_file_path = os.path.join(data_folder, "activeGD.pkl")
    try:
        # with open(pickle_file_path, "rb") as file:
        #    gd = pickle.load(file)
        activegd_obj = db.storage.binary.get("active-gd-pkl")
        gd = pickle.loads(activegd_obj)
    except FileNotFoundError:
        print("File does not exist.")
        gd = Gameday()
        # activeGD = {} # db.storage.json.get("gameDayInfo.json")
    except pickle.PickleError as e:
        print(f"An error occurred with the pickle file: {e}")

    ######################################
    #   Check if it is time to get new odds data:
    ######################################
    # Hardcoded update times. This script should only run 12, 3, 1 and 0.5 hours before the deadline.
    time_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    # gd_key = next(iter(activeGD))
    # gd = activeGD[gd_key]
    time_diff = (parser.parse(gd.sale_stop) - time_now).total_seconds()
    print(f"Time difference: {time_diff}\n")

    #### This should be moved to main where all times should be checked in order to check if we want to get the odds or not.
    accepted_time_diffs = [
        20 * 60 * 60,
        7.5 * 60 * 60,
        3 * 60 * 60,
        1 * 60 * 60,
        0.5 * 60 * 60,
    ]
    get_data = False
    interval = 29 * 60  # 29 minutes
    for t in accepted_time_diffs:
        # Check if the time difference from the closest gameday is within the threshold
        if t - interval / 2 <= time_diff <= t + interval / 2:
            get_data = True

    # If the time is right, update odds data!
    if get_data:
        ######################################
        #   API Call info
        ######################################
        API_KEY = db.secrets.get("THE_ODDS_API_KEY")
        # 'upcoming' # use the sport_key from the /sports endpoint below, or use 'upcoming' to see the next 8 games across all sports
        # SPORT = "soccer_uefa_nations_league"
        REGION = "uk"  # uk | us | eu | au
        MARKET = "h2h"  # h2h | spreads | totals
        # 10 bookies to get the mean of, might as well just do 2 one but hey, why not if it "costs" the same :P
        BOOKMAKERS = [
            "nordicbet",
            "pinnacle",
            "williamhill",
            "sport888",
            "unibet",
            "betfair",
            "marathonbet",
            "betclic",
            "paddypower",
            "skybet",
        ]

        # days = ["MIDWEEK", "SATURDAY", "SUNDAY"]
        ######################################
        #   Get NT Arrangement keys and map to available markets in the odds API.
        ######################################
        # # Check if NT arrangement key values can be found in the mapping and then set up the odds query.
        # test_list_keys = ["UEFA Nations League, A, Gr. 4", "UEFA Nations League, A, Gr. 1", "UEFA Nations League, A, Gr. 3", "UEFA Nations League, A, Gr. 2", "Norsk Tipping-ligaen avd1", "Norsk Tipping-ligaen avd3", "Norsk Tipping-ligaen avd5", "NOR PostNord-ligaen 2", "Toppserien, Women"]
        # TODO: Get this list of keys from the different gameweek days. Maybe also add timing such that the odds will only be checked from a couple days before the gameday?
        accepted_keys = []
        cl_value = NT_to_theOdds_mapping["champions league"]
        for game_name, game in gd.games.items():
            # Add check for champions league? This is NOT the best way lol
            if (
                "champ. league" in game.arrangement_name.lower()
                and cl_value not in accepted_keys
            ):
                accepted_keys.append(cl_value)
            else:
                for key, value in NT_to_theOdds_mapping.items():
                    if (
                        key in game.arrangement_name.lower()
                        and value not in accepted_keys
                    ):
                        accepted_keys.append(value)
        print(accepted_keys)

        ######################################
        #   Get Odds data from the mapped keys list before mapping these to the matches themselves.
        ######################################
        odds_data = []
        api_tries = 5

        for the_odds_sport_key in accepted_keys:
            # Add while loop to test this for 2-3 times before breaking and moving on?
            api_try = 1
            odds_data_received = False

            while not odds_data_received and api_try < api_tries:
                # Get response
                odds_response = requests.get(
                    "https://api.the-odds-api.com/v3/odds",
                    params={
                        "api_key": API_KEY,
                        "sport": the_odds_sport_key,  # SPORT,
                        "region": REGION,
                        "mkt": MARKET,
                        "bookmakers": BOOKMAKERS,
                    },
                )
                # print(f"Status code: {odds_response.status_code}")

                if odds_response.status_code == 200:
                    try:
                        odds_json = json.loads(odds_response.text)
                        # Appending the odds data for the different keys to a list that can later be looped when searching for the available odds.
                        odds_data.append(odds_json["data"])
                        print(
                            "\nRemaining requests",
                            odds_response.headers["x-requests-remaining"],
                        )
                        print("Used requests", odds_response.headers["x-requests-used"])
                        odds_data_received = True
                    except KeyError:
                        print(
                            f"No data received in OK response... Try again. This is try nr: {api_try} \n"
                        )
                        api_try += 1
                else:
                    print(
                        f"Response for request not satisfactory. Try again. This is try nr: {api_try} \n"
                    )
                    api_try += 1

            if api_tries == api_try:
                print(
                    f"Not able to get data for key: {the_odds_sport_key} after {api_try} api calls...\n"
                )
            else:
                print("Successfully received data! \n")

                # TODO: Add e-mailing service to notify when there is not many requests left.

        ######################################
        #   Store updated data
        ######################################

        # db.storage.json.put("odds.json", odds_data)
        # pickle_file_path = os.path.join(data_folder, "odds.pkl")
        ## TODO: Do I need to read and check if it already exist here?
        # with open(pickle_file_path, "wb") as file:
        #    pickle.dump(odds_data, file)
        pickled = pickle.dumps(odds_data)
        db.storage.binary.put("odds-pkl", pickled)
        db.storage.json.put("odds_obj.json", odds_data)

        # Trigger handle odds since it is new?
        handle_the_odds(gd, odds_data)
    else:
        print("Not time for getting odds data atm...")


def handle_the_odds(
    gd: Gameday, odds
):  # Need to type check the odds and or restructure the odds data maybe :P stupid the way it is as of now.
    # Get Master data, the gameday dictionary such that the odds will also be updated for this data
    # Maybe it is not really worth it to have the active dataframe really?
    try:
        # with open(pickle_file_path, "rb") as file:
        #    gameday_dict = pickle.load(file)
        gds_obj = db.storage.binary.get("gds-pkl")
        gameday_dict = pickle.loads(gds_obj)
        print("Successfully loaded GD dict")
    except FileNotFoundError:
        print("File does not exist.")
        gameday_dict = {}  # db.storage.json.get("gameDayInfo.json")
    except pickle.PickleError as e:
        print(f"An error occurred with the pickle file: {e}")

    # Get updated odds
    # pickle_file_path = os.path.join(data_folder, "odds.pkl")
    ## TODO: Do I need to read and check if it already exist here?
    # with open(pickle_file_path, "rb") as file:
    #    odds = pickle.load(file)

    # print(f"Handle the odds with odds array as: {odds}")

    # Check odds data if we should continue or throw an error or something
    odds_entries = sum(len(sublist) for sublist in odds)
    if not odds_entries > 1:
        print(
            f"There is no available odds atm. Something went wrong.. number of odds endtries are: {odds_entries}"
        )
        return

    ######################################
    #   Update data json with new odds data.
    ######################################
    # for gameName, game in gameday_dict[closest_matchday]["games"].items():
    for gameName, game in gd.games.items():
        game_found = False
        # Check if game is international, then change from Norwegian to english if necessary in order to pinpoint better the correct match!
        ##### IF INTERNATIONAL GAME ##################
        heime = game.home_team
        borte = game.away_team
        # TODO: Check this for the World cup!
        if (
            ("nations league" in game.arrangement_name.lower())
            or ("mesterskap" in game.arrangement_name.lower())
            or ("vm" in game.arrangement_name.lower())
        ):
            if game.home_team in country_mapping:
                heime = country_mapping[game.home_team]
            if game.away_team in country_mapping:
                borte = country_mapping[game.away_team]
        ###############################################

        # Loop through the odds matches and try to find the correct fit (Norwegian to english if internationak games at least..)
        for market in odds:
            # Variable for breaking out of "markets" if game has been found. Just to get rid of multiple matches found to be correct in different markets.
            if game_found:
                break
            # Ranked list of trusted bookies to be used to choose the one available with the highest priority. Lowest number has higher priority.
            trusted_site_nice_dict = {
                "Betfair": 1,
                "Betway": 3,
                "Unibet": 2,
            }  #  ["Betfair", "Betway", "Unibet"]
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

                if ratio > 0.75:
                    chosen_bookie = ""
                    bookie_rank = 0
                    bookie_idx = 0
                    for idx, bookie in enumerate(match["sites"]):
                        if bookie["site_nice"] in trusted_site_nice_dict.keys():
                            # Get the one with the highest priority
                            if chosen_bookie == "":
                                chosen_bookie = bookie["site_nice"]
                                bookie_rank = trusted_site_nice_dict[
                                    bookie["site_nice"]
                                ]
                                bookie_idx = idx
                            else:
                                if (
                                    trusted_site_nice_dict[bookie["site_nice"]]
                                    < bookie_rank
                                ):
                                    chosen_bookie = bookie["site_nice"]
                                    bookie_rank = trusted_site_nice_dict[
                                        bookie["site_nice"]
                                    ]
                                    bookie_idx = idx

                    # Try to update the odds of the game
                    try:
                        # print(
                        #    f"Updating odds! {match['sites'][bookie_idx]['odds']['h2h']}"
                        # )
                        game.update_odds(
                            [
                                match["sites"][bookie_idx]["odds"]["h2h"][home],
                                match["sites"][bookie_idx]["odds"]["h2h"][2],
                                match["sites"][bookie_idx]["odds"]["h2h"][away],
                            ]
                        )
                    except TypeError:
                        print("Invalid input! Odds must be a List of 3 ints..")
                    chosen_odds = match["sites"][bookie_idx]["odds"]["h2h"]
                    print(
                        f"Chosen bookie: {chosen_bookie} with rank: {bookie_rank} and odds: {chosen_odds} for game NT: {NT_game}, Odds: {odds_game} with a similarity of: {ratio}"
                    )
                    game_found = True  # Set game found to true. Ideally, the diff-checker should be more strict...
                    break

    ######################################
    #   Store updated data
    ######################################
    # db.storage.json.put("gameDayInfo.json", gameday_dict)
    # pickle_file_path = os.path.join(data_folder, "activeGD.pkl")
    # with open(pickle_file_path, "wb") as file:
    #    pickle.dump(gd, file)
    pickled = pickle.dumps(gd)
    db.storage.binary.put("active-gd-pkl", pickled)
    db.storage.json.put("active-gd.json", gd.to_dict())

    # NB: Need to also update the BASIS of the whole update cycle ofc. Otherwise, I'll keep resetting the odds every time the NT is run since that is the "basis" of the update cycle and the master data manager in gds
    gameday_dict[gd.day_str] = gd
    pickled = pickle.dumps(gameday_dict)
    db.storage.binary.put("gds-pkl", pickled)


def get_results():
    ######################################
    #   Load the old gameday and the dictionary of legacy gamedays
    ######################################
    # pickle_file_path = os.path.join(data_folder, "oldGD.pkl")
    try:
        # with open(pickle_file_path, "rb") as file:
        # gd = pickle.load(file)
        oldgd_obj = db.storage.binary.get("old-gd-pkl")
        gd = pickle.loads(oldgd_obj)
        print(f"Old GameDay retrieved for day: {gd.day_str}")
        if gd.day_str == None:
            print("Gameday is empty. Return! ")
            return
    except FileNotFoundError:
        print("\nFile does not exist, please run this after the GD is complete.")
        # gd = Gameday()
        return
    except pickle.PickleError as e:
        print(f"An error occurred with the pickle file: {e}")

    # Check if it is actual time to get the results and so on. Should be done 3 hours after the last game time, at least. Maybe 6 hours just to be sure.
    time_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    time_diff = (time_now - parser.parse(gd.last_game_time)).total_seconds()
    hours = 5
    if not (time_diff > hours * 60 * 60):
        print(
            f"Time difference: {time_diff} whereas the delay for getting the results (in seconds) is: {hours*60*60}"
        )
        return

    print("Time to get results for old gameday.")
    # pickle_file_path = os.path.join(data_folder, "oldGDS.pkl")
    try:
        # with open(pickle_file_path, "rb") as file:
        #    oldGDS = pickle.load(file)
        oldgds_obj = db.storage.binary.get("old-gds-pkl")
        oldGDS = pickle.loads(oldgds_obj)
        print("Old gameday dictionary retrieved.")
    except FileNotFoundError:
        print(
            "File does not exist. Create new empty dictionary to fill in old gamedays with results."
        )
        oldGDS = {}
    except pickle.PickleError as e:
        print(f"An error occurred with the pickle file: {e}")

    ######################################
    #   Get NT results data
    ######################################
    print("Get NT results for latest GD...")
    url = f"https://api.norsk-tipping.no/SportGameInfo/v1/api/tipping/results"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    }
    r = requests.get(url, headers=headers)
    data = json.loads(r.text)
    # print(data)

    # Extract data from NT
    results_data = data["game"]
    # gd_nr = results_data["gameDayNo"]
    gd_name = results_data["gameDay"]

    # Get overall bet objects
    bet_object = results_data["betObject"]

    # Get info about this round
    sale_stop = bet_object["saleStop"]
    # sale_amount_half = bet_object["saleAmount"]["halfTime"]
    prices_halfTime = bet_object["prizes"]["halfTime"][
        "prizeDetails"
    ]  # returning a dict of ten, eleven and twelve with amount and numberOfWinners described.

    # sale_amount_full = bet_object["saleAmount"]["fullTime"]
    prices_fullTime = bet_object["prizes"]["fullTime"][
        "prizeDetails"
    ]  # returning a dict of ten, eleven and twelve with amount and numberOfWinners described.

    # Check if correct gd and then fill info:
    if gd_name != gd.day_str and sale_stop != gd.sale_stop:
        print("Something wrong with results and latest gameday. Return!")
        return

    gd.prizes_fulltime = prices_fullTime
    gd.prizes_halftime = prices_halfTime

    gd.compute_total_payout()
    # Get actual games (or events)
    event_list = bet_object["events"]

    # counter = 0 #Use counter since this should always be structured from 0-11 (or G1 to G12)
    for event in event_list:
        game = gd.games[event["eventName"]]
        try:
            game.result = event["result"]["fullTime"]["score"]
        except KeyError:
            game.result = "x-x"
        game.outcome = event["result"]["fullTime"]["outcome"]
        game.status = event["matchStatus"]["statusForClient"]  # Update status for game

    # Get tips # [0]['distribution'] is people and [1]['distribution'] are experts returning a list of lists
    # tips_half = bet_object["tips"]["halfTime"]
    # tips_full = bet_object["tips"]["fullTime"]

    # Get the actual results of the last day, check if it is the correct date and update???

    print("Insert GD into GDD")
    oldGDS[gd.day_str + "_" + gd.last_game_time] = gd
    # pickle_file_path = os.path.join(data_folder, "oldGDS.pkl")
    # with open(pickle_file_path, "wb") as file:
    #    pickle.dump(oldGDS, file)
    pickled = pickle.dumps(oldGDS)
    print("Save old GD into GDD pickle and its own json for debugging.")
    db.storage.binary.put("old-gds-pkl", pickled)
    db.storage.json.put("previous-old-gd.json", gd.to_dict())

    # Also update the overall json file for the old gamedays, will be removed once everything works as expected.
    print("Save old GDD as json for debugging.")
    gd_dict = {}
    for key, gd in oldGDS.items():
        gd_dict[key] = gd.to_dict()
    db.storage.json.put("old-gds.json", gd_dict)

    # Overwrite the old gameday such that it will be empty for the nest trigger.
    print("Insert empty old GD into pickle.")
    empty_gd = Gameday()
    # pickle_file_path = os.path.join(data_folder, "oldGD.pkl")
    # with open(pickle_file_path, "wb") as file:
    #    pickle.dump(empty_gd, file)
    pickled = pickle.dumps(empty_gd)
    db.storage.binary.put("old-gd-pkl", pickled)
    db.storage.json.put("test-old-gd.json", empty_gd.to_dict())
