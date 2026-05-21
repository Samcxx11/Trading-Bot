# Binance Futures Testnet Trading Bot

A lightweight Python CLI application for placing orders on **Binance Futures Testnet (USDT-M)**. Supports Market, Limit, and Stop-Market orders with structured logging and robust error handling.

---

## Features

- **Market & Limit orders** on Binance Futures Testnet
- **Stop-Market orders** (bonus feature)
- **BUY / SELL** support for all order types
- **CLI interface** with argument validation via `argparse`
- **Structured logging** — dual output to console (INFO) and file (DEBUG)
- **Error handling** — input validation, API errors, network failures
- **Clean architecture** — separated client, order logic, validators, and CLI layers

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package init
│   ├── client.py            # Binance REST API client (HMAC signing, requests)
│   ├── orders.py            # Order placement logic & output formatting
│   ├── validators.py        # Input validation for all order parameters
│   └── logging_config.py    # Dual logging setup (console + file)
├── logs/                    # Log files (auto-created at runtime)
│   ├── sample_market_order.log
│   └── sample_limit_order.log
├── cli.py                   # CLI entry point
├── .env.example             # Template for API credentials
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

### 1. Prerequisites

- Python 3.8+
- A [Binance Futures Testnet](https://testnet.binancefuture.com/) account

### 2. Clone & Install

```bash
git clone https://github.com/yourusername/trading_bot.git
cd trading_bot
pip install -r requirements.txt
```

### 3. Configure API Credentials

1. Go to [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Register/login and generate API credentials
3. Create a `.env` file from the template:

```bash
cp .env.example .env
```

4. Edit `.env` with your credentials:

```
BINANCE_API_KEY=your_actual_testnet_api_key
BINANCE_API_SECRET=your_actual_testnet_api_secret
```

> **Note:** Never commit `.env` to version control.

## Usage

### Place a Market Order

```bash
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Place a Limit Order

```bash
python cli.py order --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.05 --price 2500
```

### Place a Stop-Market Order (Bonus)

```bash
python cli.py order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 100000
```

### Check Current Price

```bash
python cli.py price --symbol BTCUSDT
```

### Check Account Balances

```bash
python cli.py account
```

### View Help

```bash
python cli.py --help
python cli.py order --help
```

## Example Output

### Market Order

```
==============================================
           ORDER REQUEST SUMMARY
==============================================
  Symbol      : BTCUSDT
  Side        : BUY
  Type        : MARKET
  Quantity    : 0.001
==============================================

==============================================
           ORDER RESPONSE DETAILS
==============================================
  Order ID    : 4375028842
  Symbol      : BTCUSDT
  Side        : BUY
  Type        : MARKET
  Status      : FILLED
  Orig Qty    : 0.001
  Executed Qty: 0.001
  Avg Price   : 107234.50
==============================================

  ORDER SUCCESSFUL - ID: 4375028842 | Status: FILLED
```

### Limit Order

```
==============================================
           ORDER REQUEST SUMMARY
==============================================
  Symbol      : ETHUSDT
  Side        : SELL
  Type        : LIMIT
  Quantity    : 0.05
  Price       : 2500.0
==============================================

==============================================
           ORDER RESPONSE DETAILS
==============================================
  Order ID    : 4375029115
  Symbol      : ETHUSDT
  Side        : SELL
  Type        : LIMIT
  Status      : NEW
  Orig Qty    : 0.050
  Executed Qty: 0.000
  Avg Price   : 0.00
==============================================

  ORDER SUCCESSFUL - ID: 4375029115 | Status: NEW
```

## Logging

All API requests, responses, and errors are logged to timestamped files in the `logs/` directory:

```
logs/trading_bot_20260521_121500.log
```

Log files include:
- Full request parameters (DEBUG level)
- API response bodies (DEBUG level)
- Order summaries (INFO level)
- Validation and API errors (ERROR level)

Sample log files from test runs are included in `logs/`.

## Assumptions

1. **Testnet only** — This bot is designed exclusively for the Binance Futures Testnet (`https://testnet.binancefuture.com`). Do not use with mainnet credentials.
2. **USDT-M futures** — All orders target USDT-margined futures contracts.
3. **Supported symbols** — A curated list of 15 common trading pairs is supported (see `validators.py`). This can be extended easily.
4. **Time-in-force** — Limit orders default to GTC (Good Till Cancelled).
5. **No position management** — This bot places individual orders. It does not track open positions or implement trading strategies.
6. **Clock sync** — The client fetches server time from Binance to avoid timestamp rejection issues.

## Error Handling

| Scenario | Handling |
|---|---|
| Invalid symbol | Rejected with list of supported symbols |
| Missing price for LIMIT | Clear error message before API call |
| Invalid quantity | Validated as positive number |
| API key issues | Descriptive error from Binance API |
| Network timeout | Caught and logged with retry suggestion |
| Unexpected API response | Logged at ERROR level with full response |

## Bonus Feature: Stop-Market Orders

The bot supports `STOP_MARKET` orders as a bonus feature. When the market price reaches the specified `--stop-price`, a market order is automatically triggered.

```bash
python cli.py order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 100000
```

## Dependencies

- `requests` — HTTP client for REST API calls
- `python-dotenv` — Environment variable management

No heavy SDK dependencies — all Binance API interaction is done via direct REST calls with HMAC-SHA256 signing.

## License

MIT
