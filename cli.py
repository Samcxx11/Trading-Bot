#!/usr/bin/env python3
"""
Trading Bot CLI — Command-line interface for placing orders
on Binance Futures Testnet (USDT-M).

Usage examples:
    # Market order
    python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

    # Limit order
    python cli.py order --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3000

    # Stop-Market order (bonus)
    python cli.py order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 100000

    # Check current price
    python cli.py price --symbol BTCUSDT

    # Check account info
    python cli.py account
"""

import argparse
import os
import sys

from dotenv import load_dotenv

# Add parent dir to path so `bot` package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.logging_config import setup_logging
from bot.client import BinanceFuturesClient, BinanceClientError, BinanceNetworkError
from bot.validators import validate_order_params
from bot.orders import execute_order


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot (USDT-M)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
  %(prog)s order --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.05 --price 2500
  %(prog)s order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 100000
  %(prog)s price --symbol BTCUSDT
  %(prog)s account
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- order subcommand ---
    order_parser = subparsers.add_parser("order", help="Place an order")
    order_parser.add_argument(
        "--symbol", "-s", required=True,
        help="Trading pair (e.g., BTCUSDT, ETHUSDT)",
    )
    order_parser.add_argument(
        "--side", required=True, choices=["BUY", "SELL", "buy", "sell"],
        help="Order side: BUY or SELL",
    )
    order_parser.add_argument(
        "--type", "-t", dest="order_type", required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET", "market", "limit", "stop_market"],
        help="Order type: MARKET, LIMIT, or STOP_MARKET",
    )
    order_parser.add_argument(
        "--quantity", "-q", required=True,
        help="Order quantity (e.g., 0.001)",
    )
    order_parser.add_argument(
        "--price", "-p", default=None,
        help="Limit price (required for LIMIT orders)",
    )
    order_parser.add_argument(
        "--stop-price", default=None,
        help="Stop trigger price (required for STOP_MARKET orders)",
    )

    # --- price subcommand ---
    price_parser = subparsers.add_parser("price", help="Get current price for a symbol")
    price_parser.add_argument(
        "--symbol", "-s", required=True,
        help="Trading pair (e.g., BTCUSDT)",
    )

    # --- account subcommand ---
    subparsers.add_parser("account", help="Show testnet account info")

    return parser


def get_client() -> BinanceFuturesClient:
    """Load credentials and return an authenticated client."""
    load_dotenv()

    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print("\nError: API credentials not found.")
        print("Set BINANCE_API_KEY and BINANCE_API_SECRET in a .env file or as env vars.")
        print("See README.md for setup instructions.\n")
        sys.exit(1)

    return BinanceFuturesClient(api_key, api_secret)


def handle_order(args, logger):
    """Handle the 'order' subcommand."""
    # Validate all inputs before touching the API
    try:
        params = validate_order_params(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValueError as e:
        logger.error("Validation error: %s", e)
        print(f"\n  Validation Error: {e}\n")
        sys.exit(1)

    # Create client and execute
    client = get_client()

    try:
        execute_order(client, params)
    except (BinanceClientError, BinanceNetworkError) as e:
        logger.error("Order execution failed: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during order execution")
        print(f"\n  Unexpected Error: {e}\n")
        sys.exit(1)


def handle_price(args, logger):
    """Handle the 'price' subcommand."""
    client = get_client()
    try:
        ticker = client.get_ticker_price(args.symbol.upper())
        price = ticker.get("price", "N/A")
        print(f"\n  {args.symbol.upper()} current price: {price}\n")
        logger.info("Price for %s: %s", args.symbol.upper(), price)
    except (BinanceClientError, BinanceNetworkError) as e:
        logger.error("Failed to fetch price: %s", e)
        print(f"\n  Error: {e}\n")
        sys.exit(1)


def handle_account(logger):
    """Handle the 'account' subcommand."""
    client = get_client()
    try:
        info = client.get_account_info()
        balances = info.get("assets", [])
        print("\n  Testnet Account Balances (non-zero):")
        print("  " + "-" * 40)
        found = False
        for asset in balances:
            wb = float(asset.get("walletBalance", 0))
            if wb > 0:
                found = True
                name = asset.get("asset", "???")
                print(f"    {name:>8s}  :  {wb:.4f}")
        if not found:
            print("    (no non-zero balances)")
        print()
        logger.info("Account info retrieved successfully")
    except (BinanceClientError, BinanceNetworkError) as e:
        logger.error("Failed to fetch account: %s", e)
        print(f"\n  Error: {e}\n")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Initialize logging
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    logger = setup_logging(log_dir)
    logger.info("CLI invoked with: %s", " ".join(sys.argv[1:]))

    if args.command == "order":
        handle_order(args, logger)
    elif args.command == "price":
        handle_price(args, logger)
    elif args.command == "account":
        handle_account(logger)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
