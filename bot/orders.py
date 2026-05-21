"""
Order placement logic.

Translates validated parameters into Binance API calls and formats
the results for user-facing output.
"""

import logging
from typing import Any, Dict

from .client import BinanceFuturesClient, BinanceClientError, BinanceNetworkError

logger = logging.getLogger("trading_bot")


def _format_order_summary(params: dict) -> str:
    """Build a human-readable order request summary."""
    lines = [
        "",
        "=" * 46,
        "           ORDER REQUEST SUMMARY",
        "=" * 46,
        f"  Symbol      : {params['symbol']}",
        f"  Side        : {params['side']}",
        f"  Type        : {params['order_type']}",
        f"  Quantity    : {params['quantity']}",
    ]
    if params.get("price") is not None:
        lines.append(f"  Price       : {params['price']}")
    if params.get("stop_price") is not None:
        lines.append(f"  Stop Price  : {params['stop_price']}")
    lines.append("=" * 46)
    return "\n".join(lines)


def _format_order_response(response: dict) -> str:
    """Build a human-readable order response summary."""
    lines = [
        "",
        "=" * 46,
        "           ORDER RESPONSE DETAILS",
        "=" * 46,
        f"  Order ID    : {response.get('orderId', 'N/A')}",
        f"  Symbol      : {response.get('symbol', 'N/A')}",
        f"  Side        : {response.get('side', 'N/A')}",
        f"  Type        : {response.get('type', 'N/A')}",
        f"  Status      : {response.get('status', 'UNKNOWN')}",
        f"  Orig Qty    : {response.get('origQty', 'N/A')}",
        f"  Executed Qty: {response.get('executedQty', '0')}",
        f"  Avg Price   : {response.get('avgPrice', response.get('price', 'N/A'))}",
        "=" * 46,
    ]
    return "\n".join(lines)


def place_market_order(client, symbol, side, quantity):
    """Place a MARKET order."""
    return client.place_order(symbol=symbol, side=side, type="MARKET", quantity=quantity)


def place_limit_order(client, symbol, side, quantity, price):
    """Place a LIMIT order with GTC time-in-force."""
    return client.place_order(
        symbol=symbol, side=side, type="LIMIT",
        timeInForce="GTC", quantity=quantity, price=price,
    )


def place_stop_market_order(client, symbol, side, quantity, stop_price):
    """Place a STOP_MARKET order triggered at stop_price."""
    return client.place_order(
        symbol=symbol, side=side, type="STOP_MARKET",
        quantity=quantity, stopPrice=stop_price,
    )


def execute_order(client: BinanceFuturesClient, params: dict) -> Dict[str, Any]:
    """
    Execute an order based on validated parameters.

    Prints request summary, dispatches to correct handler,
    prints response, and returns the result.
    """
    summary = _format_order_summary(params)
    logger.debug("Order request: %s", summary)
    print(summary)

    order_type = params["order_type"]

    try:
        if order_type == "MARKET":
            response = place_market_order(
                client, params["symbol"], params["side"], params["quantity"])
        elif order_type == "LIMIT":
            response = place_limit_order(
                client, params["symbol"], params["side"],
                params["quantity"], params["price"])
        elif order_type == "STOP_MARKET":
            response = place_stop_market_order(
                client, params["symbol"], params["side"],
                params["quantity"], params["stop_price"])
        else:
            raise ValueError(f"Unsupported order type: {order_type}")

    except BinanceClientError as e:
        logger.error("Order failed - API error: %s", e)
        print(f"\n  ORDER FAILED: {e}")
        raise
    except BinanceNetworkError as e:
        logger.error("Order failed - Network error: %s", e)
        print(f"\n  ORDER FAILED (network): {e}")
        raise

    resp_text = _format_order_response(response)
    logger.debug("Order response: %s", resp_text)
    print(resp_text)

    status = response.get("status", "UNKNOWN")
    order_id = response.get("orderId", "N/A")

    if status in ("FILLED", "NEW", "PARTIALLY_FILLED"):
        print(f"\n  ORDER SUCCESSFUL - ID: {order_id} | Status: {status}")
        logger.info("Order successful: ID=%s Status=%s", order_id, status)
    else:
        print(f"\n  ORDER STATUS: {status} - ID: {order_id}")
        logger.warning("Unexpected order status: %s", status)

    return response
