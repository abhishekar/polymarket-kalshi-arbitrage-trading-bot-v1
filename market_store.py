import asyncio
import time
from typing import Dict, Any, Optional
from kalshi_client import KalshiClient

class MarketStore:
    """
    In-memory store for real-time market data.
    Maintains the latest orderbook and ticker state.
    """
    
    def __init__(self, rest_client: KalshiClient):
        self.rest_client = rest_client
        self.markets: Dict[str, Dict[str, Any]] = {}
        self.orderbooks: Dict[str, Dict[str, Any]] = {}
        self.event_markets: Dict[str, list] = {}  # event_ticker -> list of market tickers
        self._lock = asyncio.Lock()

    async def sync_market(self, ticker: str):
        """Fetch initial market and orderbook state via REST."""
        async with self._lock:
            # Fetch market details
            market = self.rest_client.get_market_by_ticker(ticker)
            if market:
                self.markets[ticker] = market
                
                # Track event association
                event_ticker = market.get('event_ticker', ticker)
                if event_ticker not in self.event_markets:
                    self.event_markets[event_ticker] = []
                if ticker not in self.event_markets[event_ticker]:
                    self.event_markets[event_ticker].append(ticker)
            
            # Fetch initial orderbook
            orderbook = self.rest_client.get_market_orderbook(ticker)
            if orderbook:
                self.orderbooks[ticker] = {
                    "yes": orderbook.get("orderbook", {}).get("yes", []),
                    "no": orderbook.get("orderbook", {}).get("no", []),
                    "ts": time.time()
                }
            print(f"Synced initial state for {ticker}")

    def handle_ticker_update(self, data: Dict[str, Any]):
        """Update market state from ticker_v2 channel."""
        msg = data.get("msg", {})
        ticker = msg.get("ticker")
        if not ticker:
            return
            
        if ticker not in self.markets:
            self.markets[ticker] = {}
            
        # Update price fields
        self.markets[ticker].update({
            "yes_bid": msg.get("yes_bid"),
            "yes_ask": msg.get("yes_ask"),
            "no_bid": msg.get("no_bid"),
            "no_ask": msg.get("no_ask"),
            "last_price": msg.get("last_price"),
            "volume": msg.get("volume"),
            "ts": msg.get("ts")
        })

    def handle_orderbook_delta(self, data: Dict[str, Any]):
        """Update orderbook state from orderbook_delta channel."""
        msg = data.get("msg", {})
        ticker = msg.get("market_ticker")
        if not ticker or ticker not in self.orderbooks:
            return
            
        side = msg.get("side") # 'yes' or 'no'
        price = msg.get("price")
        delta = msg.get("delta")
        
        # Update the specific price level in the orderbook
        # Note: In a real implementation, we'd manage a sorted list of levels.
        # For simplicity in this version, we'll just track the top levels if needed,
        # but the delta channel is intended for full book maintenance.
        
        current_book = self.orderbooks[ticker].get(side, [])
        # Find and update or remove the price level
        found = False
        for i, level in enumerate(current_book):
            if level[0] == price:
                new_count = level[1] + delta
                if new_count <= 0:
                    current_book.pop(i)
                else:
                    current_book[i] = [price, new_count]
                found = True
                break
        
        if not found and delta > 0:
            current_book.append([price, delta])
            # Keep it sorted: Bids (Yes) descending, Asks (No) descending? 
            # Actually Kalshi orderbook is YES bids/asks and NO bids/asks.
            current_book.sort(key=lambda x: x[0], reverse=True)
            
        self.orderbooks[ticker][side] = current_book
        self.orderbooks[ticker]["ts"] = time.time()

    def get_market_summary(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get a consolidated view of the market."""
        market = self.markets.get(ticker)
        if not market:
            return None
            
        return {
            "ticker": ticker,
            "event_ticker": market.get("event_ticker", ticker),
            "event_title": market.get("event_title", ""),
            "title": market.get("title", ""),
            "yes_bid": market.get("yes_bid"),
            "yes_ask": market.get("yes_ask"),
            "no_bid": market.get("no_bid"),
            "no_ask": market.get("no_ask"),
            "last_price": market.get("last_price"),
            "expiration_time": market.get("expiration_time"),
            "expiration_date": market.get("expiration_date")
        }
    
    def get_event_summary(self, event_ticker: str) -> list:
        """Get all markets belonging to an event."""
        if event_ticker not in self.event_markets:
            return []
        
        return [self.get_market_summary(t) for t in self.event_markets[event_ticker] 
                if self.get_market_summary(t) is not None]
