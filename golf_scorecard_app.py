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

# --- Load persistent data ---
golf_data = load_data()
today = str(date.today())
if today not in golf_data:
    golf_data[today] = {}

# --- Title ---
st.title("🏌️‍♂️ Golf Scorecard — Table Input Version")
st.markdown("""
Track your golf rounds more easily by entering **all scores in one table**.  
Supports 1–4 players and stores daily rounds automatically for 365 days.
""")

# --- Player Setup ---
if "setup_done" not in st.session_state:
    st.session_state.setup_done = False

if not st.session_state.setup_done:
    st.header("👥 Player Setup")
    num_players = st.number_input("Number of Players (1–4):", min_value=1, max_value=4, step=1)
    player_names = []
    for i in range(num_players):
        player_names.append(st.text_input(f"Enter name for Player {i+1}:", key=f"player_{i}"))

    if st.button("Start Round"):
        if all(player_names):
            st.session_state.players = player_names
            st.session_state.setup_done = True
            st.success("✅ Players set! Enter scores in the table below.")
        else:
            st.error("Please fill all player names before starting.")
else:
    players = st.session_state.players
    total_holes = 18

    st.header(f"📋 Enter Scores for {today}")

    # --- Create editable score table ---
    columns = ["Hole", "Par"] + players
    holes = [f"Hole {i+1}" for i in range(total_holes)]
    df_template = pd.DataFrame(columns=columns)
    df_template["Hole"] = holes
    df_template["Par"] = [4] * total_holes  # default par 4

    # --- Editable DataFrame ---
    edited_df = st.data_editor(
        df_template,
        use_container_width=True,
        num_rows="fixed",
        key="score_editor",
        hide_index=True,
    )

    # --- Save Button ---
    if st.button("💾 Save Scores"):
        try:
            # Validate entries
            edited_df["Par"] = edited_df["Par"].astype(int)
            for player in players:
                edited_df[player] = edited_df[player].astype(int)

            # Calculate totals
            total_scores = {player: edited_df[player].sum() for player in players}
            total_par = edited_df["Par"].sum()
            to_par = {p: total_scores[p] - total_par for p in players}

            # Save in persistent JSON
            golf_data[today] = {
                "players": players,
                "scores": edited_df.to_dict(),
                "total_scores": total_scores,
                "to_par": to_par,
            }
            save_data(golf_data)

            # Display Results
            st.success("✅ Scores saved successfully!")
            st.subheader("🏁 Final Results")
            st.dataframe(edited_df)

            # Display Totals and To-Par
            results_df = pd.DataFrame({
                "Total Strokes": [total_scores[p] for p in players],
                "To Par": [f"{'+' if to_par[p] > 0 else ''}{to_par[p]}" if to_par[p] != 0 else "E" for p in players]
            }, index=players)
            st.table(results_df)

            # Show Winner
            winner = min(total_scores, key=total_scores.get)
            st.success(f"🏆 Winner: **{winner}** with {total_scores[winner]} strokes ({'+' if to_par[winner] > 0 else ''}{to_par[winner]} to par)")

        except Exception as e:
            st.error(f"Error saving scores: {e}")

    # --- View 365-Day History ---
    if st.button("📜 View 365-Day History"):
        st.subheader("📅 Saved Rounds (Past 365 Days)")
        if golf_data:
            for day, data in golf_data.items():
                st.markdown(f"### 📆 {day}")
                if "scores" in data:
                    hist_df = pd.DataFrame(data["scores"])
                    st.dataframe(hist_df)
                    st.write("**Total Scores:**", data.get("total_scores", {}))
                    st.write("**To Par:**", data.get("to_par", {}))
        else:
            st.info("No past rounds found yet.")

    # --- Reset Round ---
    if st.button("🔄 Reset Round"):
        st.session_state.clear()
        st.experimental_rerun()
