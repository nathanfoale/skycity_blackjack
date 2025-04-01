
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import random

# === Streamlit Setup ===
st.set_page_config(page_title="Blackjack Card Counting Simulator", layout="wide")
st.title("🃏 Blackjack Simulation with Card Counting (8 Decks)")

# === Parameters ===
initial_bankroll = st.sidebar.number_input("Initial Bankroll ($)", 1000, 1000000, 1000000, step=1000)
min_bet = st.sidebar.number_input("Minimum Bet ($)", 10, 500, 100, step=10)
spread = st.sidebar.slider("Bet Spread (for Hi-Lo Count)", 1, 20, 10)
num_simulations = st.sidebar.slider("Number of Simulations", 1, 1000, 100)
num_hands = st.sidebar.slider("Hands per Simulation", 100, 20000, 10000, step=100)
num_decks = st.sidebar.slider("Number of Decks", 1, 8, 8)

# === Hi-Lo Card Values ===
card_values = {
    '2': 1, '3': 1, '4': 1, '5': 1, '6': 1,
    '7': 0, '8': 0, '9': 0,
    '10': -1, 'J': -1, 'Q': -1, 'K': -1, 'A': -1
}
cards = list(card_values.keys()) * 4 * num_decks

def get_true_count(running_count, decks_remaining):
    if decks_remaining == 0:
        return 0
    return running_count / decks_remaining

def simulate_single_run():
    deck = cards.copy()
    random.shuffle(deck)
    running_count = 0
    bankroll = initial_bankroll
    bankrolls = []

    for i in range(num_hands):
        if len(deck) < 52:
            deck = cards.copy()
            random.shuffle(deck)
            running_count = 0

        card = deck.pop()
        running_count += card_values[card]
        true_count = get_true_count(running_count, len(deck)/52)

        bet = min_bet
        if true_count > 1:
            bet *= min(spread, int(true_count))
        bet = min(bankroll, bet)

        outcome = np.random.choice(["win", "lose", "push"], p=[0.42, 0.48, 0.10])
        if outcome == "win":
            bankroll += bet
        elif outcome == "lose":
            bankroll -= bet

        bankrolls.append(bankroll)

        if bankroll <= 0:
            break

    return bankrolls

# === Run Simulations ===
all_results = [simulate_single_run() for _ in range(num_simulations)]
max_length = max(len(r) for r in all_results)
padded_results = [r + [r[-1]] * (max_length - len(r)) for r in all_results]
array_results = np.array(padded_results)

avg_bankroll = np.mean(array_results, axis=0)
std_dev = np.std(array_results[:, -1])
final_bankrolls = array_results[:, -1]
roi = ((final_bankrolls.mean() - initial_bankroll) / initial_bankroll) * 100
risk_of_ruin = np.mean(final_bankrolls <= 0) * 100

# === Plot ===
fig, ax = plt.subplots(figsize=(12, 6))
for run in array_results:
    ax.plot(run, alpha=0.2, color='gray')
ax.plot(avg_bankroll, label='Average Bankroll', color='blue', linewidth=2)
ax.axhline(initial_bankroll, linestyle="--", color="black", alpha=0.5)
ax.set_title("Blackjack Bankroll Trajectories")
ax.set_xlabel("Hand Number")
ax.set_ylabel("Bankroll ($)")
ax.legend()

st.pyplot(fig)

# === Summary ===
st.subheader("📊 Simulation Results Summary")
st.metric("Final Average Bankroll", f"${final_bankrolls.mean():,.0f}")
st.metric("Standard Deviation", f"${std_dev:,.0f}")
st.metric("Return on Investment (ROI)", f"{roi:.2f}%")
st.metric("Risk of Ruin", f"{risk_of_ruin:.2f}%")
