"""
Binance Futures Testnet API client.

Handles authentication (HMAC-SHA256 signing), request construction,
and low-level communication with the Binance Futures Testnet REST API.
"""

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot")

# Binance Futures Testnet base URL
BASE_URL = "https://testnet.binancefuture.com"

# API endpoints
ENDPOINTS = {
    "order": "/fapi/v1/order",
    "account": "/fapi/v2/account",
    "ticker_price": "/fapi/v1/ticker/price",
    "exchange_info": "/fapi/v1/exchangeInfo",
    "server_time": "/fapi/v1/time",
}


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, status_code: int, code: int, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message} (HTTP {status_code})")


class BinanceNetworkError(Exception):
    """Raised on network-level failures (timeout, DNS, connection refused)."""
    pass


class BinanceFuturesClient:
    """
    Lightweight client for the Binance Futures Testnet (USDT-M) REST API.

    Handles request signing, timestamping, and error interpretation.
    """

    def __init__(self, api_key: str, api_secret: str, timeout: int = 10):
        """
        Initialize the client.

        Args:
            api_key: Binance Futures Testnet API key.
            api_secret: Binance Futures Testnet API secret.
            timeout: HTTP request timeout in seconds.
        """
        if not api_key or not api_secret:
            raise ValueError("API key and secret must be provided.")

        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        self.base_url = BASE_URL

        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })

        logger.info("BinanceFuturesClient initialized (testnet).")

    def _generate_signature(self, query_string: str) -> str:
        """
        Generate HMAC-SHA256 signature for a query string.

        Args:
            query_string: The URL-encoded parameter string to sign.

        Returns:
            Hex-encoded signature.
        """
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _get_server_time(self) -> int:
        """Fetch server timestamp to avoid clock drift issues."""
        try:
            resp = self.session.get(
                f"{self.base_url}{ENDPOINTS['server_time']}",
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()["serverTime"]
        except Exception:
            # Fallback to local time if server time fetch fails
            return int(time.time() * 1000)

    def _signed_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send an authenticated (signed) request to the Binance API.

        Args:
            method: HTTP method ('GET', 'POST', 'DELETE').
            endpoint: API endpoint path.
            params: Query/body parameters (without timestamp/signature).

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            BinanceClientError: On API-level errors (4xx/5xx with error body).
            BinanceNetworkError: On connection/timeout failures.
        """
        if params is None:
            params = {}

        # Add timestamp
        params["timestamp"] = self._get_server_time()
        params["recvWindow"] = 5000

        query_string = urlencode(params)
        signature = self._generate_signature(query_string)
        query_string += f"&signature={signature}"

        url = f"{self.base_url}{endpoint}?{query_string}"

        logger.debug("API %s → %s%s", method, self.base_url, endpoint)
        logger.debug("Params: %s", params)

        try:
            response = self.session.request(method, url, timeout=self.timeout)
        except requests.exceptions.Timeout:
            logger.error("Request timed out: %s %s", method, endpoint)
            raise BinanceNetworkError(f"Request timed out after {self.timeout}s.")
        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error: %s", e)
            raise BinanceNetworkError(f"Connection failed: {e}")
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", e)
            raise BinanceNetworkError(f"Request error: {e}")

        # Log raw response
        logger.debug("Response [%d]: %s", response.status_code, response.text[:500])

        # Parse response
        try:
            data = response.json()
        except ValueError:
            logger.error("Non-JSON response: %s", response.text[:200])
            raise BinanceClientError(response.status_code, -1, "Invalid JSON response")

        # Check for API errors
        if response.status_code >= 400 or "code" in data and data.get("code", 0) < 0:
            code = data.get("code", response.status_code)
            msg = data.get("msg", "Unknown error")
            logger.error("API error: code=%s msg='%s'", code, msg)
            raise BinanceClientError(response.status_code, code, msg)

        return data

    def _public_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Send an unauthenticated GET request.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Public request failed: %s", e)
            raise BinanceNetworkError(f"Public request failed: {e}")

    # ---- Public Endpoints ----

    def get_ticker_price(self, symbol: str) -> Dict[str, Any]:
        """Get the latest price for a symbol."""
        logger.debug("Fetching ticker price for %s", symbol)
        return self._public_request(ENDPOINTS["ticker_price"], {"symbol": symbol})

    def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange trading rules and symbol information."""
        return self._public_request(ENDPOINTS["exchange_info"])

    # ---- Account Endpoints (signed) ----

    def get_account_info(self) -> Dict[str, Any]:
        """Get current account information including balances."""
        logger.debug("Fetching account info")
        return self._signed_request("GET", ENDPOINTS["account"])

    # ---- Order Endpoints (signed) ----

    def place_order(self, **kwargs) -> Dict[str, Any]:
        """
        Place a new order on Binance Futures Testnet.

        Args:
            **kwargs: Order parameters (symbol, side, type, quantity, etc.)

        Returns:
            Order response dictionary from the API.
        """
        logger.info("Placing order: %s", kwargs)
        return self._signed_request("POST", ENDPOINTS["order"], kwargs)

    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Query an existing order."""
        return self._signed_request("GET", ENDPOINTS["order"], {
            "symbol": symbol,
            "orderId": order_id,
        })

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an active order."""
        logger.info("Cancelling order %s on %s", order_id, symbol)
        return self._signed_request("DELETE", ENDPOINTS["order"], {
            "symbol": symbol,
            "orderId": order_id,
        })
