# Polymarket Kalshi Arbitrage Bot

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-PEP%208-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

A production-ready Python bot that identifies and executes arbitrage opportunities in Kalshi prediction markets. The bot analyzes market inefficiencies where contract probabilities don't sum to 100%, calculates net profit after fees, and can automatically execute trades when profitable opportunities are detected.

**Repository**: [polymarket-kalshi-arbitrage-trading-bot-v1](https://github.com/apemoonspin/polymarket-kalshi-arbitrage-trading-bot-v1)

## Overview

This project demonstrates production-ready software engineering practices:

- **API Integration**: Robust client with rate limiting, retry logic, and comprehensive error handling
- **Financial Analysis**: Accurate fee calculations and profit modeling with real-world trading considerations
- **Algorithm Design**: Efficient market scanning algorithms that filter and prioritize opportunities
- **Software Engineering**: Clean architecture, type hints, modular design, and comprehensive documentation
- **Production Readiness**: Error handling, configuration management, and safe defaults

### Key Achievements

- ✅ **Modular Architecture**: Clean separation of concerns with single-responsibility modules
- ✅ **Type Safety**: Comprehensive type hints for better IDE support and maintainability
- ✅ **Error Resilience**: Graceful handling of API failures, rate limits, and edge cases
- ✅ **Financial Accuracy**: Precise fee calculations ensuring realistic profit estimates
- ✅ **Production Ready**: Environment-based configuration, logging, and safe execution defaults

## Features

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

- **`bot.py`** - Arbitrage bot: finds arbitrage and immediate trade opportunities
- **`bot-v2.py`** - High odds scanner: finds markets with specific YES/NO probability ranges
- **`kalshi_client.py`** - API abstraction layer with rate limiting, retry logic, and error handling
- **`arbitrage_analyzer.py`** - Business logic for detecting probability-based arbitrage
- **`high_odds_analyzer.py`** - Filtering logic for probability-based market selection
- **`trade_executor.py`** - Orderbook analysis and trade execution engine
- **`fee_calculator.py`** - Fee calculation module with tiered fee structure support


### Design Decisions

- **Modular Design**: Each module has a single responsibility
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

# Run the bot
python bot.py
```

## Quick Reference Commands

All commands grouped for easy copy-paste.

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

## How It Works

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
- **Market Hours**: Kalshi operates nearly 24/7 with maintenance windows
- **Risk**: Arbitrage opportunities may be fleeting and require quick execution
- **Liquidity**: Ensure markets have sufficient liquidity before executing trades
- **Testing**: Test thoroughly with small positions before scaling up
- **Auto-Execute Warning**: The `--auto-execute` flag will automatically place trades. Use with extreme caution and test thoroughly first. Always monitor your account and positions.
- **Order Execution**: Limit orders are used by default for safety. Market orders may execute at worse prices but provide instant execution.

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

- **API Design**: Clean abstraction layer for external API integration
- **Error Handling**: Comprehensive exception handling with graceful degradation
- **Rate Limiting**: Intelligent rate limit detection and backoff strategies
- **Financial Modeling**: Accurate fee calculations and profit analysis
- **Algorithm Optimization**: Efficient filtering and prioritization algorithms
- **Code Quality**: Type hints, docstrings, and PEP 8 compliance
- **Configuration Management**: Environment-based configuration with validation
- **Production Practices**: Safe defaults, logging, and comprehensive testing utilities

### Code Quality Metrics

- **5 Core Modules**: Clean, focused, single-responsibility design
- **~1,674 Lines**: Well-documented, maintainable codebase
- **Type Hints**: Throughout for better IDE support and type safety
- **Error Handling**: Comprehensive try-catch blocks with meaningful error messages
- **Documentation**: Extensive docstrings and README documentation

### Real-World Application

This bot solves a real financial problem:
- Identifies market inefficiencies in prediction markets
- Calculates realistic profit estimates after fees
- Provides actionable trading recommendations
- Can execute trades automatically (with safety defaults)

## Author

**DexorynLabs**

- **GitHub**: [apemoonspin](https://github.com/apemoonspin/polymarket-kalshi-arbitrage-trading-bot-v1)
- **Telegram**: [@apemoonspin](https://t.me/ApeMoonSpin)

Built with Python 3.8+, demonstrating production-ready software engineering practices.

---

**Portfolio Project**: This project demonstrates proficiency in API integration, financial analysis, algorithm design, and software engineering best practices. The codebase showcases clean architecture, comprehensive error handling, and production-ready code quality.

