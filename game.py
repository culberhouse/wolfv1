import streamlit as st
from collections import defaultdict, deque
import random

# Define WolfGame class
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

        multiplier = {"team": 1, "solo_post": 2, "solo_pre": 3}[win_type]
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

# Streamlit app
st.set_page_config("Wolf Golf App")

if "game" not in st.session_state:
    st.session_state.game = None
if "submitted" not in st.session_state:
    st.session_state.submitted = False

if st.session_state.submitted:
    st.session_state.submitted = False
    st.experimental_rerun()
    st.session_state.submitted = False

st.title("🐺 Wolf Golf Score Tracker")

if st.session_state.game is None:
    st.header("Setup Game")
    num_players = st.selectbox("Number of players", [3, 4])
    player_names = [st.text_input(f"Player {i+1} name", key=f"name_{i}") for i in range(num_players)]
    if all(player_names):
        if st.button("Start Game"):
            st.session_state.game = WolfGame(player_names)
            st.success("Game started. Proceed to first hole.")
else:
    game = st.session_state.game
    st.subheader(f"Hole {game.current_hole}")
    wolf = game.get_wolf_for_hole(game.current_hole)
    st.markdown(f"**Wolf this hole:** {wolf}")
    tee_order = [game.rotation[(game.rotation.index(wolf) + i) % game.num_players] for i in range(game.num_players)]
    st.markdown("**Tee Order:** " + " → ".join(tee_order))

    win_type_label = st.radio("Wolf's Choice", ["Team Play", "Solo After Tee (2x)", "Solo Before Tee (3x)"])
    win_type = {"Team Play": "team", "Solo After Tee (2x)": "solo_post", "Solo Before Tee (3x)": "solo_pre"}[win_type_label]

    team = []
    if win_type == "team":
        partner_choices = [p for p in game.players if p != wolf]
        selected_partner = st.selectbox("Wolf Partner", ["None"] + partner_choices, key=f"partner_select_{game.current_hole}")
        if selected_partner != "None":
            team = [wolf, selected_partner]
        else:
            team = [p for p in game.players if p != wolf]
    else:
        team = [wolf]

    winner = st.radio("Who won the hole?", ["Wolf's Team", "Opponents", "Tie"], key=f"winner_select_{game.current_hole}")

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
        st.experimental_rerun()

    st.divider()
    st.subheader("Current Scores")
    for player, score in game.get_scores().items():
        st.write(f"{player}: {score} pts")

    st.divider()
    st.subheader("Hole History")
    for hole in game.get_hole_summary():
        st.markdown(f"Hole {hole['hole']}: {hole['result']} — {hole['points_awarded']} points")

