import os
import re
import json
import requests
import pandas as pd
from dotenv import load_dotenv
from unidecode import unidecode

from utils import call_kalshi_api

#########################################
# Load credentials
#########################################

load_dotenv()
KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID")

KALSHI_API_BASE = "https://api.elections.kalshi.com/trade-api/v2"
DATA_FILE = "data/player_data.json"

#########################################
# Stat normalization
#########################################

STAT_NORMALIZATION = {
    "points": ["points", "pts"],
    "rebounds": ["rebounds", "rebs"],
    "assists": ["assists", "asts"],
    "threes": ["three", "3pt", "3pts", "threes"]
}

#########################################
# Normalize text
#########################################

def normalize_text(text):

    text = unidecode(text)
    text = text.lower()

    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()

#########################################
# Convert Kalshi price → implied probability
#########################################

def price_to_probability(price):

    if price is None:
        return None

    return price / 100.0

#########################################
# Load player JSON data
#########################################

def load_player_data():

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    legs = []

    for row in data:

        threshold = int(re.search(r"\d+", row["threshold"]).group())

        legs.append({
            "player": row["player_name"],
            "player_norm": normalize_text(row["player_name"]),
            "team": row["team"],
            "stat": row["stat_type"],
            "threshold": threshold,
            "model_probability": row["success_probability"] / 100
        })

    return legs

#########################################
# Fetch Kalshi NBA markets
#########################################

def fetch_kalshi_markets():


    r = call_kalshi_api(private_key_path="credentials/kalshi-secret.txt", 
                    method= "GET",
                    base_url=KALSHI_API_BASE, 
                    endpoint_path="/markets?series_sub_tags=nba",
                    kalshi_key_id= KALSHI_KEY_ID)



    return r.json()["markets"]

#########################################
# Check if stat matches market title
#########################################

def stat_matches(stat, title):

    variants = STAT_NORMALIZATION.get(stat, [])

    for v in variants:
        if v in title:
            return True

    return False

#########################################
# Match legs to Kalshi markets
#########################################

def match_markets(legs, markets):

    matches = []

    for market in markets:

        title = market.get("title", "")
        title_norm = normalize_text(title)

        ticker = market.get("ticker")

        yes_price = market.get("yes_bid") or market.get("yes_ask")

        market_prob = price_to_probability(yes_price)

        event_date = market.get("event_date")

        for leg in legs:

            if leg["player_norm"] not in title_norm:
                continue

            if str(leg["threshold"]) not in title_norm:
                continue

            if not stat_matches(leg["stat"], title_norm):
                continue

            edge = None

            if market_prob is not None:
                edge = leg["model_probability"] - market_prob

            matches.append({
                "player": leg["player"],
                "team": leg["team"],
                "stat": leg["stat"],
                "threshold": leg["threshold"],
                "model_probability": leg["model_probability"],
                "kalshi_yes_price": yes_price,
                "kalshi_implied_probability": market_prob,
                "edge": edge,
                "event_date": event_date,
                "ticker": ticker,
                "market_title": title
            })

    return matches

#########################################
# Main
#########################################

def main():

    print("Loading player data...")

    legs = load_player_data()

    print(f"Loaded {len(legs)} stat legs")

    print("Fetching Kalshi NBA markets...")

    markets = fetch_kalshi_markets()

    print(markets)

    print(f"Found {len(markets)} markets")

    print("Matching markets...")

    matches = match_markets(legs, markets)

    df = pd.DataFrame(matches)

    if df.empty:
        print("No matches found")
        return

    print(df.head())

    df.to_csv("kalshi_matches.csv", index=False)

    print("Saved results to kalshi_matches.csv")


if __name__ == "__main__":
    main()