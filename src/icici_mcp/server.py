"""ICICI Direct MCP Server — exposes Breeze Connect as tools for AI assistants."""

import json
from datetime import datetime, timedelta
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from icici_mcp.auth import automated_login, get_authenticated_breeze, get_login_url, load_credentials

mcp = FastMCP("icici")

# Annotation presets
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=False)


def _breeze():
    """Return an authenticated BreezeConnect instance."""
    creds = load_credentials()
    return get_authenticated_breeze(creds)


def _iso_date(date_str: str) -> str:
    """Convert YYYY-MM-DD to ISO8601 format used by Breeze API."""
    if "T" in date_str:
        return date_str
    return f"{date_str}T06:00:00.000Z"


def _today_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT06:00:00.000Z")


def _past_iso(days: int = 30) -> str:
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT06:00:00.000Z")


@mcp.tool(annotations=WRITE)
def icici_login() -> str:
    """Authenticate with ICICI Direct. Auto-logs in with TOTP if available, or uses manual session token. Call this if other tools fail with auth errors."""
    creds = load_credentials()
    try:
        get_authenticated_breeze(creds)
        return "Login successful. Session token cached for today."
    except RuntimeError as e:
        return f"Login failed: {e}"


@mcp.tool(annotations=READ_ONLY)
def get_holdings(
    exchange_code: Annotated[str, "Exchange: NSE or NFO. Default: NSE"] = "NSE",
) -> str:
    """Get portfolio holdings with quantity, average price, current price, and P&L."""
    breeze = _breeze()
    result = breeze.get_portfolio_holdings(
        exchange_code=exchange_code,
        from_date=_past_iso(365),
        to_date=_today_iso(),
        stock_code="",
        portfolio_type="",
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool(annotations=READ_ONLY)
def get_demat_holdings() -> str:
    """Get demat holdings (all shares held in your demat account)."""
    breeze = _breeze()
    result = breeze.get_demat_holdings()
    return json.dumps(result, indent=2, default=str)


@mcp.tool(annotations=READ_ONLY)
def get_positions() -> str:
    """Get current day's open positions."""
    breeze = _breeze()
    result = breeze.get_portfolio_positions()
    return json.dumps(result, indent=2, default=str)


@mcp.tool(annotations=READ_ONLY)
def get_orders(
    exchange_code: Annotated[str, "Exchange: NSE or NFO. Default: NSE"] = "NSE",
    from_date: Annotated[str, "Start date in YYYY-MM-DD format. Default: today"] = "",
    to_date: Annotated[str, "End date in YYYY-MM-DD format. Default: today"] = "",
) -> str:
    """Get order list for the specified date range."""
    breeze = _breeze()
    result = breeze.get_order_list(
        exchange_code=exchange_code,
        from_date=_iso_date(from_date) if from_date else _today_iso(),
        to_date=_iso_date(to_date) if to_date else _today_iso(),
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool(annotations=READ_ONLY)
def get_margins(
    exchange_code: Annotated[str, "Exchange: NSE or NFO. Default: NSE"] = "NSE",
) -> str:
    """Get available margins for trading."""
    breeze = _breeze()
    result = breeze.get_margin(exchange_code=exchange_code)
    return json.dumps(result, indent=2, default=str)


@mcp.tool(annotations=READ_ONLY)
def get_funds() -> str:
    """Get available funds in your trading account."""
    breeze = _breeze()
    result = breeze.get_funds()
    return json.dumps(result, indent=2, default=str)


@mcp.tool(annotations=READ_ONLY)
def get_quote(
    stock_code: Annotated[str, "Stock symbol, e.g. RELIANCE, INFY, NIFTY"],
    exchange_code: Annotated[str, "Exchange: NSE for stocks, NFO for F&O"] = "NSE",
    product_type: Annotated[str, "Product: cash, futures, or options. Default: cash"] = "cash",
    expiry_date: Annotated[str, "Expiry date DD-MMM-YYYY for F&O, e.g. 27-Mar-2026. Empty for equity."] = "",
    right: Annotated[str, "call, put, or others. Use 'others' for equity/futures."] = "others",
    strike_price: Annotated[str, "Strike price for options. Use '' for equity/futures."] = "",
) -> str:
    """Get live market quote for a stock or derivative."""
    breeze = _breeze()
    result = breeze.get_quotes(
        stock_code=stock_code,
        exchange_code=exchange_code,
        product_type=product_type,
        expiry_date=expiry_date,
        right=right,
        strike_price=strike_price,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool(annotations=READ_ONLY)
def get_historical_data(
    stock_code: Annotated[str, "Stock symbol, e.g. RELIANCE, INFY"],
    interval: Annotated[str, "Candle interval: 1minute, 5minute, 30minute, 1day"],
    from_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    to_date: Annotated[str, "End date in YYYY-MM-DD format"],
    exchange_code: Annotated[str, "Exchange: NSE for stocks, NFO for F&O"] = "NSE",
    product_type: Annotated[str, "Product: cash, futures, or options. Default: cash"] = "cash",
    expiry_date: Annotated[str, "Expiry date ISO8601 for F&O. Empty for equity."] = "",
    right: Annotated[str, "call, put, or others. Use 'others' for equity/futures."] = "others",
    strike_price: Annotated[str, "Strike price for options. Empty for equity/futures."] = "",
) -> str:
    """Get historical OHLCV candle data for a stock or derivative."""
    breeze = _breeze()
    result = breeze.get_historical_data_v2(
        interval=interval,
        from_date=_iso_date(from_date),
        to_date=_iso_date(to_date),
        stock_code=stock_code,
        exchange_code=exchange_code,
        product_type=product_type,
        expiry_date=expiry_date,
        right=right,
        strike_price=strike_price,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool(annotations=READ_ONLY)
def get_option_chain(
    stock_code: Annotated[str, "Stock symbol, e.g. NIFTY, BANKNIFTY, RELIANCE"],
    exchange_code: Annotated[str, "Exchange: NFO for options"] = "NFO",
    expiry_date: Annotated[str, "Expiry date in DD-MMM-YYYY format, e.g. 27-Mar-2026"] = "",
    product_type: Annotated[str, "Product type: options"] = "options",
) -> str:
    """Get option chain quotes for a stock or index."""
    breeze = _breeze()
    result = breeze.get_option_chain_quotes(
        stock_code=stock_code,
        exchange_code=exchange_code,
        product_type=product_type,
        expiry_date=expiry_date,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool(annotations=WRITE)
def place_order(
    stock_code: Annotated[str, "Stock symbol, e.g. RELIANCE, INFY, NIFTY"],
    exchange_code: Annotated[str, "Exchange: NSE for stocks, NFO for F&O"],
    action: Annotated[str, "buy or sell"],
    quantity: Annotated[int, "Number of shares or lots"],
    order_type: Annotated[str, "limit or market"] = "market",
    product: Annotated[str, "cash (delivery), futures, options, margin, btst"] = "cash",
    price: Annotated[str, "Price for limit orders. Use '0' for market orders."] = "0",
    validity: Annotated[str, "day or ioc"] = "day",
    stoploss: Annotated[str, "Stop-loss trigger price. Use '' for none."] = "",
    expiry_date: Annotated[str, "Expiry date ISO8601 for F&O. Empty for equity."] = "",
    right: Annotated[str, "call, put, or others. Use 'others' for equity/futures."] = "others",
    strike_price: Annotated[str, "Strike price for options. Use '0' for equity/futures."] = "0",
    disclosed_quantity: Annotated[str, "Disclosed quantity. Use '0' for full disclosure."] = "0",
) -> str:
    """Place a buy or sell order. Returns order details on success."""
    breeze = _breeze()
    result = breeze.place_order(
        stock_code=stock_code,
        exchange_code=exchange_code,
        product=product,
        action=action,
        order_type=order_type,
        quantity=str(quantity),
        price=price,
        validity=validity,
        stoploss=stoploss,
        disclosed_quantity=disclosed_quantity,
        validity_date=_today_iso(),
        expiry_date=expiry_date,
        right=right,
        strike_price=strike_price,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool(annotations=WRITE)
def modify_order(
    order_id: Annotated[str, "Order ID to modify"],
    exchange_code: Annotated[str, "Exchange: NSE or NFO"],
    quantity: Annotated[int, "New quantity"],
    price: Annotated[str, "New price"],
    order_type: Annotated[str, "limit or market"] = "limit",
    validity: Annotated[str, "day or ioc"] = "day",
    stoploss: Annotated[str, "Stop-loss trigger price. Use '0' for none."] = "0",
    disclosed_quantity: Annotated[str, "Disclosed quantity. Use '0' for full disclosure."] = "0",
) -> str:
    """Modify a pending order."""
    breeze = _breeze()
    result = breeze.modify_order(
        order_id=order_id,
        exchange_code=exchange_code,
        order_type=order_type,
        stoploss=stoploss,
        quantity=str(quantity),
        price=price,
        validity=validity,
        disclosed_quantity=disclosed_quantity,
        validity_date=_today_iso(),
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool(annotations=DESTRUCTIVE)
def cancel_order(
    exchange_code: Annotated[str, "Exchange: NSE or NFO"],
    order_id: Annotated[str, "Order ID to cancel"],
) -> str:
    """Cancel a pending order."""
    breeze = _breeze()
    result = breeze.cancel_order(
        exchange_code=exchange_code,
        order_id=order_id,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool(annotations=WRITE)
def square_off(
    exchange_code: Annotated[str, "Exchange: NSE or NFO"],
    stock_code: Annotated[str, "Stock symbol to square off"],
    quantity: Annotated[int, "Quantity to square off"],
    action: Annotated[str, "buy or sell (opposite of your open position)"],
    product: Annotated[str, "cash, futures, options, margin"] = "margin",
    price: Annotated[str, "Price. Use '0' for market."] = "0",
    expiry_date: Annotated[str, "Expiry date ISO8601 for F&O. Empty for equity."] = "",
    right: Annotated[str, "call, put, or others"] = "others",
    strike_price: Annotated[str, "Strike price for options. Use '0' for equity."] = "0",
    order_type: Annotated[str, "limit or market"] = "market",
) -> str:
    """Square off an open position."""
    breeze = _breeze()
    result = breeze.square_off(
        exchange_code=exchange_code,
        product=product,
        stock_code=stock_code,
        quantity=str(quantity),
        price=price,
        action=action,
        order_type=order_type,
        validity="day",
        stoploss="0",
        disclosed_quantity="0",
        expiry_date=expiry_date,
        right=right,
        strike_price=strike_price,
    )
    return json.dumps(result, indent=2, default=str)


def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
