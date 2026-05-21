"""
Input validation utilities for order parameters.

Provides strict validation of user-supplied order parameters before
they are sent to the Binance API, producing clear error messages.
"""

import logging
from typing import Optional

logger = logging.getLogger("trading_bot")

# Supported trading pairs (common USDT-M futures)
SUPPORTED_SYMBOLS = {
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
    "SOLUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "LTCUSDT", "TRXUSDT", "UNIUSDT", "ATOMUSDT",
}

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalize a trading symbol.

    Args:
        symbol: Trading pair (e.g., 'btcusdt', 'ETHUSDT').

    Returns:
        Uppercased, validated symbol string.

    Raises:
        ValueError: If symbol is not in the supported set.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    if symbol not in SUPPORTED_SYMBOLS:
        raise ValueError(
            f"Unsupported symbol '{symbol}'. Supported: {sorted(SUPPORTED_SYMBOLS)}"
        )
    logger.debug("Symbol validated: %s", symbol)
    return symbol


def validate_side(side: str) -> str:
    """
    Validate order side.

    Args:
        side: 'BUY' or 'SELL' (case-insensitive).

    Returns:
        Uppercased, validated side string.

    Raises:
        ValueError: If side is not BUY or SELL.
    """
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Invalid side '{side}'. Must be one of: {VALID_SIDES}")
    logger.debug("Side validated: %s", side)
    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.

    Args:
        order_type: 'MARKET', 'LIMIT', or 'STOP_MARKET' (case-insensitive).

    Returns:
        Uppercased, validated order type string.

    Raises:
        ValueError: If order type is not supported.
    """
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Must be one of: {VALID_ORDER_TYPES}"
        )
    logger.debug("Order type validated: %s", order_type)
    return order_type


def validate_quantity(quantity: str) -> float:
    """
    Validate and parse order quantity.

    Args:
        quantity: Quantity as a string (e.g., '0.001').

    Returns:
        Parsed float quantity.

    Raises:
        ValueError: If quantity is not a positive number.
    """
    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be positive, got {qty}.")
    logger.debug("Quantity validated: %s", qty)
    return qty


def validate_price(price: Optional[str], order_type: str) -> Optional[float]:
    """
    Validate and parse order price.

    Price is required for LIMIT and STOP_MARKET orders, and must not
    be provided for MARKET orders.

    Args:
        price: Price as a string, or None.
        order_type: The validated order type.

    Returns:
        Parsed float price, or None for MARKET orders.

    Raises:
        ValueError: If price is missing for LIMIT/STOP_MARKET, provided
                     for MARKET, or not a positive number.
    """
    if order_type == "MARKET":
        if price is not None:
            logger.warning("Price is ignored for MARKET orders.")
        return None

    if order_type in ("LIMIT", "STOP_MARKET"):
        if price is None:
            raise ValueError(f"Price is required for {order_type} orders.")
        try:
            p = float(price)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid price '{price}'. Must be a positive number.")
        if p <= 0:
            raise ValueError(f"Price must be positive, got {p}.")
        logger.debug("Price validated: %s", p)
        return p

    return None


def validate_stop_price(stop_price: Optional[str], order_type: str) -> Optional[float]:
    """
    Validate and parse stop price (for STOP_MARKET orders).

    Args:
        stop_price: Stop price as a string, or None.
        order_type: The validated order type.

    Returns:
        Parsed float stop price, or None if not applicable.

    Raises:
        ValueError: If stop price is missing for STOP_MARKET or invalid.
    """
    if order_type != "STOP_MARKET":
        return None

    if stop_price is None:
        raise ValueError("Stop price (--stop-price) is required for STOP_MARKET orders.")

    try:
        sp = float(stop_price)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid stop price '{stop_price}'. Must be a positive number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be positive, got {sp}.")
    logger.debug("Stop price validated: %s", sp)
    return sp


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
) -> dict:
    """
    Validate all order parameters in one call.

    Args:
        symbol: Trading pair.
        side: BUY or SELL.
        order_type: MARKET, LIMIT, or STOP_MARKET.
        quantity: Order quantity.
        price: Limit price (required for LIMIT/STOP_MARKET).
        stop_price: Stop trigger price (required for STOP_MARKET).

    Returns:
        Dictionary of validated parameters ready for the API client.

    Raises:
        ValueError: On any validation failure.
    """
    validated_type = validate_order_type(order_type)
    params = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validated_type,
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, validated_type),
        "stop_price": validate_stop_price(stop_price, validated_type),
    }
    logger.info("All order parameters validated successfully.")
    return params
