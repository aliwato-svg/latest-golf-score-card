import streamlit as st
import pandas as pd
import json
import os
from datetime import date

st.set_page_config(page_title="Golf Scorecard", page_icon="⛳", layout="centered")

DATA_FILE = "golf_scores.json"

# --- Helper Functions ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Load or initialize persistent data ---
golf_data = load_data()

# Keep a dictionary for each date for 365 days
today = str(date.today())
if today not in golf_data:
    golf_data[today] = {}

# --- Title and Intro ---
st.title("🏌️‍♂️ Annual Golf Score Tracker")
st.markdown("""
Track your golf rounds day-by-day for up to 365 days!  
Start fresh each day, record hole-by-hole scores, and keep track of all rounds easily.
""")

# --- Setup players ---
if "setup_done" not in st.session_state:
    st.session_state.setup_done = False

if not st.session_state.setup_done:
    st.header("👥 Player Setup")
    num_players = st.number_input("Enter number of players (1–4):", min_value=1, max_value=4, step=1)
    player_names = []
    for i in range(num_players):
        player_names.append(st.text_input(f"Enter name for Player {i+1}:", key=f"p{i}"))

    if st.button("Start Round"):
        if all(player_names):
            st.session_state.players = player_names
            st.session_state.scores = {player: [None] * 18 for player in player_names}
            st.session_state.pars = [None] * 18
            st.session_state.played_holes = set()
            st.session_state.setup_done = True
            st.success("✅ Players set! Start recording holes below.")
        else:
            st.error("Please enter all player names before continuing.")
else:
    st.header(f"🎯 Scoring for {today}")
    players = st.session_state.players

    hole = st.number_input("Enter Hole Number (1–18):", min_value=1, max_value=18, step=1)
    par = st.selectbox("Enter Par for this hole:", [3, 4, 5])

    st.write("### Enter Strokes per Player")
    hole_scores = {}
    cols = st.columns(len(players))
    for i, player in enumerate(players):
        with cols[i]:
            hole_scores[player] = st.number_input(f"{player}", min_value=1, max_value=15, step=1, key=f"{player}_{hole}")

    if st.button("💾 Record This Hole"):
        for player in players:
            st.session_state.scores[player][hole - 1] = hole_scores[player]
        st.session_state.pars[hole - 1] = par
        st.session_state.played_holes.add(hole)
        st.success(f"Hole {hole} recorded successfully!")

        # Save to persistent data
        golf_data[today] = {
            "players": players,
            "scores": st.session_state.scores,
            "pars": st.session_state.pars
        }
        save_data(golf_data)

    # --- Display live table ---
    if st.session_state.played_holes:
        st.divider()
        st.subheader("📊 Live Scoreboard")

        played = sorted(list(st.session_state.played_holes))
        df = pd.DataFrame({
            player: [st.session_state.scores[player][i - 1] for i in played]
            for player in players
        }, index=[f"Hole {i} (Par {st.session_state.pars[i - 1]})" for i in played])
        df.loc["Total"] = df.sum()

        # Calculate “To Par”
        par_total = sum([st.session_state.pars[i - 1] for i in played if st.session_state.pars[i - 1] is not None])
        to_par = {player: df.loc["Total", player] - par_total for player in players}

        st.dataframe(df.style.format(na_rep="—").set_properties(**{"text-align": "center"}))

        st.write("### 🧮 Player To-Par Stats")
        to_par_df = pd.DataFrame({
            "Score (To Par)": [f"{'+' if to_par[p] > 0 else ''}{to_par[p]}" if to_par[p] != 0 else "E" for p in players]
        }, index=players)
        st.table(to_par_df)

    # --- Reset and History ---
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset Round"):
            st.session_state.clear()
            st.experimental_rerun()
    with col2:
        if st.button("📜 View 365-Day History"):
            st.session_state.view_history = True

# --- 365-Day History ---
if "view_history" in st.session_state and st.session_state.view_history:
    st.subheader("📅 365-Day Golf Log")
    if golf_data:
        for day, info in golf_data.items():
            st.write(f"### 📆 {day}")
            if "players" in info and "scores" in info:
                df_hist = pd.DataFrame(info["scores"])
                df_hist.index = [f"Hole {i+1}" for i in range(18)]
                df_hist.loc["Total"] = df_hist.sum()
                st.dataframe(df_hist)
            else:
                st.write("_No data for this day yet._")
    else:
        st.info("No past data found yet. Play a round to start tracking!")
