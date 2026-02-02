import asyncio
import os
import signal
import time
from typing import List, Dict, Any
from kalshi_client import KalshiClient
from kalshi_ws_client import KalshiWSClient
from market_store import MarketStore
from arbitrage_analyzer import ArbitrageAnalyzer
from trade_executor import TradeExecutor

class RealTimeArbitrageBot:
    """
    High-frequency arbitrage bot using Kalshi WebSockets.
    """
    
    def __init__(self):
        self.rest_client = KalshiClient()
        self.ws_client = KalshiWSClient()
        self.store = MarketStore(self.rest_client)
        self.analyzer = ArbitrageAnalyzer()
        self.executor = TradeExecutor(self.rest_client)
        
        self.active_tickers: List[str] = []
        self.event_tickers: Dict[str, List[str]] = {}  # event_ticker -> list of market tickers
        self.is_running = False
        self.msg_count = 0
        self.start_time = time.time()
        self.last_alert: Dict[str, float] = {}  # ticker/event -> timestamp of last alert

    async def start(self):
        """Start the real-time bot."""
        print("Starting Real-time Arbitrage Bot...")
        self.is_running = True
        self.start_time = time.time()
        
        # Start status logger
        asyncio.create_task(self._status_logger())
        
        # 1. Fetch a larger pool of markets and filter for quality
        print("Fetching and filtering markets...")
        all_markets = self.rest_client.get_events_with_markets(limit=200)
        
        if not all_markets:
            print("WARNING: No markets returned from API.")
            return

        # Filter for active markets with 24h volume
        active_markets = [m for m in all_markets 
                         if str(m.get('status', '')).lower() in ['open', 'active']
                         and m.get('volume_24h', 0) > 0]
        
        if not active_markets:
            print(f"WARNING: No markets with 24h volume. Using all active markets as fallback.")
            active_markets = [m for m in all_markets 
                            if str(m.get('status', '')).lower() in ['open', 'active']]
        
        # Sort by 24h volume (higher activity = more arbitrage opportunities)
        active_markets.sort(key=lambda x: x.get('volume_24h', 0) or 0, reverse=True)
        
        # Group markets by event_ticker for multi-way arbitrage
        event_groups: Dict[str, List[Dict]] = {}
        for market in active_markets:
            event_ticker = market.get('event_ticker', market.get('ticker'))
            if event_ticker not in event_groups:
                event_groups[event_ticker] = []
            event_groups[event_ticker].append(market)
        
        # Select top events by combined 24h volume
        event_volumes = []
        for event_ticker, markets in event_groups.items():
            total_24h_vol = sum(m.get('volume_24h', 0) or 0 for m in markets)
            event_volumes.append((event_ticker, markets, total_24h_vol))
        
        event_volumes.sort(key=lambda x: x[2], reverse=True)
        
        # Take top 20 events (which may have multiple markets each)
        selected_events = event_volumes[:20]
        
        # Build ticker lists
        selected_markets = []
        for event_ticker, markets, vol in selected_events:
            self.event_tickers[event_ticker] = [m['ticker'] for m in markets]
            selected_markets.extend(markets)
        
        self.active_tickers = [m['ticker'] for m in selected_markets]
        
        print(f"Selected {len(selected_events)} events with {len(self.active_tickers)} total markets.")
        print(f"Top 5 events by 24h volume:")
        for event_ticker, markets, vol in selected_events[:5]:
            print(f"  - {event_ticker}: {len(markets)} markets, 24h Vol: {vol:,.0f}")

        # 2. Connect WebSocket
        await self.ws_client.connect()

        # 3. Sync initial state and subscribe
        # We do this in batches to avoid overwhelming the REST API
        for i in range(0, len(self.active_tickers), 5):
            batch = self.active_tickers[i:i+5]
            sync_tasks = [self.store.sync_market(ticker) for ticker in batch]
            await asyncio.gather(*sync_tasks)
            
            # Subscribe to ticker, orderbook, and trade updates
            await self.ws_client.subscribe("ticker_v2", batch, self._on_ticker_update)
            await self.ws_client.subscribe("orderbook_delta", batch, self._on_orderbook_update)
            await self.ws_client.subscribe("trade", batch, self._on_trade_update)
            
            # Small delay between batches
            await asyncio.sleep(0.5)

        print("Bot is fully operational and listening for updates.")
        
        # Keep the bot running
        while self.is_running:
            await asyncio.sleep(1)

    async def _on_ticker_update(self, data: Dict[str, Any]):
        """Callback for ticker updates."""
        self.msg_count += 1
        self.store.handle_ticker_update(data)
        ticker = data.get("msg", {}).get("ticker")
        await self._check_arbitrage(ticker)

    async def _on_orderbook_update(self, data: Dict[str, Any]):
        """Callback for orderbook updates."""
        self.msg_count += 1
        self.store.handle_orderbook_delta(data)
        ticker = data.get("msg", {}).get("market_ticker")
        await self._check_arbitrage(ticker)

    async def _on_trade_update(self, data: Dict[str, Any]):
        """Callback for trade updates - signals real market activity."""
        self.msg_count += 1
        ticker = data.get("msg", {}).get("market_ticker")
        # Trade events indicate real activity - check for arbitrage opportunities
        await self._check_arbitrage(ticker)

    async def _status_logger(self):
        """Periodically log bot status."""
        while self.is_running:
            await asyncio.sleep(60)
            uptime = int(time.time() - self.start_time)
            print(f"[Status] Uptime: {uptime}s | Messages Processed: {self.msg_count} | Monitoring: {len(self.active_tickers)} markets")

    async def _check_arbitrage(self, ticker: str):
        """Analyze a market for arbitrage opportunities."""
        if not ticker:
            return
        
        current_time = time.time()
        alert_cooldown = 30  # Only alert once per 30 seconds for the same opportunity
        
        # 1. Single-market arbitrage check
        market_summary = self.store.get_market_summary(ticker)
        if market_summary:
            # Check if we alerted for this ticker recently
            if ticker not in self.last_alert or (current_time - self.last_alert[ticker]) > alert_cooldown:
                opportunity = self.analyzer.analyze_market(market_summary)
                
                if opportunity:
                    self.last_alert[ticker] = current_time
                    print(f"\n!!! SINGLE-MARKET ARBITRAGE FOUND in {ticker} !!!")
                    print(f"Deviation: {opportunity.deviation:.2f}%")
                    print(f"Net Profit: ${opportunity.net_profit:.2f}")
                    print(f"Days to expiration: {opportunity.days_to_expiration:.1f}\n")
                    
                    if os.getenv("AUTO_EXECUTE", "false").lower() == "true":
                        print(f"Executing trades for {ticker}...")
                        # self.executor.execute_arbitrage(opportunity)
        
        # 2. Multi-way arbitrage check (event-level)
        # Find the event this ticker belongs to
        event_ticker = None
        for evt, tickers in self.event_tickers.items():
            if ticker in tickers:
                event_ticker = evt
                break
        
        if event_ticker and len(self.event_tickers[event_ticker]) > 1:
            # Check if we alerted for this event recently
            event_key = f"event:{event_ticker}"
            if event_key not in self.last_alert or (current_time - self.last_alert[event_key]) > alert_cooldown:
                # Get all markets for this event
                event_markets = []
                for t in self.event_tickers[event_ticker]:
                    summary = self.store.get_market_summary(t)
                    if summary:
                        event_markets.append(summary)
                
                if len(event_markets) > 1:
                    # Check for multi-way arbitrage
                    opportunity = self.analyzer.analyze_event(event_markets)
                    
                    if opportunity:
                        self.last_alert[event_key] = current_time
                        print(f"\n!!! MULTI-WAY ARBITRAGE FOUND in event {event_ticker} !!!")
                        print(f"Total Probability: {opportunity.total_probability:.2f}%")
                        print(f"Deviation: {opportunity.deviation:.2f}%")
                        print(f"Net Profit: ${opportunity.net_profit:.2f}")
                        print(f"Markets involved: {len(event_markets)}")
                        print(f"Days to expiration: {opportunity.days_to_expiration:.1f}\n")
                        
                        if os.getenv("AUTO_EXECUTE", "false").lower() == "true":
                            print(f"Executing trades for event {event_ticker}...")
                            # self.executor.execute_arbitrage(opportunity)

    async def stop(self):
        """Gracefully stop the bot."""
        print("Stopping bot...")
        self.is_running = False
        # Cancel the status logger
        for task in asyncio.all_tasks():
            if task.get_coro().__name__ == "_status_logger":
                task.cancel()
        await self.ws_client.stop()

if __name__ == "__main__":
    bot = RealTimeArbitrageBot()
    
    loop = asyncio.get_event_loop()
    
    # Handle signals
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(bot.stop()))
        
    try:
        loop.run_until_complete(bot.start())
    except Exception as e:
        print(f"Bot exited with error: {e}")
    finally:
        loop.close()
