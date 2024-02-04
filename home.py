# import databutton as db 
import pandas as pd
import streamlit as st

pd.set_option("display.precision", 2)
pd.options.display.float_format = "{:,.2f}".format
# pd.set_option("display.nan_repr", "None")
import datetime
import json
import os

# import matplotlib
import requests
from dateutil import parser
import pickle

# TODO: Remove these imports
# from handle import handle_the_odds
from update import update_df_obj
from utils import bookies, highlight_row_equalto


# @st.cache_resource
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

abs_path = os.path.abspath(__file__) + "/data/"


##### Get active GD #####
# stored_obj = db.storage.binary.get("active-gd-pkl")
# gd = pickle.loads(stored_obj)
        
gd = get_pickled_obj(abs_path+"active-gd.pkl")

# stored_obj = db.storage.binary.get("gds-pkl")
# gds = pickle.loads(stored_obj)
gds = get_pickled_obj(abs_path+"gds.pkl")

##### Get old GDS #####
try:
    # with open(pickle_file_path, "rb") as file:
    #    gd = pickle.load(file)
    # stored_obj = db.storage.binary.get("old-gds-pkl")
    # oldGDS = pickle.loads(stored_obj)
    oldGDS = get_pickled_obj(abs_path+"old-gds.pkl")

except FileNotFoundError:
    print("File does not exist.")
    oldGDS = {}
    # activeGD = {} # db.storage.json.get("gameDayInfo.json")
except pickle.PickleError as e:
    print(f"An error occurred with the pickle file: {e}")

# Could be better to add a sidebar like this maybe?
# st.sidebar.title("NT distribution")
# option = st.sidebar.selectbox(label="Choose game day", options=["monday","tuesday"])

# Update df on opening of the page
update_df_obj()

# Options is either to have tabs like this or use a sidebar with everything tied to that one.. However, I do think that that option is to be used more for widgets and so on..
nextGameWeekTab, nextGameWeekProblemTab, historyTab = st.tabs(
    ["Next Gameday", "Fix/report gameday", "History"]
)
with nextGameWeekTab:
    ##### GAMEDAY INFO
    st.title(f"Tipping info for {gd.day_str}")
    st.subheader(
        "This page shows the implied value of the upcoming 'Tipping' event aka 'Tolvarenj'"
    )
    st.write(f"Sale Amount: {gd.sale_amount_full}")
    try:
        bonus = gd.bonus
    except:
        bonus = 0
    st.write(f"Bonus: ca. {bonus}")

    # df = db.storage.dataframes.get("MATCHDAY_DF_obj" )  # This should be redone to just get the upcoming matchday DF
    df = pd.read_pickle(abs_path+'MATCHDAY_DF.pkl')

    df1 = df[["GameNr", "Game", "H_valu", "U_valu", "B_valu"]]
    df1 = df1.set_index("GameNr")
    df1.sort_index(inplace=True)
    # Show dataframe
    st.subheader("Value dataframe")
    df1 = df1.style.background_gradient(
        cmap="RdYlGn",
        low=0,
        high=0,
        axis=1,
        subset=["H_valu", "U_valu", "B_valu"],
        text_color_threshold=0.408,
        vmin=-20,
        vmax=20,
        gmap=None,
    )  # .set_precision(2)
    df1 = df1.format(precision=2)
    st.dataframe(
        df1, 900, 455
    )  # Add styling for better visualization later on (df.style.highlight_min(color = 'red', axis = 1).highlight_max(color = 'lightgreen', axis = 1))
    st.button("UPDATE", on_click=update_df_obj())

    st.subheader("Odds and value df:")
    df2 = df[
        [
            "GameNr",
            "Game",
            "tip",
            "H_folk",
            "U_folk",
            "B_folk",
            "H_mean",
            "U_mean",
            "B_mean",
            "H_valu",
            "U_valu",
            "B_valu",
        ]
    ]
    df2 = df2.set_index("GameNr")
    df2.sort_index(inplace=True)

    df2 = (
        df2.style.background_gradient(
            cmap="RdYlGn_r",
            axis=1,
            low=0,
            high=0,
            # vmin=1,
            # vmax=20,
            subset=["H_mean", "U_mean", "B_mean"],
        )
        .background_gradient(
            cmap="RdYlGn",
            axis=1,
            low=0,
            high=0,
            vmin=-20,
            vmax=20,
            subset=["H_valu", "U_valu", "B_valu"],
        )
        .apply(highlight_row_equalto, value="-", column=["tip"], axis=1)
        # .set_precision(2)
    )
    df2 = df2.format(precision=2)
    st.dataframe(df2, 900, 455)

    # Show all data at the bottom of the page:
    st.markdown("ALL DATA:")
    df = df.set_index("GameNr")
    df.sort_index(inplace=True)
    # df = df.format(precision=2)
    # df = df.style.set_precision(2)
    st.dataframe(df, 900, 455)
    st.markdown(
        "Disclaimer: Use at your own risk. This is by no means betting advice and we cannot be held responsible for any losses or gains ;)"
    )

with nextGameWeekProblemTab:
    # Add input field to add odds to matches
    st.markdown("Add odds for new matches below.")
    # df = db.storage.dataframes.get("MATCHDAY_DF_obj")
    df = pd.read_pickle(abs_path+'MATCHDAY_DF.pkl')

    # TODO: Remove bookies and shit, should be just one!!
    bookies = bookies()
    bookie = st.selectbox(label="Choose bookie", options=bookies)
    match = st.selectbox(label="Choose match", options=df["Game"].tolist())
    # numberH = st.slider("Odds H",0.0,15.0)
    # numberU = st.slider("Odds U",0.0,15.0)
    # numberB = st.slider("Odds B",0.0,15.0)
    numberH = st.number_input("Odds H", min_value=0.0, max_value=20.0, step=0.01)
    numberU = st.number_input("Odds U", min_value=0.0, max_value=20.0, step=0.01)
    numberB = st.number_input("Odds B", min_value=0.0, max_value=20.0, step=0.01)

    odds = [numberH, numberU, numberB]

    if st.button("Submit odds"):
        # Stupiditycheck to see if no changes have been done to the odds.
        if all(
            i >= 1 for i in odds
        ):  # TODO: Add check to see if odds is vastly different from already available odds, for now we just trust anyone with the link :P
            # Try updating the odds dataframe
            # gd.games.game
            chosen_game = gd.games[match]
            chosen_game.update_odds(odds)

            st.write("Thank you for the odds data and for improving this service.")
            st.write("Data will be updated shortly.")

            ######################################
            #   Store updated data
            ######################################
            # db.storage.json.put("gameDayInfo.json", gameday_dict)
            # pickled = pickle.dumps(gd)
            # db.storage.binary.put("active-gd-pkl", pickled)
            store_pickled_obj(abs_path+"active-gd.pkl")

            # This might not be necessary. Could do this in the NT instead such that it is faster?
            # Either way, it is REALLY important such that odds info does not disappappear:P
            gds[gd.day_str] = gd
            # pickled = pickle.dumps(gds)
            # db.storage.binary.put("gds-pkl", pickled)
            store_pickled_obj(abs_path+"gds.pkl")

            # for idx, game in gd.games.items():
            #    # print(f"Game: {idx} and odds: {game.odds}")
            #    st.write(f"Game: {idx} and odds: {game.odds}")
            update_df_obj()
        else:
            st.write("Please fill in a decent odds")

    # if st.button("Submit odds and remove other"):
    #    st.write("OK")

with historyTab:
    # st.markdown("##### Add history here..")
    columns = [
        "GameNr",
        "Game",
        "tip",
        "outcome",
        "H_valu",
        "U_valu",
        "B_valu",
        "result",
        "H_folk",
        "U_folk",
        "B_folk",
        "H_odds",
        "U_odds",
        "B_odds",
        "Adj_valu",
        "Win_odds",
        "Win_dist"
    ]
    adj_valu_total = 0
    outcome_mapping = {"HOME": "H", "AWAY": "B", "DRAW": "U"}
    if len(oldGDS) < 1:
        st.write("No old GW's yet")
    else:
        selected_old_gd_name = st.selectbox(
            label="Choose Gameday", options=oldGDS.keys()
        )
        # st.write("Load and display old gameweeks with results etc")
        # for gamedayname, gameday in oldGDS.items():
        old_gd = oldGDS[selected_old_gd_name]
        st.write(f"Gameday: {old_gd.day_str}")

        # st.write(
        #    f"Sale amount: {old_gd.sale_amount_full} vs payout: {old_gd.payout_total_full}, so a ratio of: {old_gd.payout_total_full/old_gd.sale_amount_full*100}"
        # )

        data = []  # [[0] * len(columns)] * len(old_gd.games.keys())
        # Init datafram variables to zero.
        for gameName, game in old_gd.games.items():
            # st.write(
            #    f"{game.game_nr} : {gameName}, Value: {((1/game.odds[0])-game.dist[0]/100)*100} {((1/game.odds[1])-game.dist[1]/100)*100} {((1/game.odds[2])-game.dist[2]/100)*100} result: {game.result} {game.outcome}"
            # )

            h_odds = (
                game.odds[0] if game.odds != None else 1
            )  # if len(game.odds) != 0 else 1
            h_imp = (1 / h_odds) * 100
            u_odds = game.odds[1] if game.odds != None else 1
            u_imp = (1 / u_odds) * 100
            b_odds = game.odds[2] if game.odds != None else 1
            b_imp = (1 / b_odds) * 100

            # Get values:
            h_valu = h_imp - game.dist[0] if h_imp != 100 else 1
            u_valu = u_imp - game.dist[1] if u_imp != 100 else 1
            b_valu = b_imp - game.dist[2] if h_imp != 100 else 1

            # Calculate tip TODO: This was just something quick and dirty :P This should be properly defined in a formula ;)
            if b_valu >= 10 and b_odds <= 3:
                tip = "B"
            elif u_valu >= 10 and u_odds <= 3.65:
                tip = "U"
            elif h_valu >= 10 and h_odds <= 3:
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

            outcome = outcome_mapping.get(game.outcome)
            adj_valu = 0
            win_odds = 1
            win_dist = 100
            if game.outcome == "HOME": 
                adj_valu = h_valu/h_odds #((1/h_odds)*100)
                win_odds = h_odds
                win_dist = game.dist[0]
            elif game.outcome == "AWAY": 
                adj_valu = b_valu/b_odds
                win_odds = b_odds
                win_dist = game.dist[2]
            else:
                adj_valu = u_valu/u_odds
                win_odds = u_odds
                win_dist = game.dist[1]
            data.append(
                [
                    game.game_nr,
                    game.game_str,
                    tip,
                    outcome,
                    h_valu,
                    u_valu,
                    b_valu,
                    game.result,
                    game.dist[0],
                    game.dist[1],
                    game.dist[2],
                    h_odds,
                    u_odds,
                    b_odds,
                    adj_valu,
                    win_odds,
                    win_dist
                ]
            )
    df = pd.DataFrame(data=data, columns=columns).round(2)
    df = df.set_index("GameNr")
    df.sort_index(inplace=True)
    st.dataframe(df)

    st.write(
        f"Dag: {old_gd.day_str}  \nBonus: {old_gd.bonus}  \n Omsetning fulltid: {old_gd.sale_amount_full}  \nUtbetaling fulltid: {old_gd.payout_total_full}  \nOmsetning pause: {old_gd.sale_amount_half}  \nUtbetaling pause: {old_gd.payout_total_half}\n"
    )

    # st.json(old_gd.to_dict())
    data2 = [
        [
            12,
            old_gd.prizes_fulltime["twelve"]["numberOfWinners"],
            old_gd.prizes_fulltime["twelve"]["amount"],
            old_gd.prizes_fulltime["twelve"]["total"],
        ],
        [
            11,
            old_gd.prizes_fulltime["eleven"]["numberOfWinners"],
            old_gd.prizes_fulltime["eleven"]["amount"],
            old_gd.prizes_fulltime["eleven"]["total"],
        ],
        [
            10,
            old_gd.prizes_fulltime["ten"]["numberOfWinners"],
            old_gd.prizes_fulltime["ten"]["amount"],
            old_gd.prizes_fulltime["ten"]["total"],
        ],
    ]
    df2 = pd.DataFrame(
        data=data2, columns=["Riktige", "Vinnere", "Utbetaling", "Total"]
    )
    st.dataframe(df2)
    utbet_diff = old_gd.sale_amount_full - old_gd.payout_total_full
    utbet_prosent = old_gd.payout_total_full/old_gd.sale_amount_full*100
    st.write(
        f"Utbetaling total: {old_gd.payout_total_full} vs Omsetning: {old_gd.sale_amount_full}  \nDiff: {utbet_diff} => {utbet_prosent}% payout"
    )
    if utbet_prosent >= 55:
        st.write("Bonuspott popped!")

    # st.download_button(label="Download pickled old gameday data",
    #                   data = gds,# This might be wrong and should probably be on a binary format, so pickled.
    #                   file_name="oldGDS.pkl",
    #                   mime="application/octet-stream")
