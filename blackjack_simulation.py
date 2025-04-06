import streamlit as st
import numpy as np
import plotly.graph_objects as go
import random

st.set_page_config(
    page_title="Crown Blackjack Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.expander("📜 Crown Melbourne Blackjack Rules (Summary)", expanded=False):
    st.markdown("""
    **Game Rules for Crown Melbourne Blackjack (as of March 2024):**
    
    - **Decks Used**: 8 standard decks (52 cards each, no jokers).
    - **Dealer Hits Soft 17**: Yes, the dealer hits on soft 17.
    - **Blackjack Payout**: 3 to 2.
    - **Doubling Down**: Only allowed on hard 9, 10, or 11.
    - **Splits**: Up to 3 hands allowed (no resplitting Aces).
    - **Split Aces**: One card only dealt to each Ace; no Blackjack possible on split Aces.
    - **Surrender**: Not available in standard Crown Blackjack.
    - **Insurance**: Available when dealer shows an Ace (pays 2:1).
    - **Push on Dealer 22**: No — dealer busts on 22.
    - **Continuous Shuffling**: Cards reshuffled when low; continuous shuffle machine may be used.

    For full official rules, see the [Crown Melbourne Blackjack Rules PDF](https://www.crownmelbourne.com.au/getmedia/05258b9f-3cb3-4b2e-a9b2-9e309e56f70c/Blackjack-Rules-March-2024).
    """)


# Crown Blackjack Rules
NUM_DECKS = 8
BLACKJACK_PAYOUT = 1.5
H17 = True
OBBO = True
DAS = True
SPLITS_ALLOWED = 3
DOUBLE_ON = [9, 10, 11]
RSA = False
LATE_SURRENDER = False

# Sidebar Parameters
initial_bankroll = st.sidebar.number_input("Initial Bankroll ($)", 1000, 1000000, 100000, step=1000)
min_bet = st.sidebar.number_input("Minimum Bet ($)", 10, 500, 100, step=10)
spread = st.sidebar.slider("Bet Spread (Hi-Lo Count Multiplier)", 1, 20, 10)
num_simulations = st.sidebar.slider("Number of Simulations", 1, 500, 100)
num_hands = st.sidebar.slider("Hands per Simulation", 100, 10000, 2000, step=100)

# Card Values
card_values = {
    '2': 1, '3': 1, '4': 1, '5': 1, '6': 1,
    '7': 0, '8': 0, '9': 0,
    '10': -1, 'J': -1, 'Q': -1, 'K': -1, 'A': -1
}
all_cards = list(card_values.keys()) * 4 * NUM_DECKS

def get_true_count(running_count, decks_remaining):
    return running_count / decks_remaining if decks_remaining > 0 else 0

def simulate_single_run():
    deck = all_cards.copy()
    random.shuffle(deck)
    running_count = 0
    bankroll = initial_bankroll
    bankrolls = []
    true_counts = []

    for _ in range(num_hands):
        if len(deck) < 52:
            deck = all_cards.copy()
            random.shuffle(deck)
            running_count = 0

        card = deck.pop()
        running_count += card_values[card]
        decks_remaining = len(deck) / 52
        true_count = round(get_true_count(running_count, decks_remaining))
        true_counts.append(true_count)

        # Bet sizing
        bet = min_bet
        if true_count > 1:
            bet *= min(spread, true_count)
        bet = min(bankroll, bet)

        # Simulate double/split hands
        double_down = np.random.rand() < 0.10
        splittable = np.random.rand() < 0.05
        if double_down or splittable:
            bet = min(bankroll, bet * 2)

        # Count 10s and Aces left for blackjack probability
        tens_left = sum(deck.count(x) for x in ['10', 'J', 'Q', 'K'])
        aces_left = deck.count('A')
        bj_prob = (tens_left / len(deck)) * (aces_left / len(deck)) * 2

        # Win/Loss probabilities
        edge = 0.005 + (0.005 * true_count)
        win_prob = min(0.44 + edge, 0.52)
        lose_prob = max(0.44 - edge, 0.36)
        push_prob = 1.0 - win_prob - lose_prob
        probs = np.array([win_prob, lose_prob, push_prob])
        probs = probs / probs.sum()
        win_prob, lose_prob, push_prob = probs

        outcome = np.random.choice(["win", "lose", "push"], p=[win_prob, lose_prob, push_prob])
        if outcome == "win":
            if np.random.rand() < bj_prob:
                bankroll += bet * BLACKJACK_PAYOUT
            else:
                bankroll += bet
        elif outcome == "lose":
            bankroll -= bet

        bankrolls.append(bankroll)
        if bankroll <= 0:
            break

    return bankrolls, true_counts

# === Run Simulations ===
with st.spinner("Simulating Crown Blackjack hands..."):
    all_results = []
    all_true_counts = []
    for _ in range(num_simulations):
        result, true_count_run = simulate_single_run()
        all_results.append(result)
        all_true_counts.append(true_count_run)

max_length = max(len(r) for r in all_results)
padded_results = [r + [r[-1]] * (max_length - len(r)) for r in all_results]
padded_true_counts = [r + [r[-1]] * (max_length - len(r)) for r in all_true_counts]
array_results = np.array(padded_results)
array_true_counts = np.array(padded_true_counts)

avg_bankroll = np.mean(array_results, axis=0)
avg_true_counts = np.mean(array_true_counts, axis=0)
final_bankrolls = array_results[:, -1]
roi = ((final_bankrolls.mean() - initial_bankroll) / initial_bankroll) * 100
risk_of_ruin = np.mean(final_bankrolls <= 0) * 100
std_dev = np.std(final_bankrolls)
std_dev_pct = (std_dev / initial_bankroll) * 100
sharpe_ratio = roi / std_dev_pct if std_dev_pct != 0 else 0
# === Additional Calculations ===
max_gain = np.max(final_bankrolls) - initial_bankroll
max_loss = initial_bankroll - np.min(final_bankrolls)
ev_per_hand = (final_bankrolls.mean() - initial_bankroll) / num_hands

# === Animated Bankroll Growth: Average + Sim Paths ===
num_to_animate = 10  # number of sim lines to animate
frames = []

# Create frames for animation
for k in range(1, len(avg_bankroll), 10):

    frame_data = []

    # Sim paths
    # Use brighter, more varied colors
    colors = [
        "rgba(255,99,132,0.2)", "rgba(54,162,235,0.2)", "rgba(255,206,86,0.2)",
        "rgba(75,192,192,0.2)", "rgba(153,102,255,0.2)", "rgba(255,159,64,0.2)"
    ]
    for i in range(num_to_animate):
        frame_data.append(go.Scatter(
            y=array_results[i][:k+1],
            mode='lines',
            line=dict(width=1.5, color=colors[i % len(colors)]),
            showlegend=False,
            hoverinfo='skip'
    ))


    # Average line
    frame_data.append(go.Scatter(
        y=avg_bankroll[:k+1],
        mode='lines',
        name='Average Bankroll',
        line=dict(color='deepskyblue', width=4),
        hoverinfo='skip'
    ))

    # Initial bankroll reference
    frame_data.append(go.Scatter(
        y=[initial_bankroll] * (k+1),
        mode='lines',
        name='Initial Bankroll',
        line=dict(dash='dash', color='gray'),
        hoverinfo='skip'
    ))

    frames.append(go.Frame(data=frame_data, name=str(k)))

# Create initial data trace
init_data = []

# Sim paths at frame 0
for i in range(num_to_animate):
    init_data.append(go.Scatter(
        y=[array_results[i][0]],
        mode='lines',
        line=dict(width=1, color='rgba(255,255,255,0.08)'),
        showlegend=False,
        hoverinfo='skip'
    ))

# Add average + initial bankroll lines
init_data.append(go.Scatter(
    y=[avg_bankroll[0]],
    mode='lines',
    name='Average Bankroll',
    line=dict(color='deepskyblue', width=4)
))
init_data.append(go.Scatter(
    y=[initial_bankroll],
    mode='lines',
    name='Initial Bankroll',
    line=dict(dash='dash', color='gray')
))

# Create animation figure
animated_fig = go.Figure(
    data=init_data,
    layout=go.Layout(
        title={
            'text': "🃏 Crown Blackjack Simulation<br><sup>(Perfect Basic Strategy + Card Counting)</sup>",
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=50)
        },
        xaxis=dict(title="Hands Played", range=[0, len(avg_bankroll)]),
        yaxis=dict(title="Bankroll ($)", range=[min(avg_bankroll)*0.98, max(avg_bankroll)*1.05]),
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
            x=0.1, y=1.15, xanchor="left", yanchor="top"
        )]
    ),
    frames=frames
)

st.plotly_chart(animated_fig, use_container_width=True)





# === 📊 Simulation Results (Compact All-in-One Layout) ===
st.subheader("📊 Simulation Results")

# First row: core performance metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("💸 Final Avg Bankroll", f"${final_bankrolls.mean():,.0f}")
col2.metric("📉 Std Dev", f"${std_dev:,.0f}")
col3.metric("📈 ROI", f"{roi:.2f}%", delta_color="normal")
col4.metric("📐 Sharpe Ratio", f"{sharpe_ratio:.4f}")


# Second row: advanced stats + custom outcomes
col5, col6, col7, col8 = st.columns(4)
col5.metric("🧮 EV per Hand", f"${ev_per_hand:.2f}")
col6.metric("🏆 Best Outcome", f"${max_gain:,.0f}")
col7.metric("💀 Worst Outcome", f"-${max_loss:,.0f}")
col8.metric("⚠️ Risk of Ruin", f"{risk_of_ruin:.2f}%")






# === Histogram of Final Bankrolls ===
st.subheader("📉 Distribution of Final Bankrolls")
hist_fig = go.Figure()
hist_fig.add_trace(go.Histogram(x=final_bankrolls, nbinsx=40, marker_color='green'))
hist_fig.update_layout(bargap=0.1, xaxis_title="Final Bankroll", yaxis_title="Frequency", height=600)
st.plotly_chart(hist_fig, use_container_width=True)

# === Plot True Count Over Time ===
st.subheader("📈 Average True Count Over Time")
true_fig = go.Figure()
true_fig.add_trace(go.Scatter(y=avg_true_counts, mode='lines', line=dict(color='orange', width=3)))
true_fig.update_layout(title="📊 True Count Over Time", xaxis_title="Hands Played", yaxis_title="True Count", height=500)
st.plotly_chart(true_fig, use_container_width=True)
