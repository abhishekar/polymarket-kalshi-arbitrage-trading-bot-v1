"""
Kalshi API Client

A client for interacting with the Kalshi prediction market API.
Handles authentication, rate limiting, and API requests.

Features:
- Automatic rate limiting to avoid API throttling
- Support for both official SDK and REST API
- Error handling and retry logic
"""
import os
import requests
import time
import json
import hmac
import hashlib
import base64
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class KalshiClient:
    """Client for interacting with Kalshi API."""
    
    def __init__(self):
        # API Key ID from Kalshi account settings
        self.api_key = os.getenv("KALSHI_API_KEY")
        # Private Key from Kalshi account settings (can be PEM string or file path)
        self.api_secret = os.getenv("KALSHI_API_SECRET")
        self.base_url = os.getenv("KALSHI_API_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2")
        self.session = requests.Session()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = float(os.getenv("API_MIN_INTERVAL", "0.1"))  # 100ms between requests
        self.request_count = 0
        self.rate_limit_reset_time = 0
        
        # Check if credentials are set (not placeholders)
        if not self.api_key or self.api_key == "your_api_key_id_here":
            print("Warning: KALSHI_API_KEY not set or still has placeholder value")
        if not self.api_secret or self.api_secret == "your_private_key_here":
            print("Warning: KALSHI_API_SECRET not set or still has placeholder value")
        
        # Try to use official SDK if available, otherwise use REST API
        self.use_sdk = False
        try:
            from kalshi_python import Configuration, KalshiClient as SDKClient
            self.use_sdk = True
            # If private key is a file path, read it
            private_key = self.api_secret
            if os.path.isfile(self.api_secret):
                with open(self.api_secret, 'r') as f:
                    private_key = f.read()
            
            config = Configuration(
                host=self.base_url,
                api_key_id=self.api_key,
                private_key_pem=private_key
            )
            self.sdk_client = SDKClient(config)
        except ImportError:
            # Fall back to REST API with custom auth
            if self.api_key and self.api_secret:
                # Kalshi may use JWT or custom headers - this is a placeholder
                # You may need to adjust based on actual API requirements
                self.session.headers.update({
                    'X-API-Key': self.api_key,
                    'X-API-Secret': self.api_secret
                })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make an authenticated request to the Kalshi API with rate limiting."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Rate limiting: ensure minimum interval between requests
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        # Check if we're in a rate limit cooldown period
        if current_time < self.rate_limit_reset_time:
            wait_time = self.rate_limit_reset_time - current_time
            print(f"Rate limit cooldown: waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
        
        try:
            self.last_request_time = time.time()
            self.request_count += 1
            
            response = self.session.request(method, url, **kwargs)
            
            # Handle rate limiting
            if response.status_code == 429:
                # Extract retry-after header if available
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    wait_time = int(retry_after)
                else:
                    # Default wait time for rate limits
                    wait_time = 60  # Wait 60 seconds
                
                self.rate_limit_reset_time = time.time() + wait_time
                print(f"Rate limit hit (429). Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
                
                # Retry once after waiting
                response = self.session.request(method, url, **kwargs)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 429:
                    # Rate limit error - don't print full error, just wait
                    retry_after = e.response.headers.get('Retry-After', '60')
                    wait_time = int(retry_after)
                    self.rate_limit_reset_time = time.time() + wait_time
                    print(f"Rate limit error. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    raise
                else:
                    print(f"API request failed: {e}")
                    if hasattr(e.response, 'text'):
                        print(f"Response: {e.response.text}")
            else:
                print(f"API request failed: {e}")
            raise
    
    def get_markets(self, limit: int = 100, status: str = "open") -> List[Dict]:
        """
        Fetch active markets from Kalshi with pagination support.
        
        Args:
            limit: Maximum number of markets to return
            status: Market status filter (e.g., 'open', 'closed')
        
        Returns:
            List of market dictionaries
        """
        all_markets = []
        cursor = None
        page_size = min(1000, limit)  # API max is 1000 for /markets endpoint
        
        try:
            while len(all_markets) < limit:
                params = {
                    "limit": page_size,
                    "status": status
                }
                if cursor:
                    params["cursor"] = cursor
                
                response = self._make_request("GET", "/markets", params=params)
                markets = response.get("markets", [])
                
                if not markets:
                    break
                
                all_markets.extend(markets)
                
                cursor = response.get("cursor")
                if not cursor:
                    break
            
            return all_markets[:limit]
        except Exception as e:
            print(f"Error fetching markets: {e}")
            return all_markets
    
    def get_market_by_ticker(self, ticker: str) -> Optional[Dict]:
        """
        Fetch a single market by its ticker.
        
        Args:
            ticker: The market ticker (e.g., 'KXNBAPTS-26JAN28SASHOU-HOUKDURANT7-20')
        
        Returns:
            Market dictionary if found, None otherwise
        """
        try:
            response = self._make_request("GET", f"/markets/{ticker}")
            return response.get("market")
        except Exception as e:
            # Market not found or other error
            return None
    
    def get_events_with_markets(self, limit: int = 100, status: str = "open") -> List[Dict]:
        """
        Fetch events with nested markets from Kalshi.
        
        This returns the actual prediction markets (politics, economics, etc.)
        rather than just sports parlays from the /markets endpoint.
        
        Args:
            limit: Maximum number of markets to return (will paginate through events)
            status: Event status filter (e.g., 'open', 'closed')
        
        Returns:
            List of market dictionaries extracted from events
        """
        all_markets = []
        cursor = None
        page_size = min(200, limit)  # API max is around 200
        
        try:
            while len(all_markets) < limit:
                params = {
                    "limit": page_size,
                    "status": status,
                    "with_nested_markets": "true"
                }
                if cursor:
                    params["cursor"] = cursor
                
                response = self._make_request("GET", "/events", params=params)
                events = response.get("events", [])
                
                if not events:
                    break  # No more events
                
                # Extract all markets from events
                for event in events:
                    event_markets = event.get("markets", [])
                    # Add event metadata to each market
                    for market in event_markets:
                        market["event_ticker"] = event.get("event_ticker", "")
                        market["event_title"] = event.get("title", "")
                        market["category"] = event.get("category", "")
                        all_markets.append(market)
                        
                        if len(all_markets) >= limit:
                            break
                    
                    if len(all_markets) >= limit:
                        break
                
                # Check for pagination cursor
                cursor = response.get("cursor")
                if not cursor:
                    break  # No more pages
            
            return all_markets[:limit]
        except Exception as e:
            print(f"Error fetching events with markets: {e}")
            return all_markets  # Return what we got so far
    
    def get_market(self, market_ticker: str) -> Optional[Dict]:
        """
        Get detailed information about a specific market.
        
        Args:
            market_ticker: The ticker symbol for the market
        
        Returns:
            Market dictionary with full details
        """
        try:
            response = self._make_request("GET", f"/markets/{market_ticker}")
            return response.get("market")
        except Exception as e:
            print(f"Error fetching market {market_ticker}: {e}")
            return None
    
    def get_market_orderbook(self, market_ticker: str) -> Optional[Dict]:
        """
        Get the orderbook for a market.
        
        Args:
            market_ticker: The ticker symbol for the market
        
        Returns:
            Orderbook data with bids and asks
        """
        try:
            response = self._make_request("GET", f"/markets/{market_ticker}/orderbook")
            return response
        except Exception as e:
            print(f"Error fetching orderbook for {market_ticker}: {e}")
            return None
    
    def get_portfolio(self) -> Optional[Dict]:
        """Get current portfolio information."""
        try:
            response = self._make_request("GET", "/portfolio")
            return response
        except Exception as e:
            print(f"Error fetching portfolio: {e}")
            return None
    
    def place_order(self, market_ticker: str, side: str, action: str, 
                   count: int, price: int, order_type: str = "limit") -> Optional[Dict]:
        """
        Place an order on Kalshi.
        
        Args:
            market_ticker: The ticker symbol for the market
            side: 'yes' or 'no'
            action: 'buy' or 'sell'
            count: Number of contracts
            price: Price in cents (0-100)
            order_type: 'limit' or 'market'
        
        Returns:
            Order response dictionary
        """
        try:
            payload = {
                "ticker": market_ticker,
                "side": side,
                "action": action,
                "count": count,
                "price": price,
                "type": order_type
            }
            response = self._make_request("POST", "/portfolio/orders", json=payload)
            return response
        except Exception as e:
            print(f"Error placing order: {e}")
            return None

