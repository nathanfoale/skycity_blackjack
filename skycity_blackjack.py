import streamlit as st
import numpy as np
import plotly.graph_objects as go
import random
from collections import deque

st.set_page_config(
    page_title="SkyCity Blackjack Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.expander("📜 SkyCity Blackjack Rules (Summary)", expanded=False):
    st.markdown("""
    **Game Rules for SkyCity Blackjack (as of 2025):**

    - **Decks Used**: 6 standard decks, reshuffled after each round.
    - **Dealer Hits Soft 17**: Yes
    - **Blackjack Payout**: 3 to 2
    - **Doubling Down**: Allowed only on hard 9, 10, or 11
    - **Double After Split (DAS)**: Allowed
    - **Splits**: Unlimited splits allowed except Aces
    - **Split Aces**: One split allowed; only one card dealt per Ace
    - **Blackjack on Split Aces**: Not allowed
    - **Surrender**: Not available
    - **Insurance**: Available when dealer shows an Ace (pays 2:1)
    - **Push on Dealer 22**: No — dealer busts on 22
    - **Continuous Shuffling Machine (CSM)**: All cards are returned to the deck after each round
    """)

# Constants
NUM_DECKS = 6
BLACKJACK_PAYOUT = 1.5
MIN_BET = 25

CARD_VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
               '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}

def deal_card(deck):
    return deck.pop() if deck else random.choice(list(CARD_VALUES.keys()))

def hand_value(hand):
    value = sum(CARD_VALUES[card] for card in hand)
    aces = hand.count('A')
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

def is_blackjack(hand):
    return len(hand) == 2 and hand_value(hand) == 21

def play_dealer_hand(deck, hand):
    while hand_value(hand) < 17 or (hand_value(hand) == 17 and 'A' in hand and sum(CARD_VALUES[c] for c in hand) > 17):
        hand.append(deal_card(deck))
    return hand

def basic_strategy(player_hand, dealer_card):
    value = hand_value(player_hand)
    if value <= 11:
        return 'hit'
    if 12 <= value <= 16:
        if dealer_card in ['2', '3', '4', '5', '6']:
            return 'stand'
        else:
            return 'hit'
    return 'stand'

# Sidebar parameters
initial_bankroll = st.sidebar.number_input("Initial Bankroll ($)", 1000, 1000000, 100000, step=1000)
num_simulations = st.sidebar.slider("Number of Simulations", 1, 500, 100)
num_hands = st.sidebar.slider("Hands per Simulation", 100, 10000, 2000, step=100)

# Simulate one full session
all_cards = list(CARD_VALUES.keys()) * 4 * NUM_DECKS

def simulate_single_run():
    bankroll = initial_bankroll
    bankrolls = []

    for _ in range(num_hands):
        deck = all_cards.copy()
        random.shuffle(deck)

        if bankroll < MIN_BET:
            bankrolls.append(bankroll)
            break

        bet = MIN_BET
        player = [deal_card(deck), deal_card(deck)]
        dealer = [deal_card(deck), deal_card(deck)]

        # Check for natural blackjack
        if is_blackjack(player):
            if is_blackjack(dealer):
                outcome = 'push'
            else:
                outcome = 'blackjack'
        elif is_blackjack(dealer):
            outcome = 'lose'
        else:
            # Player hits according to basic strategy
            while basic_strategy(player, dealer[0]) == 'hit':
                player.append(deal_card(deck))
                if hand_value(player) > 21:
                    break

            # Evaluate outcome
            player_score = hand_value(player)
            if player_score > 21:
                outcome = 'lose'
            else:
                dealer = play_dealer_hand(deck, dealer)
                dealer_score = hand_value(dealer)
                if dealer_score > 21:
                    outcome = 'win'
                elif dealer_score > player_score:
                    outcome = 'lose'
                elif dealer_score < player_score:
                    outcome = 'win'
                else:
                    outcome = 'push'

        if outcome == 'blackjack':
            bankroll += bet * BLACKJACK_PAYOUT
        elif outcome == 'win':
            bankroll += bet
        elif outcome == 'lose':
            bankroll -= bet

        bankrolls.append(bankroll)

    return bankrolls

# Run Simulations
with st.spinner("Simulating SkyCity Blackjack hands..."):
    all_results = [simulate_single_run() for _ in range(num_simulations)]

max_length = max(len(r) for r in all_results)
padded_results = [r + [r[-1]] * (max_length - len(r)) for r in all_results]
array_results = np.array(padded_results)
avg_bankroll = np.mean(array_results, axis=0)
final_bankrolls = array_results[:, -1]

roi = ((final_bankrolls.mean() - initial_bankroll) / initial_bankroll) * 100
std_dev = np.std(final_bankrolls)
sharpe_ratio = roi / (std_dev / initial_bankroll) if std_dev > 0 else 0
max_gain = np.max(final_bankrolls) - initial_bankroll
max_loss = initial_bankroll - np.min(final_bankrolls)
ev_per_hand = (final_bankrolls.mean() - initial_bankroll) / num_hands
risk_of_ruin = np.mean(final_bankrolls <= 0) * 100

# Display Results
st.subheader("📊 Simulation Results")
col1, col2, col3, col4 = st.columns(4)
col1.metric("💸 Final Avg Bankroll", f"${final_bankrolls.mean():,.0f}")
col2.metric("📉 Std Dev", f"${std_dev:,.0f}")
col3.metric("📈 ROI", f"{roi:.2f}%")
col4.metric("📐 Sharpe Ratio", f"{sharpe_ratio:.4f}")
col5, col6, col7, col8 = st.columns(4)
col5.metric("🧮 EV per Hand", f"${ev_per_hand:.2f}")
col6.metric("🏆 Best Outcome", f"${max_gain:,.0f}")
col7.metric("💀 Worst Outcome", f"-${max_loss:,.0f}")
col8.metric("⚠️ Risk of Ruin", f"{risk_of_ruin:.2f}%")

# Plot animated bankroll over time
st.subheader("📈 Animated Bankroll Growth")
num_to_animate = min(10, len(array_results))
frames = []
colors = ["rgba(255,99,132,0.2)", "rgba(54,162,235,0.2)", "rgba(255,206,86,0.2)",
          "rgba(75,192,192,0.2)", "rgba(153,102,255,0.2)", "rgba(255,159,64,0.2)"]

for k in range(1, len(avg_bankroll), 10):
    frame_data = []
    for i in range(num_to_animate):
        frame_data.append(go.Scatter(
            y=array_results[i][:k+1],
            mode='lines',
            line=dict(width=1.5, color=colors[i % len(colors)]),
            showlegend=False,
            hoverinfo='skip'))
    frame_data.append(go.Scatter(
        y=avg_bankroll[:k+1],
        mode='lines',
        name='Average Bankroll',
        line=dict(color='deepskyblue', width=4),
        hoverinfo='skip'))
    frame_data.append(go.Scatter(
        y=[initial_bankroll] * (k+1),
        mode='lines',
        name='Initial Bankroll',
        line=dict(dash='dash', color='gray'),
        hoverinfo='skip'))
    frames.append(go.Frame(data=frame_data, name=str(k)))

init_data = []
for i in range(num_to_animate):
    init_data.append(go.Scatter(
        y=[array_results[i][0]],
        mode='lines',
        line=dict(width=1, color='rgba(255,255,255,0.08)'),
        showlegend=False,
        hoverinfo='skip'))
init_data.append(go.Scatter(
    y=[avg_bankroll[0]],
    mode='lines',
    name='Average Bankroll',
    line=dict(color='deepskyblue', width=4)))
init_data.append(go.Scatter(
    y=[initial_bankroll],
    mode='lines',
    name='Initial Bankroll',
    line=dict(dash='dash', color='gray')))

animated_fig = go.Figure(
    data=init_data,
    layout=go.Layout(
        title={
            'text': "🃏 SkyCity Blackjack Simulation\n<sup>(Basic Strategy, CSM, Flat Bet)</sup>",
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=30)
        },
        xaxis=dict(title="Hands Played", range=[0, len(avg_bankroll)]),
        yaxis=dict(title="Bankroll ($)", range=[min(avg_bankroll)*0.95, max(avg_bankroll)*1.5]),
        template='plotly_dark',
        height=700,
        hovermode='x unified',
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            buttons=[
                dict(label="Play", method="animate", args=[None, {"frame": {"duration": 25, "redraw": True}, "fromcurrent": True}]),
                dict(label="Pause", method="animate", args=[[None], {"frame": {"duration": 0}, "mode": "immediate"}])
            ],
            x=0.1, y=1.15, xanchor="left", yanchor="top")]
    ),
    frames=frames
)
st.plotly_chart(animated_fig, use_container_width=True)

# Histogram
st.subheader("📉 Distribution of Final Bankrolls")
hist_fig = go.Figure()
hist_fig.add_trace(go.Histogram(x=final_bankrolls, nbinsx=40, marker_color='green'))
hist_fig.update_layout(bargap=0.1, xaxis_title="Final Bankroll", yaxis_title="Frequency", height=600)
st.plotly_chart(hist_fig, use_container_width=True)
