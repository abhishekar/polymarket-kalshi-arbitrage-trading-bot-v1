#!/usr/bin/env python3
"""
Kalshi High Odds Market Scanner (Bot v2)

A Python tool that finds active Kalshi markets with YES odds in a specified range.
Default range: 85% - 95% (high probability events).

Configuration via .env file:
    DEFAULT_LIMIT=1000          # Default number of markets to fetch
    MIN_ODDS=0.85               # Default minimum YES probability (0.0-1.0)
    MAX_ODDS=0.95               # Default maximum YES probability (0.0-1.0)
    MIN_LIQUIDITY=10000         # Default minimum liquidity in cents ($100)
    MAX_DAYS=None               # Default max days to close (None = no filter)

Usage:
    python3 bot-v2.py --limit 1000
    python3 bot-v2.py --limit 500 --min-odds 0.90 --max-odds 0.95
    python3 bot-v2.py --limit 1000 --output json

Author: DexorynLabs
License: MIT
"""
import argparse
import json
import os
import sys
from datetime import datetime
from typing import List

from dotenv import load_dotenv

from kalshi_client import KalshiClient
from high_odds_analyzer import HighOddsAnalyzer, HighOddsMarket

load_dotenv()

# Load defaults from environment variables
DEFAULT_LIMIT = int(os.getenv("DEFAULT_LIMIT", "1000"))
DEFAULT_MIN_ODDS = float(os.getenv("MIN_ODDS", "0.85"))
DEFAULT_MAX_ODDS = float(os.getenv("MAX_ODDS", "0.95"))
DEFAULT_MIN_LIQUIDITY = int(os.getenv("MIN_LIQUIDITY", "0"))
DEFAULT_MAX_DAYS = os.getenv("MAX_DAYS")  # None if not set
if DEFAULT_MAX_DAYS is not None and DEFAULT_MAX_DAYS.strip():
    DEFAULT_MAX_DAYS = int(DEFAULT_MAX_DAYS)
else:
    DEFAULT_MAX_DAYS = None


def format_liquidity(cents: int) -> str:
    """Format liquidity in cents to dollar string."""
    dollars = cents / 100.0
    if dollars >= 1000:
        return f"${dollars:,.0f}"
    return f"${dollars:.2f}"


def format_expiration(dt: datetime) -> str:
    """Format expiration datetime to readable string."""
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M")


def truncate_string(s: str, max_len: int) -> str:
    """Truncate string to max length with ellipsis."""
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."


def display_table(markets: List[HighOddsMarket], min_odds: float, max_odds: float):
    """Display markets in a formatted table with full titles."""
    min_pct = int(min_odds * 100)
    max_pct = int(max_odds * 100)
    
    print(f"\nFound {len(markets)} markets with YES odds between {min_pct}% - {max_pct}%\n")
    
    if not markets:
        print("No markets found matching the criteria.")
        return
    
    # Display each market as a block for better readability
    print("=" * 100)
    
    for i, market in enumerate(markets, 1):
        # Use event_title if available (more descriptive), otherwise use title
        display_title = market.event_title if market.event_title else market.title
        category = market.category if market.category else "N/A"
        yes_price = f"{market.yes_price}¢"
        no_price = f"{100 - market.yes_price}¢"
        liquidity = format_liquidity(market.liquidity)
        expires = format_expiration(market.expiration_date)
        
        print(f"[{i}] {display_title}")
        print(f"    Ticker: {market.ticker}")
        print(f"    Category: {category} | YES: {yes_price} | NO: {no_price} | Liquidity: {liquidity} | Closes: {expires}")
        print("-" * 100)
    
    print(f"\nTotal: {len(markets)} markets")


def display_json(markets: List[HighOddsMarket], analyzer: HighOddsAnalyzer):
    """Display markets as JSON output."""
    output = {
        "summary": analyzer.get_summary(markets),
        "markets": [m.to_dict() for m in markets]
    }
    print(json.dumps(output, indent=2, default=str))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Kalshi High Odds Market Scanner - Find markets with high YES probability"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Maximum number of markets to fetch from API (default: {DEFAULT_LIMIT}, env: DEFAULT_LIMIT)"
    )
    parser.add_argument(
        "--min-odds",
        type=float,
        default=DEFAULT_MIN_ODDS,
        dest="min_odds",
        help=f"Minimum YES probability (0.0-1.0, default: {DEFAULT_MIN_ODDS}, env: MIN_ODDS)"
    )
    parser.add_argument(
        "--max-odds",
        type=float,
        default=DEFAULT_MAX_ODDS,
        dest="max_odds",
        help=f"Maximum YES probability (0.0-1.0, default: {DEFAULT_MAX_ODDS}, env: MAX_ODDS)"
    )
    parser.add_argument(
        "--min-liquidity",
        type=int,
        default=DEFAULT_MIN_LIQUIDITY,
        dest="min_liquidity",
        help=f"Minimum liquidity in cents (default: {DEFAULT_MIN_LIQUIDITY}, env: MIN_LIQUIDITY)"
    )
    parser.add_argument(
        "--max-days",
        type=int,
        default=DEFAULT_MAX_DAYS,
        dest="max_days",
        help=f"Maximum days until market closes (default: {DEFAULT_MAX_DAYS or 'no filter'}, env: MAX_DAYS)"
    )
    parser.add_argument(
        "--output",
        choices=["table", "json"],
        default="table",
        help="Output format: table (default) or json"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug information about market data"
    )
    parser.add_argument(
        "--source",
        choices=["events", "markets"],
        default="events",
        help="Data source: 'events' for prediction markets (default), 'markets' for sports parlays"
    )
    
    args = parser.parse_args()
    
    # Validate odds range
    if not (0.0 <= args.min_odds <= 1.0):
        print(f"Error: --min-odds must be between 0.0 and 1.0, got {args.min_odds}")
        sys.exit(1)
    if not (0.0 <= args.max_odds <= 1.0):
        print(f"Error: --max-odds must be between 0.0 and 1.0, got {args.max_odds}")
        sys.exit(1)
    if args.min_odds > args.max_odds:
        print(f"Error: --min-odds ({args.min_odds}) cannot be greater than --max-odds ({args.max_odds})")
        sys.exit(1)
    
    # Initialize client and analyzer
    source_desc = "prediction markets (events)" if args.source == "events" else "sports parlays (markets)"
    print(f"[{datetime.now()}] Fetching up to {args.limit} {source_desc} from Kalshi...")
    
    client = KalshiClient()
    analyzer = HighOddsAnalyzer(min_odds=args.min_odds, max_odds=args.max_odds)
    
    # Fetch markets from appropriate source
    if args.source == "events":
        markets = client.get_events_with_markets(limit=args.limit, status="open")
    else:
        markets = client.get_markets(limit=args.limit, status="open")
    
    if not markets:
        print("No markets found or API error.")
        sys.exit(1)
    
    # Debug: show sample market data and statistics
    if args.debug:
        print(f"\n[DEBUG] Sample market data (first 3 markets):")
        for i, m in enumerate(markets[:3]):
            print(f"  Market {i+1}: {json.dumps({k: m.get(k) for k in ['ticker', 'title', 'status', 'yes_bid', 'yes_ask', 'no_bid', 'no_ask', 'liquidity', 'last_price']}, indent=4)}")
        
        # Find a market with non-zero prices
        non_zero_markets = [m for m in markets if m.get("yes_bid", 0) > 0 or m.get("last_price", 0) > 0]
        if non_zero_markets:
            print(f"\n[DEBUG] Sample market with actual prices:")
            m = non_zero_markets[0]
            print(f"  {json.dumps({k: m.get(k) for k in ['ticker', 'title', 'status', 'yes_bid', 'yes_ask', 'no_bid', 'no_ask', 'liquidity', 'last_price', 'volume', 'volume_24h']}, indent=4)}")
        else:
            print(f"\n[DEBUG] No markets found with non-zero yes_bid or last_price!")
            # Show all keys from first market
            if markets:
                print(f"[DEBUG] All keys in market data: {list(markets[0].keys())}")
        
        # Count markets by status
        statuses = {}
        for m in markets:
            s = m.get("status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1
        print(f"\n[DEBUG] Markets by status: {statuses}")
        
        # Count markets with yes_bid
        has_yes_bid = sum(1 for m in markets if m.get("yes_bid") is not None)
        has_yes_ask = sum(1 for m in markets if m.get("yes_ask") is not None)
        has_last_price = sum(1 for m in markets if m.get("last_price") is not None)
        print(f"[DEBUG] Markets with yes_bid: {has_yes_bid}/{len(markets)}")
        print(f"[DEBUG] Markets with yes_ask: {has_yes_ask}/{len(markets)}")
        print(f"[DEBUG] Markets with last_price: {has_last_price}/{len(markets)}")
        
        # Show yes_bid distribution for markets that have it
        yes_bids = [m.get("yes_bid") for m in markets if m.get("yes_bid") is not None]
        if yes_bids:
            print(f"[DEBUG] yes_bid range: {min(yes_bids)} - {max(yes_bids)} cents")
            in_range = sum(1 for yb in yes_bids if args.min_odds * 100 <= yb <= args.max_odds * 100)
            print(f"[DEBUG] yes_bid in {int(args.min_odds*100)}-{int(args.max_odds*100)} range: {in_range}")
        
        # Show last_price distribution (more reliable for actual pricing)
        last_prices = [m.get("last_price") for m in markets if m.get("last_price") is not None and m.get("last_price") > 0]
        if last_prices:
            print(f"[DEBUG] last_price (non-zero) count: {len(last_prices)}/{len(markets)}")
            print(f"[DEBUG] last_price range: {min(last_prices)} - {max(last_prices)} cents")
            in_range = sum(1 for lp in last_prices if args.min_odds * 100 <= lp <= args.max_odds * 100)
            print(f"[DEBUG] last_price in {int(args.min_odds*100)}-{int(args.max_odds*100)} range: {in_range}")
        print()
    
    filter_desc = f"YES odds {int(args.min_odds*100)}%-{int(args.max_odds*100)}%"
    if args.max_days:
        filter_desc += f", closing within {args.max_days} days"
    print(f"[{datetime.now()}] Fetched {len(markets)} markets. Filtering by {filter_desc}...")
    
    # Filter markets
    filtered_markets = analyzer.filter_markets(
        markets, 
        min_liquidity=args.min_liquidity,
        max_days_to_close=args.max_days
    )
    
    # Display results
    if args.output == "json":
        display_json(filtered_markets, analyzer)
    else:
        display_table(filtered_markets, args.min_odds, args.max_odds)


if __name__ == "__main__":
    main()
