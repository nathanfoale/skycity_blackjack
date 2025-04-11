# 🎰 SkyCity Blackjack Simulator

A fully interactive and realistic simulation of **Blackjack at SkyCity Casino**, built in Python using **Streamlit**, **NumPy**, and **Plotly**.

This tool lets you simulate thousands of hands under real-world conditions using **flat betting**, **basic strategy**, and **continuous shuffling machine (CSM)** rules. Ideal for analyzing the house edge, risk of ruin, and bankroll fluctuations over time.

---

## 🃏 Casino Rules Modeled

The simulator reflects SkyCity’s 2025 blackjack table rules:

- **Decks Used**: 6 standard decks (52 cards each)
- **Dealer Hits Soft 17**: ✅
- **Blackjack Payout**: 3:2
- **Doubling Down**: Only on hard 9–11
- **Double After Split (DAS)**: ✅
- **Splits**: Unlimited (except Aces)
- **Split Aces**: One split allowed, one card only dealt
- **Surrender**: ❌ Not available
- **Insurance**: ✅ (available when dealer shows an Ace)
- **Dealer 22**: Busts (not a push)
- **Shuffling**: Simulated Continuous Shuffling Machine (CSM)

---

## 📊 Features

- 🔁 **Simulate** thousands of hands across multiple sessions
- 📈 **Animated bankroll progression** and average trajectory
- 🧮 **Statistical metrics**: ROI, EV per hand, risk of ruin, Sharpe ratio
- 📉 **Distribution plots** for final bankroll outcomes
- ⚙️ Adjustable parameters via sidebar:
  - Initial bankroll
  - Number of hands and simulations
  - Bet size (flat)

---

## 🚀 Live Demo

> **[Launch on Streamlit Cloud](https://skycity-blackjack.streamlit.app)**  
> *(Or clone this repo and run locally)*

---

## 🧠 Strategy Used

This version simulates:
- **Flat betting only** (no card counting)
- **Basic strategy** decisions (simplified logic with some variations)

---

## 🛠 How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/nathanfoale/skycity_blackjack.git
cd skycity_blackjack

