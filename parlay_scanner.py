#!/usr/bin/env python3
"""
Parlay Scanner CLI

Scans Kalshi sports parlay markets, analyzes their legs, and identifies
potential value opportunities where the parlay price differs from the
fair price calculated from individual leg probabilities.

Usage:
    python3 parlay_scanner.py                           # Scan for value parlays
    python3 parlay_scanner.py --ticker TICKER           # Analyze a specific parlay
    python3 parlay_scanner.py --min-edge 5              # Only show parlays with 5%+ edge
    python3 parlay_scanner.py --max-legs 5              # Only show parlays with 5 or fewer legs
    python3 parlay_scanner.py --min-volume 1            # Only show parlays with activity

Author: DexorynLabs
License: MIT
"""
import argparse
import json
import sys
from datetime import datetime
from typing import List

from dotenv import load_dotenv

from kalshi_client import KalshiClient
from parlay_analyzer import ParlayAnalyzer, ParlayBreakdown

load_dotenv()


def format_probability(prob: float) -> str:
    """Format probability as percentage."""
    if prob is None:
        return "N/A"
    return f"{prob * 100:.1f}%"


def format_edge(edge: float) -> str:
    """Format edge with sign."""
    if edge is None:
        return "N/A"
    sign = "+" if edge > 0 else ""
    return f"{sign}{edge:.1f}%"


def display_parlay_breakdown(breakdown: ParlayBreakdown, show_legs: bool = True):
    """Display a parlay breakdown in formatted text."""
    print("=" * 100)
    print(f"PARLAY: {breakdown.ticker}")
    print("-" * 100)
    
    # Truncate title if too long
    title = breakdown.title
    if len(title) > 200:
        title = title[:197] + "..."
    print(f"Title: {title}")
    print()
    
    # Pricing info
    print(f"Parlay Price: {breakdown.parlay_price_cents}¢ (YES) / {100 - breakdown.parlay_price_cents}¢ (NO)")
    
    if breakdown.fair_price_cents is not None:
        print(f"Fair Price:   {breakdown.fair_price_cents}¢ (calculated from legs)")
        print(f"Edge:         {format_edge(breakdown.edge)} ({breakdown.edge_direction})")
    else:
        print("Fair Price:   Unable to calculate (missing leg prices)")
    
    print()
    
    # Activity info
    print(f"Volume: {breakdown.volume} | 24h Volume: {breakdown.volume_24h} | Open Interest: {breakdown.open_interest}")
    if breakdown.expected_expiration:
        print(f"Expected Settlement: {breakdown.expected_expiration}")
    print()
    
    # Legs breakdown
    if show_legs and breakdown.legs:
        print(f"LEGS ({breakdown.num_legs}):")
        for i, leg in enumerate(breakdown.legs, 1):
            title = leg.title if leg.title else leg.market_ticker
            if len(title) > 80:
                title = title[:77] + "..."
            
            prob_str = leg.probability_pct
            side_str = leg.side.upper()
            
            print(f"  {i}. {title}")
            print(f"     Ticker: {leg.market_ticker}")
            print(f"     Side: {side_str} | Implied Prob: {prob_str}")
            if leg.price_cents is not None:
                print(f"     Price: {leg.price_cents}¢")
            print()
    
    # Fair price calculation breakdown
    if breakdown.fair_price is not None and breakdown.legs:
        probs = [leg.probability for leg in breakdown.legs if leg.probability is not None]
        if probs:
            calc_str = " x ".join([f"{p:.2f}" for p in probs])
            print(f"Fair Price Calculation: {calc_str} = {breakdown.fair_price:.4f} ({breakdown.fair_price_cents}¢)")
    
    print("=" * 100)
    print()


def display_summary_table(breakdowns: List[ParlayBreakdown]):
    """Display a summary table of parlays."""
    if not breakdowns:
        print("No parlays found matching criteria.")
        return
    
    print(f"\nFound {len(breakdowns)} parlays with potential value:\n")
    
    for i, b in enumerate(breakdowns, 1):
        fair_str = f"{b.fair_price_cents}¢" if b.fair_price_cents else "N/A"
        edge_str = format_edge(b.edge) if b.edge else "N/A"
        vol = b.volume + b.open_interest
        
        print(f"[{i}] {b.ticker}")
        print(f"    Legs: {b.num_legs} | Price: {b.parlay_price_cents}¢ | Fair: {fair_str} | Edge: {edge_str} ({b.edge_direction}) | Vol: {vol}")
        print()
    
    print(f"Total: {len(breakdowns)} parlays")
    print()


def display_json(breakdowns: List[ParlayBreakdown]):
    """Display results as JSON."""
    output = {
        "scan_time": datetime.now().isoformat(),
        "count": len(breakdowns),
        "parlays": [b.to_dict() for b in breakdowns]
    }
    print(json.dumps(output, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(
        description="Parlay Scanner - Analyze sports parlays for value opportunities"
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default=None,
        help="Analyze a specific parlay by ticker"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of parlays to fetch (default: 1000)"
    )
    parser.add_argument(
        "--min-edge",
        type=float,
        default=0,
        dest="min_edge",
        help="Minimum absolute edge in percentage points (default: 0)"
    )
    parser.add_argument(
        "--max-legs",
        type=int,
        default=None,
        dest="max_legs",
        help="Maximum number of legs per parlay (default: no limit)"
    )
    parser.add_argument(
        "--min-volume",
        type=int,
        default=0,
        dest="min_volume",
        help="Minimum volume + open interest (default: 0)"
    )
    parser.add_argument(
        "--output",
        choices=["table", "detail", "json"],
        default="table",
        help="Output format: table (summary), detail (full breakdown), json"
    )
    parser.add_argument(
        "--no-fetch-legs",
        action="store_true",
        dest="no_fetch_legs",
        help="Don't fetch individual leg markets (faster but no fair price calculation)"
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        dest="show_all",
        help="Show all parlays, not just those with calculable edge"
    )
    
    args = parser.parse_args()
    
    # Initialize client and analyzer
    client = KalshiClient()
    analyzer = ParlayAnalyzer(client)
    
    # Single ticker analysis
    if args.ticker:
        print(f"[{datetime.now()}] Fetching parlay {args.ticker}...")
        market = client.get_market_by_ticker(args.ticker)
        
        if not market:
            print(f"Error: Parlay not found: {args.ticker}")
            sys.exit(1)
        
        print(f"[{datetime.now()}] Analyzing parlay legs...")
        breakdown = analyzer.analyze_parlay(market, fetch_legs=not args.no_fetch_legs)
        
        if args.output == "json":
            print(json.dumps(breakdown.to_dict(), indent=2, default=str))
        else:
            display_parlay_breakdown(breakdown, show_legs=True)
        
        return
    
    # Scan for value parlays
    print(f"[{datetime.now()}] Fetching up to {args.limit} sports parlays...")
    parlays = client.get_markets(limit=args.limit, status="open")
    
    if not parlays:
        print("No parlays found or API error.")
        sys.exit(1)
    
    # Filter to only parlay markets (KXMVE...)
    parlays = [p for p in parlays if p.get("ticker", "").startswith("KXMVE")]
    print(f"[{datetime.now()}] Found {len(parlays)} parlay markets.")
    
    # Further filter to parlays with activity
    if args.min_volume > 0:
        parlays = [p for p in parlays if (p.get("volume", 0) + p.get("open_interest", 0)) >= args.min_volume]
        print(f"[{datetime.now()}] {len(parlays)} parlays with volume >= {args.min_volume}")
    
    # Filter to parlays with a price
    parlays = [p for p in parlays if p.get("last_price", 0) > 0]
    print(f"[{datetime.now()}] {len(parlays)} parlays with trading activity (last_price > 0)")
    
    if not parlays:
        print("No active parlays found.")
        sys.exit(0)
    
    # Analyze parlays
    fetch_legs = not args.no_fetch_legs
    if fetch_legs:
        print(f"[{datetime.now()}] Analyzing parlay legs (this may take a moment)...")
    
    results = analyzer.find_value_parlays(
        parlays,
        min_edge=args.min_edge,
        max_legs=args.max_legs,
        min_volume=args.min_volume,
        fetch_legs=fetch_legs
    )
    
    # Filter to only those with calculable edge (unless --show-all)
    if not args.show_all:
        results = [r for r in results if r.edge is not None]
    
    # Display results
    if args.output == "json":
        display_json(results)
    elif args.output == "detail":
        for breakdown in results:
            display_parlay_breakdown(breakdown, show_legs=True)
    else:  # table
        display_summary_table(results)
        
        # Show top 3 in detail if table mode
        if results and len(results) <= 10:
            print("\n--- DETAILED BREAKDOWN ---\n")
            for breakdown in results[:3]:
                display_parlay_breakdown(breakdown, show_legs=True)


if __name__ == "__main__":
    main()
