"""
Parlay Analyzer Module

Analyzes sports parlay markets by breaking down their individual legs,
fetching each leg's probability, and comparing the combined probability
to the parlay price to identify potential value.

Author: DexorynLabs
License: MIT
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time


@dataclass
class ParlayLeg:
    """Represents a single leg in a parlay."""
    market_ticker: str
    event_ticker: str
    side: str  # 'yes' or 'no'
    title: str = ""
    probability: Optional[float] = None  # 0.0 to 1.0
    price_cents: Optional[int] = None
    status: str = ""
    
    @property
    def probability_pct(self) -> str:
        """Return probability as percentage string."""
        if self.probability is not None:
            return f"{self.probability * 100:.1f}%"
        return "N/A"
    
    def to_dict(self) -> Dict:
        return {
            "market_ticker": self.market_ticker,
            "event_ticker": self.event_ticker,
            "side": self.side,
            "title": self.title,
            "probability": self.probability,
            "price_cents": self.price_cents,
            "status": self.status
        }


@dataclass
class ParlayBreakdown:
    """Represents a full parlay analysis."""
    ticker: str
    title: str
    parlay_price_cents: int  # The actual parlay price
    legs: List[ParlayLeg] = field(default_factory=list)
    volume: int = 0
    volume_24h: int = 0
    open_interest: int = 0
    liquidity: int = 0
    expected_expiration: Optional[str] = None
    status: str = ""
    
    @property
    def num_legs(self) -> int:
        return len(self.legs)
    
    @property
    def fair_price(self) -> Optional[float]:
        """
        Calculate fair price by multiplying leg probabilities.
        Returns probability (0.0 to 1.0) or None if any leg is missing probability.
        """
        if not self.legs:
            return None
        
        fair = 1.0
        for leg in self.legs:
            if leg.probability is None:
                return None
            fair *= leg.probability
        return fair
    
    @property
    def fair_price_cents(self) -> Optional[int]:
        """Fair price in cents."""
        fair = self.fair_price
        if fair is not None:
            return int(fair * 100)
        return None
    
    @property
    def edge(self) -> Optional[float]:
        """
        Calculate edge (difference between fair price and actual price).
        Positive edge = parlay is underpriced (potential value for YES)
        Negative edge = parlay is overpriced (potential value for NO)
        Returns percentage points.
        """
        fair = self.fair_price
        if fair is None:
            return None
        actual = self.parlay_price_cents / 100.0
        return (fair - actual) * 100  # Convert to percentage points
    
    @property
    def edge_direction(self) -> str:
        """Return 'UNDERPRICED', 'OVERPRICED', or 'FAIR'."""
        edge = self.edge
        if edge is None:
            return "UNKNOWN"
        if edge > 1:
            return "UNDERPRICED"
        elif edge < -1:
            return "OVERPRICED"
        return "FAIR"
    
    def to_dict(self) -> Dict:
        return {
            "ticker": self.ticker,
            "title": self.title,
            "parlay_price_cents": self.parlay_price_cents,
            "fair_price_cents": self.fair_price_cents,
            "edge_pct": self.edge,
            "edge_direction": self.edge_direction,
            "num_legs": self.num_legs,
            "legs": [leg.to_dict() for leg in self.legs],
            "volume": self.volume,
            "volume_24h": self.volume_24h,
            "open_interest": self.open_interest,
            "liquidity": self.liquidity,
            "expected_expiration": self.expected_expiration,
            "status": self.status
        }


class ParlayAnalyzer:
    """Analyzes parlay markets by breaking down their legs."""
    
    def __init__(self, client, rate_limit_delay: float = 0.1):
        """
        Initialize the analyzer.
        
        Args:
            client: KalshiClient instance
            rate_limit_delay: Delay between API calls in seconds (default 0.1s)
        """
        self.client = client
        self.rate_limit_delay = rate_limit_delay
        self._leg_cache: Dict[str, Dict] = {}  # Cache leg market data
    
    def _get_leg_market(self, ticker: str) -> Optional[Dict]:
        """
        Fetch a leg's market data, using cache if available.
        
        Args:
            ticker: Market ticker for the leg
            
        Returns:
            Market dictionary or None if not found
        """
        if ticker in self._leg_cache:
            return self._leg_cache[ticker]
        
        time.sleep(self.rate_limit_delay)
        market = self.client.get_market_by_ticker(ticker)
        
        if market:
            self._leg_cache[ticker] = market
        
        return market
    
    def _get_leg_probability(self, market: Dict, side: str) -> Optional[float]:
        """
        Get the probability for a leg based on its side.
        
        Args:
            market: Market dictionary
            side: 'yes' or 'no'
            
        Returns:
            Probability (0.0 to 1.0) or None if not available
        """
        # Try yes_bid first (what you can sell at), then yes_ask, then last_price
        yes_price = None
        
        yes_bid = market.get("yes_bid")
        yes_ask = market.get("yes_ask")
        last_price = market.get("last_price")
        
        if yes_bid is not None and yes_bid > 0:
            yes_price = yes_bid
        elif yes_ask is not None and yes_ask > 0 and yes_ask < 100:
            yes_price = yes_ask
        elif last_price is not None and last_price > 0:
            yes_price = last_price
        
        if yes_price is None:
            return None
        
        # Convert to probability based on side
        if side == "yes":
            return yes_price / 100.0
        else:  # "no"
            return (100 - yes_price) / 100.0
    
    def analyze_parlay(self, parlay_market: Dict, fetch_legs: bool = True) -> ParlayBreakdown:
        """
        Analyze a parlay market and break down its legs.
        
        Args:
            parlay_market: Parlay market dictionary from API
            fetch_legs: If True, fetch each leg's market data for probabilities
            
        Returns:
            ParlayBreakdown with leg analysis
        """
        # Get parlay price
        parlay_price = 0
        last_price = parlay_market.get("last_price", 0)
        yes_bid = parlay_market.get("yes_bid", 0)
        yes_ask = parlay_market.get("yes_ask", 0)
        
        if last_price > 0:
            parlay_price = last_price
        elif yes_bid > 0:
            parlay_price = yes_bid
        elif yes_ask > 0 and yes_ask < 100:
            parlay_price = yes_ask
        
        breakdown = ParlayBreakdown(
            ticker=parlay_market.get("ticker", ""),
            title=parlay_market.get("title", ""),
            parlay_price_cents=parlay_price,
            volume=parlay_market.get("volume", 0),
            volume_24h=parlay_market.get("volume_24h", 0),
            open_interest=parlay_market.get("open_interest", 0),
            liquidity=parlay_market.get("liquidity", 0),
            expected_expiration=parlay_market.get("expected_expiration_time"),
            status=parlay_market.get("status", "")
        )
        
        # Extract legs from mve_selected_legs
        mve_legs = parlay_market.get("mve_selected_legs", [])
        
        for leg_data in mve_legs:
            market_ticker = leg_data.get("market_ticker", "")
            event_ticker = leg_data.get("event_ticker", "")
            side = leg_data.get("side", "yes")
            
            leg = ParlayLeg(
                market_ticker=market_ticker,
                event_ticker=event_ticker,
                side=side
            )
            
            # Fetch leg market data if requested
            if fetch_legs and market_ticker:
                leg_market = self._get_leg_market(market_ticker)
                if leg_market:
                    leg.title = leg_market.get("title", "")
                    leg.status = leg_market.get("status", "")
                    leg.probability = self._get_leg_probability(leg_market, side)
                    
                    # Store raw price
                    yes_price = leg_market.get("yes_bid") or leg_market.get("yes_ask") or leg_market.get("last_price")
                    if yes_price:
                        leg.price_cents = yes_price if side == "yes" else (100 - yes_price)
            
            breakdown.legs.append(leg)
        
        return breakdown
    
    def find_value_parlays(self, parlays: List[Dict], min_edge: float = 0, 
                           max_legs: int = None, min_volume: int = 0,
                           fetch_legs: bool = True) -> List[ParlayBreakdown]:
        """
        Find parlays with potential value (mispriced).
        
        Args:
            parlays: List of parlay market dictionaries
            min_edge: Minimum absolute edge in percentage points
            max_legs: Maximum number of legs (None = no limit)
            min_volume: Minimum volume/activity
            fetch_legs: If True, fetch each leg's market data
            
        Returns:
            List of ParlayBreakdown objects sorted by edge
        """
        results = []
        
        for parlay in parlays:
            # Quick filters before expensive leg fetching
            volume = parlay.get("volume", 0) + parlay.get("open_interest", 0)
            if volume < min_volume:
                continue
            
            mve_legs = parlay.get("mve_selected_legs", [])
            if max_legs is not None and len(mve_legs) > max_legs:
                continue
            
            # Must have a price
            last_price = parlay.get("last_price", 0)
            if last_price <= 0:
                continue
            
            # Analyze the parlay
            breakdown = self.analyze_parlay(parlay, fetch_legs=fetch_legs)
            
            # Filter by edge
            if breakdown.edge is not None and abs(breakdown.edge) >= min_edge:
                results.append(breakdown)
        
        # Sort by absolute edge (highest first)
        results.sort(key=lambda x: abs(x.edge) if x.edge else 0, reverse=True)
        
        return results
    
    def clear_cache(self):
        """Clear the leg market cache."""
        self._leg_cache.clear()
