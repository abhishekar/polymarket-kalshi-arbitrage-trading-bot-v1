"""
High Odds Market Analyzer

Filters Kalshi prediction markets by YES probability range.
Used to find markets with high probability outcomes (e.g., 85-95% YES odds).

Author: DexorynLabs
License: MIT
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from dateutil import parser as date_parser


@dataclass
class HighOddsMarket:
    """Represents a market with high YES odds."""
    ticker: str
    title: str
    yes_bid: Optional[int]  # Price in cents
    yes_ask: Optional[int]  # Price in cents
    yes_price: int  # The price used for filtering (in cents)
    liquidity: int  # Liquidity in cents
    expiration_date: Optional[datetime]
    status: str
    category: str = ""  # Market category (Politics, Economics, etc.)
    event_title: str = ""  # Parent event title
    
    @property
    def yes_probability(self) -> float:
        """Return YES probability as a decimal (0.0 to 1.0)."""
        return self.yes_price / 100.0
    
    @property
    def yes_percentage(self) -> float:
        """Return YES probability as a percentage (0 to 100)."""
        return float(self.yes_price)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON output."""
        return {
            "ticker": self.ticker,
            "title": self.title,
            "event_title": self.event_title,
            "category": self.category,
            "yes_bid": self.yes_bid,
            "yes_ask": self.yes_ask,
            "yes_price": self.yes_price,
            "yes_probability": self.yes_probability,
            "liquidity_cents": self.liquidity,
            "liquidity_dollars": self.liquidity / 100.0,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "status": self.status
        }


class HighOddsAnalyzer:
    """Analyzes and filters markets by YES probability range."""
    
    def __init__(self, min_odds: float = 0.85, max_odds: float = 0.95):
        """
        Initialize the analyzer.
        
        Args:
            min_odds: Minimum YES probability (0.0 to 1.0), default 0.85
            max_odds: Maximum YES probability (0.0 to 1.0), default 0.95
        """
        self.min_odds = min_odds
        self.max_odds = max_odds
        # Convert to cents for comparison
        self.min_cents = int(min_odds * 100)
        self.max_cents = int(max_odds * 100)
    
    def _get_yes_price(self, market: Dict) -> Optional[int]:
        """
        Get the YES price from market data.
        
        Uses yes_bid as the primary price (represents what you can sell at).
        Falls back to yes_ask, last_price, or midpoint if bid is not available.
        
        Args:
            market: Market dictionary from API
            
        Returns:
            YES price in cents, or None if not available
        """
        yes_bid = market.get("yes_bid")
        yes_ask = market.get("yes_ask")
        last_price = market.get("last_price")
        
        # Primary: use yes_bid if it's a meaningful value (not 0)
        if yes_bid is not None and yes_bid > 0:
            return yes_bid
        
        # Fallback: use yes_ask if meaningful
        if yes_ask is not None and yes_ask > 0:
            return yes_ask
        
        # Fallback: use last_price if available and meaningful
        if last_price is not None and last_price > 0:
            return last_price
        
        return None
    
    def _parse_expiration(self, market: Dict) -> Optional[datetime]:
        """Parse expiration/close date from market data."""
        # Try close_time first (when trading closes), then expiration_time
        expiration_str = (
            market.get("close_time") or 
            market.get("expiration_time") or 
            market.get("expiration_date")
        )
        if expiration_str:
            try:
                return date_parser.parse(expiration_str)
            except (ValueError, TypeError):
                return None
        return None
    
    def filter_markets(self, markets: List[Dict], 
                       min_liquidity: int = 0,
                       max_days_to_close: int = None) -> List[HighOddsMarket]:
        """
        Filter markets by YES probability range.
        
        Args:
            markets: List of market dictionaries from API
            min_liquidity: Minimum liquidity in cents (default: 0, no filter)
            max_days_to_close: Maximum days until market closes (default: None, no filter)
            
        Returns:
            List of HighOddsMarket objects matching the criteria
        """
        filtered = []
        
        for market in markets:
            # Skip non-open/active markets
            status = market.get("status", "")
            if status not in ("open", "active"):
                continue
            
            # Get YES price
            yes_price = self._get_yes_price(market)
            if yes_price is None:
                continue
            
            # Check if within odds range
            if not (self.min_cents <= yes_price <= self.max_cents):
                continue
            
            # Check liquidity threshold
            liquidity = market.get("liquidity", 0)
            if liquidity < min_liquidity:
                continue
            
            # Check expiration timeframe
            if max_days_to_close is not None:
                expiration_date = self._parse_expiration(market)
                if expiration_date:
                    # Make comparison timezone-aware
                    now = datetime.now(expiration_date.tzinfo) if expiration_date.tzinfo else datetime.now()
                    days_to_close = (expiration_date - now).days
                    if days_to_close < 0 or days_to_close > max_days_to_close:
                        continue
                else:
                    # No expiration date available, skip if filtering by days
                    continue
            
            # Create HighOddsMarket object
            high_odds_market = HighOddsMarket(
                ticker=market.get("ticker", ""),
                title=market.get("title", ""),
                yes_bid=market.get("yes_bid"),
                yes_ask=market.get("yes_ask"),
                yes_price=yes_price,
                liquidity=liquidity,
                expiration_date=self._parse_expiration(market),
                status=status,
                category=market.get("category", ""),
                event_title=market.get("event_title", "")
            )
            filtered.append(high_odds_market)
        
        # Sort by YES price descending (highest odds first)
        filtered.sort(key=lambda x: x.yes_price, reverse=True)
        
        return filtered
    
    def get_summary(self, markets: List[HighOddsMarket]) -> Dict:
        """
        Get summary statistics for filtered markets.
        
        Args:
            markets: List of filtered HighOddsMarket objects
            
        Returns:
            Dictionary with summary statistics
        """
        if not markets:
            return {
                "count": 0,
                "min_odds_filter": self.min_odds,
                "max_odds_filter": self.max_odds,
                "avg_yes_price": None,
                "total_liquidity": 0
            }
        
        yes_prices = [m.yes_price for m in markets]
        total_liquidity = sum(m.liquidity for m in markets)
        
        return {
            "count": len(markets),
            "min_odds_filter": self.min_odds,
            "max_odds_filter": self.max_odds,
            "avg_yes_price": sum(yes_prices) / len(yes_prices),
            "min_yes_price": min(yes_prices),
            "max_yes_price": max(yes_prices),
            "total_liquidity_cents": total_liquidity,
            "total_liquidity_dollars": total_liquidity / 100.0
        }
