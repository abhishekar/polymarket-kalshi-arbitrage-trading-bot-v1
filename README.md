# Polymarket Kalshi Arbitrage Bot

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-PEP%208-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

A production-ready Python bot that identifies and executes arbitrage opportunities in Kalshi prediction markets using **real-time WebSocket streaming**. The bot analyzes market inefficiencies where contract probabilities don't sum to 100%, calculates net profit after fees, and can automatically execute trades when profitable opportunities are detected.

**Repository**: [polymarket-kalshi-arbitrage-trading-bot-v1](https://github.com/apemoonspin/polymarket-kalshi-arbitrage-trading-bot-v1)

## Overview

This project demonstrates production-ready software engineering practices:

- **Real-Time Trading**: WebSocket integration for sub-second reaction to market movements
- **API Integration**: Robust client with rate limiting, retry logic, and comprehensive error handling
- **Financial Analysis**: Accurate fee calculations and profit modeling with real-world trading considerations
- **Algorithm Design**: Efficient market scanning algorithms that filter and prioritize opportunities
- **Software Engineering**: Clean architecture, type hints, modular design, and comprehensive documentation
- **Production Readiness**: Error handling, configuration management, and safe defaults

### Key Achievements

- ✅ **WebSocket Real-Time Trading**: Sub-second reaction time to price movements
- ✅ **Multi-Way Arbitrage Detection**: Detects probability mismatches across multiple related markets
- ✅ **Modular Architecture**: Clean separation of concerns with single-responsibility modules
- ✅ **Type Safety**: Comprehensive type hints for better IDE support and maintainability
- ✅ **Error Resilience**: Graceful handling of API failures, rate limits, and edge cases
- ✅ **Financial Accuracy**: Precise fee calculations ensuring realistic profit estimates
- ✅ **Production Ready**: Environment-based configuration, logging, and safe execution defaults

## Features

### Real-Time WebSocket Bot (`bot_ws.py`) - **NEW!**
- **Live Market Monitoring**: Subscribes to `ticker_v2`, `orderbook_delta`, and `trade` channels for real-time updates
- **Event-Level Analysis**: Groups related markets by event to detect multi-way arbitrage opportunities
- **Smart Market Selection**: Filters by 24-hour volume to focus on active markets
- **Dual Detection**: Finds both single-market and multi-way arbitrage opportunities
- **Alert Cooldown**: Prevents spam with intelligent alert throttling

### Classic Polling Bots
- **Dual Opportunity Detection**: Scans for both arbitrage and immediate trade opportunities
- **Arbitrage Detection**: Identifies markets where YES + NO probabilities don't sum to 100%
- **Immediate Trades**: Finds orderbook spreads where bid > ask (instant profit)
- **Fee Calculation**: Accurately calculates trading fees based on contract prices
- **Profit Analysis**: Computes net profit after fees and ranks by profitability
- **Continuous Monitoring**: Optional continuous scanning mode
- **Auto-Execution**: Optional automatic trade execution (use with caution)

## Architecture

The codebase follows a modular architecture with clear separation of concerns:

### Core Modules

#### Real-Time Trading (NEW)
- **`bot_ws.py`** - Real-time arbitrage bot using WebSocket streaming
- **`kalshi_ws_client.py`** - WebSocket client with authentication, heartbeat handling, and auto-reconnect
- **`market_store.py`** - In-memory data store for real-time market state tracking

#### Classic Polling Bots
- **`bot.py`** - Arbitrage bot: finds arbitrage and immediate trade opportunities
- **`bot-v2.py`** - High odds scanner: finds markets with specific YES/NO probability ranges
- **`parlay_scanner.py`** - Sports parlay analyzer: breaks down parlays to find value

#### Shared Infrastructure
- **`kalshi_client.py`** - REST API abstraction layer with rate limiting, retry logic, and error handling
- **`arbitrage_analyzer.py`** - Business logic for detecting single-market and multi-way arbitrage
- **`high_odds_analyzer.py`** - Filtering logic for probability-based market selection
- **`parlay_analyzer.py`** - Parlay breakdown and fair price calculation logic
- **`trade_executor.py`** - Orderbook analysis and trade execution engine
- **`fee_calculator.py`** - Fee calculation module with tiered fee structure support


### Design Decisions

- **Modular Design**: Each module has a single responsibility
- **Real-Time Architecture**: Event-driven WebSocket handling with async/await patterns
- **Error Handling**: Comprehensive try-catch blocks with graceful degradation
- **Rate Limiting**: Built-in rate limiting to respect API constraints
- **Type Safety**: Type hints throughout for better IDE support and maintainability
- **Configuration**: Environment-based configuration for flexibility
- **Fee Accuracy**: Precise fee calculations ensure profit estimates are realistic

## Quick Start

```bash
# Clone the repository
git clone https://github.com/dexorynLabs/polymarket-kalshi-arbitrage-trading-bot-v1.git
cd polymarket-kalshi-arbitrage-trading-bot-v1

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Kalshi API credentials

# Run the real-time WebSocket bot (RECOMMENDED)
caffeinate -i python3 bot_ws.py

# Or run the classic polling bot
python bot.py
```

## Quick Reference Commands

All commands grouped for easy copy-paste.

### bot_ws.py - Real-Time WebSocket Bot (NEW)

```bash
# Run the real-time bot (prevents Mac from sleeping)
caffeinate -i python3 bot_ws.py

# Enable auto-execution in .env (USE WITH CAUTION)
# Edit .env and set: AUTO_EXECUTE=true

# The bot will:
# - Connect to Kalshi WebSocket
# - Monitor top 20 events by 24h volume
# - Detect single-market and multi-way arbitrage
# - Alert when opportunities are found
# - Log status every 60 seconds
```

### bot.py - Arbitrage Bot

```bash
# Basic scan (prediction markets, default)
python3 bot.py

# Scan sports parlays instead
python3 bot.py --source markets

# Scan more markets, show all results
python3 bot.py --limit 5000 --all

# Continuous monitoring (every 60 seconds)
python3 bot.py --continuous --interval 60

# Only arbitrage or only trades
python3 bot.py --arbitrage-only
python3 bot.py --trades-only

# Auto-execute (USE WITH CAUTION)
python3 bot.py --auto-execute

# Filter by minimum liquidity ($500)
python3 bot.py --min-liquidity 50000
```

### bot-v2.py - High Odds Scanner

```bash
# Find high YES probability markets (default: 85-92%)
python3 bot-v2.py

# Find low YES probability markets (high NO odds)
python3 bot-v2.py --min-odds 0.05 --max-odds 0.15

# Markets expiring within 24 hours
python3 bot-v2.py --max-days 1

# High liquidity markets only ($10,000+)
python3 bot-v2.py --min-liquidity 1000000

# Output as JSON
python3 bot-v2.py --output json

# Combined filters (85-95% YES, 7 days, $5000+ liquidity)
python3 bot-v2.py --min-odds 0.85 --max-odds 0.95 --max-days 7 --min-liquidity 500000

# Debug mode to see raw market data
python3 bot-v2.py --debug
```

### parlay_scanner.py - Sports Parlay Analyzer

```bash
# Scan for value parlays (shows edge between fair price and actual price)
python3 parlay_scanner.py

# Analyze a specific parlay by ticker
python3 parlay_scanner.py --ticker KXMVESPORTSMULTIGAMEEXTENDED-S2025...

# Only show parlays with 5%+ edge
python3 parlay_scanner.py --min-edge 5

# Only show parlays with 5 or fewer legs
python3 parlay_scanner.py --max-legs 5

# Only show parlays with trading activity
python3 parlay_scanner.py --min-volume 1

# Detailed output showing all legs
python3 parlay_scanner.py --output detail

# JSON output
python3 parlay_scanner.py --output json

# Fast scan without fetching leg prices (no fair price calculation)
python3 parlay_scanner.py --no-fetch-legs
```

## Setup

### Prerequisites

- Python 3.8+
- Kalshi API credentials (API key and secret)
- pip (Python package manager)

### Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your Kalshi API credentials:
```bash
# Copy the example file
cp .env.example .env
```

Then edit `.env` and replace the placeholder values with your actual credentials:
```
# From your Kalshi account:
# - API Key ID goes in KALSHI_API_KEY
# - Private Key goes in KALSHI_API_SECRET
KALSHI_API_KEY=your_api_key_id_here
KALSHI_API_SECRET=your_private_key_here
KALSHI_API_BASE_URL=https://api.elections.kalshi.com/trade-api/v2
MIN_PROFIT_PER_DAY=0.1
MAX_POSITION_SIZE=1000
```

**Note**: In your Kalshi account settings:
- **API Key ID** → use for `KALSHI_API_KEY`
- **Private Key** → use for `KALSHI_API_SECRET`

### Optional Configuration

You can adjust these parameters in `.env`:

#### Common Settings (both scripts)

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_LIMIT` | `30000` | Default number of markets to fetch |
| `MIN_LIQUIDITY` | `10000` | Minimum liquidity in cents (bot.py: $100, bot-v2.py: $10,000) |

#### bot.py Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_PROFIT_PER_DAY` | `0.1` | Minimum profit per day threshold for arbitrage ($0.10) |
| `MAX_POSITION_SIZE` | `1000` | Maximum position size for trades (contracts) |
| `MIN_PROFIT_CENTS` | `2` | Minimum profit in cents per contract for immediate trades |

#### bot-v2.py Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_ODDS` | `0.85` | Minimum YES probability (85%) |
| `MAX_ODDS` | `0.92` | Maximum YES probability (92%) |
| `MAX_DAYS` | `3` | Maximum days until market closes |

**Note**: The bot automatically calculates the minimum profitable deviation based on actual trading fees. Any opportunity with positive net profit (after fees) will be considered, ensuring you don't miss profitable opportunities even if they're very small.

## Usage

This project includes two main scripts:
- **bot.py** - Arbitrage Bot for finding trading opportunities
- **bot-v2.py** - High Odds Scanner for finding markets by probability range

---

### bot.py - Arbitrage Bot

Scans markets for arbitrage and immediate trade opportunities.

#### Data Sources

The bot can fetch from two different Kalshi API endpoints:

| Source | Flag | Description |
|--------|------|-------------|
| Events | `--source events` (default) | Prediction markets (politics, economics, etc.) with pagination support |
| Markets | `--source markets` | Sports parlays |

#### Single Scan

Run a one-time scan (automatically scans both arbitrage and immediate trades):
```bash
python3 bot.py
```

The bot will automatically:
- Scan for immediate trade opportunities (buy low, sell high instantly)
- Scan for arbitrage opportunities (probability mismatches)
- Compare both types and show recommendations
- Display the best opportunities from each category

Display all opportunities (not just top 10):
```bash
python3 bot.py --all
```

Scan more markets:
```bash
python3 bot.py --limit 5000
```

#### Continuous Monitoring

Run continuous scanning (checks every 5 minutes by default):
```bash
python3 bot.py --continuous
```

Custom scan interval (in seconds):
```bash
python3 bot.py --continuous --interval 60
```

#### Automatic Trade Execution

**⚠️ WARNING**: Automatically execute trades (USE WITH CAUTION):
```bash
python3 bot.py --auto-execute
```

With `--auto-execute`, the bot will:
- Automatically execute immediate trade opportunities (instant profit)
- Prioritize immediate trades over arbitrage (no waiting required)
- Execute trades only when net profit is positive after fees

#### Specific Scanning Modes

If you want to scan only one type of opportunity:
```bash
# Only immediate trades
python3 bot.py --trades-only

# Only arbitrage opportunities
python3 bot.py --arbitrage-only
```

#### bot.py Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--source` | `events` | Data source: `events` (prediction markets) or `markets` (sports parlays) |
| `--limit` | `30000` (env: `DEFAULT_LIMIT`) | Maximum number of markets to scan |
| `--continuous` | off | Run continuous scanning mode |
| `--interval` | `300` | Scan interval in seconds for continuous mode |
| `--all` | off | Display all opportunities (not just top 10) |
| `--auto-execute` | off | Automatically execute profitable trades (USE WITH CAUTION) |
| `--trades-only` | off | Scan ONLY for immediate trade opportunities |
| `--arbitrage-only` | off | Scan ONLY for arbitrage opportunities |
| `--min-liquidity` | `10000` | Minimum liquidity in cents ($100) |
| `--max-scans` | infinite | Maximum number of scans in continuous mode |

---

### bot-v2.py - High Odds Scanner

Finds markets with specific YES/NO probability ranges. Useful for finding high-confidence markets or markets with favorable NO odds.

#### Use Cases

- **High YES probability**: Find markets likely to resolve YES (e.g., 85-95%)
- **High NO probability**: Find markets likely to resolve NO by searching low YES odds (e.g., 5-15%)
- **Short-term markets**: Filter by expiration date to find markets closing soon
- **Liquid markets**: Filter by liquidity to find actively traded markets

#### Basic Usage

```bash
# Find high YES probability markets (default: 85-92%)
python3 bot-v2.py

# Find low YES probability markets (high NO odds)
python3 bot-v2.py --min-odds 0.05 --max-odds 0.15

# Markets expiring within 24 hours
python3 bot-v2.py --max-days 1

# Combined filters
python3 bot-v2.py --min-odds 0.85 --max-odds 0.95 --max-days 7 --min-liquidity 500000
```

#### Output Formats

```bash
# Table format (default) - human readable
python3 bot-v2.py --output table

# JSON format - for programmatic use
python3 bot-v2.py --output json
```

#### bot-v2.py Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--source` | `events` | Data source: `events` (prediction markets) or `markets` (sports parlays) |
| `--limit` | `30000` (env: `DEFAULT_LIMIT`) | Maximum number of markets to fetch from API |
| `--min-odds` | `0.85` (env: `MIN_ODDS`) | Minimum YES probability (0.0-1.0) |
| `--max-odds` | `0.92` (env: `MAX_ODDS`) | Maximum YES probability (0.0-1.0) |
| `--min-liquidity` | `1000000` (env: `MIN_LIQUIDITY`) | Minimum liquidity in cents ($10,000) |
| `--max-days` | `3` (env: `MAX_DAYS`) | Maximum days until market closes |
| `--output` | `table` | Output format: `table` or `json` |
| `--debug` | off | Show debug information about market data |

---

### parlay_scanner.py - Sports Parlay Analyzer

Analyzes sports parlay markets by breaking down their individual legs, fetching each leg's probability, and comparing the combined "fair" probability to the actual parlay price to identify potential value.

#### How It Works

1. Fetches sports parlay markets from Kalshi's `/markets` endpoint
2. For each parlay, extracts the individual legs (player props, game outcomes, etc.)
3. Fetches the current price/probability for each leg
4. Calculates the "fair" parlay price by multiplying leg probabilities
5. Compares fair price to actual price to find edge (mispriced parlays)

#### Basic Usage

```bash
# Scan for value parlays
python3 parlay_scanner.py

# Analyze a specific parlay
python3 parlay_scanner.py --ticker KXMVESPORTSMULTIGAMEEXTENDED-S2025...

# Filter by minimum edge (5%+ difference between fair and actual)
python3 parlay_scanner.py --min-edge 5

# Limit to smaller parlays (5 legs or fewer)
python3 parlay_scanner.py --max-legs 5

# Only show parlays with trading activity
python3 parlay_scanner.py --min-volume 1
```

#### Output Formats

```bash
# Summary table (default)
python3 parlay_scanner.py --output table

# Detailed breakdown showing all legs
python3 parlay_scanner.py --output detail

# JSON format
python3 parlay_scanner.py --output json
```

#### parlay_scanner.py Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--ticker` | None | Analyze a specific parlay by ticker |
| `--limit` | `1000` | Maximum number of parlays to fetch |
| `--min-edge` | `0` | Minimum absolute edge in percentage points |
| `--max-legs` | None | Maximum number of legs per parlay |
| `--min-volume` | `0` | Minimum volume + open interest |
| `--output` | `table` | Output format: `table`, `detail`, or `json` |
| `--no-fetch-legs` | off | Skip fetching leg prices (faster but no fair price calculation) |
| `--show-all` | off | Show all parlays including those without calculable edge |

#### Understanding Edge

- **Positive edge**: Parlay is UNDERPRICED - potential value betting YES
- **Negative edge**: Parlay is OVERPRICED - potential value betting NO
- **Edge calculation**: Fair Price - Actual Price (in percentage points)

**Example:**
- Parlay has 4 legs with probabilities: 65%, 72%, 68%, 55%
- Fair price = 0.65 × 0.72 × 0.68 × 0.55 = 17.5%
- Actual parlay price = 15%
- Edge = 17.5% - 15% = +2.5% (UNDERPRICED)

## How It Works

The bot provides two modes of operation:

### Real-Time WebSocket Mode (`bot_ws.py`) - RECOMMENDED

The WebSocket bot provides sub-second reaction times to market changes:

**How it works:**
1. **Connects** to Kalshi's WebSocket API with RSA-PSS authentication
2. **Filters Markets** by 24-hour volume to focus on active opportunities
3. **Groups by Event** to enable multi-way arbitrage detection
4. **Subscribes** to `ticker_v2`, `orderbook_delta`, and `trade` channels
5. **Monitors** for two types of opportunities:
   - **Single-Market Arbitrage**: YES + NO probabilities ≠ 100%
   - **Multi-Way Arbitrage**: Sum of all event outcomes ≠ 100%
6. **Alerts** when profitable opportunities are detected (with cooldown to prevent spam)
7. **Auto-Reconnects** with exponential backoff if connection is lost

**Example Multi-Way Arbitrage:**
Event: "Next Iran Leader"
- Outcome A: 30% probability
- Outcome B: 25% probability
- Outcome C: 22% probability
- Outcome D: 15% probability
- Total: 92% (should be 100%)
- **Arbitrage**: Buy all outcomes for 92¢, guaranteed to win $1.00 (8¢ profit per set)

**WebSocket Architecture:**
```
Kalshi WebSocket → Message Handler → Market Store → Arbitrage Analyzer
                                                   → Alert (if opportunity found)
```

### Classic Polling Mode (`bot.py`)

The bot scans Kalshi markets for two types of profitable opportunities:

### 1. Arbitrage Opportunities

Arbitrage occurs when YES + NO probabilities don't sum to 100%:

**Example:**
- YES contracts trading at 52¢
- NO contracts trading at 50¢
- Total: 102% (2% arbitrage opportunity)

**How it works:**
1. Fetches active markets from Kalshi API
2. Calculates total probability (YES price + NO price)
3. Identifies markets where total ≠ 100%
4. Calculates gross profit and net profit (after fees)
5. Ranks by profit per day based on expiration date

### 2. Immediate Trade Opportunities

Immediate trades occur when bid price > ask price (can buy low, sell high instantly):

**Example:**
- Someone wants to buy YES at 43¢ (bid)
- Someone wants to sell YES at 42¢ (ask)
- Profit: 1¢ per contract (minus fees)

**How it works:**
1. Scans orderbooks for profitable spreads
2. Identifies cases where bid > ask
3. Calculates net profit after fees
4. Optionally executes trades automatically

### Comparison

The bot compares both types and recommends the best option:
- **Immediate Trades**: Instant profit, no waiting required
- **Arbitrage**: Time-based profit, requires holding until expiration

## Fee Structure

The bot uses an approximation of Kalshi's fee structure:
- Contracts priced near 50¢: ~3.5% fee
- Contracts at extremes (near 0¢ or 100¢): ~1% fee
- Maker orders (limit orders): 50% discount on fees

**Note**: Actual fees may vary. Check Kalshi's official fee schedule for precise values.

## Example Output

```
[2024-01-15 10:30:00] Scanning 100 markets for arbitrage opportunities...
Found 87 active markets. Analyzing...

============================================================
Found 3 arbitrage opportunities!
============================================================

[1] ============================================================
Market: Will Bitcoin reach $50,000 by end of month?
Ticker: BTC-50K-JAN
Total Probability: 102.5%
Deviation from 100%: 2.50%
Expiration: 2024-01-31 23:59:59
Days to Expiration: 16.50

Profit Analysis:
  Gross Profit: $25.00
  Net Profit (after fees): $22.50
  Profit per Day: $1.36

Recommended Trades:
  1. SELL 100 contracts of BTC-50K-JAN-YES at 52¢ (side: yes)
  2. SELL 100 contracts of BTC-50K-JAN-NO at 50¢ (side: no)
============================================================
```

## Important Notes

- **API Access**: You need valid Kalshi API credentials to use this bot
- **WebSocket Credentials**: Requires RSA-PSS signing - ensure your `KALSHI_API_SECRET` is properly formatted in `.env`
- **Market Hours**: Kalshi operates nearly 24/7 with maintenance windows
- **Risk**: Arbitrage opportunities may be fleeting and require quick execution
- **Liquidity**: Ensure markets have sufficient liquidity before executing trades
- **Testing**: Test thoroughly with small positions before scaling up
- **Auto-Execute Warning**: The `--auto-execute` flag (or `AUTO_EXECUTE=true` in `.env` for WebSocket bot) will automatically place trades. Use with extreme caution and test thoroughly first. Always monitor your account and positions.
- **Order Execution**: Limit orders are used by default for safety. Market orders may execute at worse prices but provide instant execution.
- **Keep Mac Awake**: Use `caffeinate -i python3 bot_ws.py` to prevent your Mac from sleeping while the bot runs

## Real-Time Performance

The WebSocket bot (`bot_ws.py`) provides significant advantages over polling:

| Feature | WebSocket (`bot_ws.py`) | Polling (`bot.py`) |
|---------|-------------------------|---------------------|
| **Reaction Time** | <1 second | 60-300 seconds |
| **Data Freshness** | Real-time | Stale (depends on scan interval) |
| **Multi-Way Arbitrage** | ✅ Automatic | ❌ Not detected |
| **Event Grouping** | ✅ Yes | ❌ No |
| **Volume Filtering** | ✅ 24h volume | ❌ Total volume |
| **Connection** | Persistent WebSocket | Repeated REST calls |
| **CPU Usage** | Low (event-driven) | High (continuous polling) |

### Example Output (WebSocket Bot)

```
Starting Real-time Arbitrage Bot...
Fetching and filtering markets...
Selected 20 events with 54 total markets.
Top 5 events by 24h volume:
  - KXPRIMEENGCONSUMPTION-30: 7 markets, 24h Vol: 3,574
  - KXMOONMAN-31: 4 markets, 24h Vol: 794
  - KXNEXTIRANLEADER-45JAN01: 6 markets, 24h Vol: 478

Connected to Kalshi WebSocket at wss://api.elections.kalshi.com/trade-api/ws/v2
Bot is fully operational and listening for updates.

!!! MULTI-WAY ARBITRAGE FOUND in event KXNEXTIRANLEADER-45JAN01 !!!
Total Probability: 91.00%
Deviation: 9.00%
Net Profit: $8.78
Markets involved: 6
Days to expiration: 45.2

[Status] Uptime: 60s | Messages Processed: 142 | Monitoring: 54 markets
```

## Technical Details

### Error Handling

The bot includes comprehensive error handling:
- **API Errors**: Graceful handling of rate limits, network errors, and API failures
- **Data Validation**: Checks for missing or invalid market data before processing
- **Trade Execution**: Validates opportunities before execution to prevent losses
- **Rate Limiting**: Automatic rate limit detection and backoff strategies

### Performance Considerations

- **Efficient Scanning**: Filters markets by liquidity before detailed analysis
- **Rate Limiting**: Built-in delays to respect API constraints
- **Batch Processing**: Processes multiple markets efficiently
- **Memory Management**: Streams data rather than loading everything into memory

### Security

- **Credential Management**: Uses environment variables, never hardcoded
- **API Key Protection**: `.env` file is gitignored
- **Safe Defaults**: Auto-execution disabled by default
- **Input Validation**: Validates all inputs before API calls

## Testing

Before using with real money:

1. **Dry Run**: Run without `--auto-execute` to see opportunities
2. **Small Test**: Start with `--limit 10` and `--min-liquidity 1000`
3. **Monitor**: Watch output and verify behavior matches expectations

## Disclaimer

This bot is for educational and informational purposes only. Trading involves risk, and past performance does not guarantee future results. Always:
- Understand the risks involved
- Test thoroughly before using real money
- Monitor your positions
- Comply with Kalshi's terms of service
- Consult with financial advisors if needed


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Project Highlights

This project showcases several important software engineering skills:

### Technical Skills Demonstrated

- **WebSocket Integration**: Real-time data streaming with authentication and auto-reconnect
- **Async/Await Patterns**: Modern Python async programming for concurrent operations
- **API Design**: Clean abstraction layer for external API integration
- **Error Handling**: Comprehensive exception handling with graceful degradation
- **Rate Limiting**: Intelligent rate limit detection and backoff strategies
- **Financial Modeling**: Accurate fee calculations and profit analysis
- **Algorithm Optimization**: Efficient filtering and prioritization algorithms
- **Event-Driven Architecture**: Reactive programming for real-time market analysis
- **Code Quality**: Type hints, docstrings, and PEP 8 compliance
- **Configuration Management**: Environment-based configuration with validation
- **Production Practices**: Safe defaults, logging, and comprehensive testing utilities

### Code Quality Metrics

- **8 Core Modules**: Clean, focused, single-responsibility design (including 3 new WebSocket modules)
- **~2,500+ Lines**: Well-documented, maintainable codebase
- **Type Hints**: Throughout for better IDE support and type safety
- **Error Handling**: Comprehensive try-catch blocks with meaningful error messages
- **Documentation**: Extensive docstrings and README documentation

### Real-World Application

This bot solves real financial problems:
- Identifies market inefficiencies in prediction markets in **real-time**
- Detects both single-market and **multi-way arbitrage** opportunities
- Calculates realistic profit estimates after fees
- Provides actionable trading recommendations
- Can execute trades automatically (with safety defaults)
- Reacts to market changes in **sub-second timeframes**

## Author

**DexorynLabs**

- **GitHub**: [apemoonspin](https://github.com/apemoonspin/polymarket-kalshi-arbitrage-trading-bot-v1)
- **Telegram**: [@apemoonspin](https://t.me/ApeMoonSpin)

Built with Python 3.8+, demonstrating production-ready software engineering practices.

---

**Portfolio Project**: This project demonstrates proficiency in real-time WebSocket integration, API design, financial analysis, algorithm optimization, and software engineering best practices. The codebase showcases clean architecture, event-driven programming, comprehensive error handling, and production-ready code quality with both real-time and polling architectures.

