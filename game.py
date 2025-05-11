import os
import pickle

import streamlit as st
import random
from collections import deque, defaultdict

# Wolf game logic
class WolfGame:
    def __init__(self, players):
        self.players = players
        self.num_players = len(players)
        self.rotation = self.generate_wolf_rotation()
        self.scores = defaultdict(int)
        self.hole_results = []
        self.current_hole = 1
        self.carry_over_points = 0

    def generate_wolf_rotation(self):
        shuffled = self.players[:]
        random.shuffle(shuffled)
        rotation = deque(shuffled)
        order = []
        for _ in range(len(shuffled)):
            order.append(rotation[0])
            rotation.rotate(-1)
        return order

    def get_wolf_for_hole(self, hole):
        index = (hole - 1) % self.num_players
        return self.rotation[index]

    def record_hole(self, wolf, team, win_type, is_tie):
        if is_tie:
            self.carry_over_points += 1
            self.hole_results.append({
                'hole': self.current_hole,
                'wolf': wolf,
                'result': 'Tie (No Blood)',
                'points_awarded': 0,
                'carry_over': self.carry_over_points
            })
            return

        multiplier = 1
        if win_type == "solo_pre":
            multiplier = 3
        elif win_type == "solo_post":
            multiplier = 2

        total_points = (self.carry_over_points + 1) * multiplier
        for player in team:
            self.scores[player] += total_points

        self.hole_results.append({
            'hole': self.current_hole,
            'wolf': wolf,
            'result': f"{' + '.join(team)} won ({win_type})",
            'points_awarded': total_points,
            'carry_over': self.carry_over_points
        })

        self.carry_over_points = 0

    def advance_hole(self):
        self.current_hole += 1

    def get_scores(self):
        return dict(self.scores)

    def get_hole_summary(self):
        return self.hole_results

# Streamlit UI
st.set_page_config(page_title="Wolf Golf Score Tracker", layout="centered")


if "game" not in st.session_state:
    st.session_state.game = None

if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Load game if saved
if st.session_state.game is None and os.path.exists("game_state.pkl"):
    with open("game_state.pkl", "rb") as f:
        st.session_state.game = pickle.load(f)

    st.session_state.submitted = False

    st.session_state.game = None

st.title("🐺 Wolf Golf Score Tracker")

# Load game if saved
    with open("game_state.pkl", "rb") as f:
        st.session_state.game = pickle.load(f)

if st.session_state.game is None:
    st.header("Setup Game")
    num_players = st.selectbox("Number of players", [3, 4])
    player_names = []

    for i in range(num_players):
        name = st.text_input(f"Player {i + 1} name", key=f"name_{i}")
        player_names.append(name)

    if all(player_names):
        if st.button("Start Game"):
            st.session_state.game = WolfGame(player_names)
            st.success("Game started. You can begin entering hole results.")
            st.stop()

else:
    game = st.session_state.game
    st.subheader(f"Hole {game.current_hole}")
    wolf = game.get_wolf_for_hole(game.current_hole)
    st.markdown(f"**Wolf this hole:** {wolf}")

    solo_type = st.radio("Did the Wolf go solo?", ["None", "Before Tee Shot (3x)", "After Tee Shot (2x)"])
    win_type = {
        "None": "team",
        "Before Tee Shot (3x)": "solo_pre",
        "After Tee Shot (2x)": "solo_post"
    }[solo_type]

    if win_type == "team":
        partner = st.selectbox("Select partner (optional)", ["None"] + [p for p in game.players if p != wolf])
        if partner != "None":
            team = [wolf, partner]
        else:
            team = [p for p in game.players if p != wolf]
    else:
        team = [wolf]

    winner = st.radio("Who won the hole?", ["Wolf's Team", "Opponents", "Tie"])


    if st.button("Submit Hole Result"):
        if winner == "Tie":
            game.record_hole(wolf, [], win_type, is_tie=True)
        elif winner == "Wolf's Team":
            game.record_hole(wolf, team, win_type, is_tie=False)
        else:
            opponents = [p for p in game.players if p not in team]
            game.record_hole(wolf, opponents, "team", is_tie=False)

        game.advance_hole()
        st.session_state.submitted = True
        with open("game_state.pkl", "wb") as f:
            pickle.dump(game, f)
        st.experimental_rerun()
