
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import random
import itertools

st.set_page_config(page_title="Crown Blackjack Simulator", layout="wide", initial_sidebar_state="expanded")

# === Styling ===
st.markdown("""
    <style>
        @media (max-width: 768px) {
            h1 { font-size: 1.5em; }
            .block-container {
                padding: 1rem 1rem;
            }
        }
        .stSlider > div[data-baseweb="slider"] {
            padding: 6px 0;
        }
    </style>
""", unsafe_allow_html=True)

# === Game Settings ===
NUM_DECKS = 8
RESHUFFLE_PENETRATION = 0.25  # reshuffle at 25% remaining
all_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
card_values = {r: min(10, int(r)) if r.isdigit() else 10 for r in all_ranks}
card_values['A'] = 11
hi_lo_values = {r: 1 for r in ['2', '3', '4', '5', '6']}
hi_lo_values.update({r: 0 for r in ['7', '8', '9']})
hi_lo_values.update({r: -1 for r in ['10', 'J', 'Q', 'K', 'A']})

# === Sidebar Inputs ===
game_variant = st.sidebar.selectbox("Game Variant", ["Crown Blackjack", "Blackjack Plus", "Free Bet Blackjack"])
strategy_mode = st.sidebar.radio("Strategy Mode", ["Perfect Basic Strategy", "Card Counting + Basic Strategy"])
initial_bankroll = st.sidebar.number_input("Initial Bankroll ($)", 100, 1000000, 100000, step=100)
min_bet = st.sidebar.number_input("Minimum Bet ($)", 10, 500, 100, step=10)
num_simulations = st.sidebar.slider("Number of Simulations", 1, 500, 100)
num_hands = st.sidebar.slider("Hands per Simulation", 100, 10000, 2000, step=100)

# === Variant-Specific Rules ===
rules = {
    "Crown Blackjack": {
        "blackjack_payout": 1.5,
        "dealer_hits_soft_17": True,
        "dealer_push_22": False,
        "free_doubles": False,
        "five_card_charlie": False,
        "counting_allowed": strategy_mode == "Card Counting + Basic Strategy"
    },
    "Blackjack Plus": {
        "blackjack_payout": 1.2,
        "dealer_hits_soft_17": True,
        "dealer_push_22": True,
        "free_doubles": False,
        "five_card_charlie": True,
        "counting_allowed": False
    },
    "Free Bet Blackjack": {
        "blackjack_payout": 1.5,
        "dealer_hits_soft_17": True,
        "dealer_push_22": True,
        "free_doubles": True,
        "five_card_charlie": False,
        "counting_allowed": False
    }
}
current_rules = rules[game_variant]

# === Helper Functions ===
def create_shoe():
    return all_ranks * 4 * NUM_DECKS

def hand_value(hand):
    val = sum(card_values[c] for c in hand)
    aces = hand.count('A')
    while val > 21 and aces:
        val -= 10
        aces -= 1
    return val

def is_soft(hand):
    return 'A' in hand and hand_value(hand) <= 21 and hand_value(hand) != sum(card_values[c] for c in hand)

def dealer_play(dealer, deck):
    while True:
        val = hand_value(dealer)
        if val > 21: return dealer
        if val > 17: return dealer
        if val == 17 and is_soft(dealer) and current_rules['dealer_hits_soft_17']:
            dealer.append(deck.pop())
        elif val < 17:
            dealer.append(deck.pop())
        else:
            return dealer

def basic_strategy(player, dealer_upcard, can_double):
    total = hand_value(player)
    if len(player) == 2 and can_double and total in [9, 10, 11]:
        return "double"
    if total >= 17:
        return "stand"
    if 13 <= total <= 16:
        if dealer_upcard in ['2', '3', '4', '5', '6']:
            return "stand"
        return "hit"
    if total == 12:
        if dealer_upcard in ['4', '5', '6']:
            return "stand"
        return "hit"
    return "hit"

def simulate_hand(deck, true_count, bankroll):
    running_count = 0
    bet = min_bet

    # Card Counting Betting Logic
    if current_rules["counting_allowed"]:
        if true_count >= 1:
            bet *= min(true_count, 10)
    bet = min(bankroll, bet)

    # Deal
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]
    dealer_up = dealer[0]

    # Count updates
    running_count += sum(hi_lo_values[c] for c in player + dealer)

    # Check for blackjacks
    if hand_value(player) == 21 and len(player) == 2:
        if hand_value(dealer) == 21 and len(dealer) == 2:
            return bankroll, running_count  # push
        return bankroll + bet * current_rules["blackjack_payout"], running_count

    if hand_value(dealer) == 21 and len(dealer) == 2:
        return bankroll - bet, running_count

    # Player actions
    action = basic_strategy(player, dealer_up, can_double=True)
    if action == "double":
        second_card = deck.pop()
        player.append(second_card)
        bet = min(bankroll, bet * 2)
    else:
        while action == "hit":
            player.append(deck.pop())
            if hand_value(player) > 21:
                return bankroll - bet, running_count
            action = basic_strategy(player, dealer_up, can_double=False)

    # Dealer actions
    dealer = dealer_play(dealer, deck)

    # Five-card Charlie
    if current_rules["five_card_charlie"] and len(player) >= 5 and hand_value(player) <= 21:
        return bankroll + bet, running_count

    dealer_val = hand_value(dealer)
    player_val = hand_value(player)

    if dealer_val > 21:
        return bankroll + bet, running_count
    if current_rules["dealer_push_22"] and dealer_val == 22:
        return bankroll, running_count
    if player_val > dealer_val:
        return bankroll + bet, running_count
    if player_val < dealer_val:
        return bankroll - bet, running_count
    return bankroll, running_count

# === Simulate ===
results = []
true_count_history = []

with st.spinner("Simulating hands..."):
    for _ in range(num_simulations):
        shoe = create_shoe()
        random.shuffle(shoe)
        bankroll = initial_bankroll
        running_count = 0
        simulation_result = []
        tc_history = []

        for h in range(num_hands):
            if len(shoe) < len(create_shoe()) * RESHUFFLE_PENETRATION:
                shoe = create_shoe()
                random.shuffle(shoe)
                running_count = 0

            decks_remaining = len(shoe) / 52
            true_count = running_count / decks_remaining if decks_remaining > 0 else 0
            tc_history.append(true_count)

            bankroll, delta_count = simulate_hand(shoe, true_count, bankroll)
            running_count += delta_count
            simulation_result.append(bankroll)
            if bankroll <= 0:
                break

        results.append(simulation_result)
        true_count_history.append(tc_history)

# === Pad Results ===
max_len = max(len(r) for r in results)
padded_results = [r + [r[-1]] * (max_len - len(r)) for r in results]
padded_tc = [t + [t[-1]] * (max_len - len(t)) for t in true_count_history]
array_results = np.array(padded_results)
array_tc = np.array(padded_tc)

avg_bankroll = np.mean(array_results, axis=0)
avg_tc = np.mean(array_tc, axis=0)
final_bankrolls = array_results[:, -1]

roi = ((final_bankrolls.mean() - initial_bankroll) / initial_bankroll) * 100
ev_per_hand = (final_bankrolls.mean() - initial_bankroll) / num_hands
std_dev = np.std(final_bankrolls)
sharpe_ratio = roi / (std_dev / initial_bankroll) if std_dev != 0 else 0
risk_of_ruin = np.mean(final_bankrolls <= 0) * 100

# === Metrics Display ===
st.title("🎯 Simulation Results")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Final Avg Bankroll", f"${final_bankrolls.mean():,.0f}")
col2.metric("ROI", f"{roi:.2f}%")
col3.metric("EV/Hand", f"${ev_per_hand:.2f}")
col4.metric("Sharpe Ratio", f"{sharpe_ratio:.4f}")

col5, col6 = st.columns(2)
col5.metric("Risk of Ruin", f"{risk_of_ruin:.2f}%")
col6.metric("Best Outcome", f"${np.max(final_bankrolls):,.0f}")

# === Plots ===
st.subheader("📉 Bankroll Over Time")
fig = go.Figure()
for i in range(min(10, len(array_results))):
    fig.add_trace(go.Scatter(y=array_results[i], mode="lines", line=dict(width=1), name=f"Sim {i+1}"))
fig.add_trace(go.Scatter(y=avg_bankroll, mode="lines", line=dict(width=4), name="Average", line_color="deepskyblue"))
fig.update_layout(template="plotly_dark", height=500)
st.plotly_chart(fig, use_container_width=True)

st.subheader("📈 True Count Over Time")
fig2 = go.Figure()
fig2.add_trace(go.Scatter(y=avg_tc, mode="lines", line=dict(color="orange", width=3)))
fig2.update_layout(template="plotly_dark", height=500)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("🏁 Final Bankroll Distribution")
fig3 = go.Figure()
fig3.add_trace(go.Histogram(x=final_bankrolls, nbinsx=40, marker_color="green"))
fig3.update_layout(template="plotly_dark", height=500)
st.plotly_chart(fig3, use_container_width=True)
