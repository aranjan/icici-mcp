# Contributing to icici-mcp

Thanks for your interest in contributing! Here's how to get started.

## Development setup

```bash
git clone https://github.com/aranjan/icici-mcp.git
cd icici-mcp
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Making changes

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Test locally -- make sure `icici-mcp` starts and `icici-mcp-login` works
4. Commit with a clear message describing what changed and why
5. Open a pull request

## What to work on

- Check [open issues](https://github.com/aranjan/icici-mcp/issues) for bugs and feature requests
- New tools (e.g., basket orders, mutual funds, IPO applications)
- Better error messages and edge case handling
- Documentation improvements
- Tests

## Code style

- Keep it simple -- avoid unnecessary abstractions
- Use type hints for function parameters and return types
- Follow existing patterns in the codebase

## Adding a new tool

1. Add your tool function in `src/icici_mcp/server.py` with the `@mcp.tool()` decorator
2. Use type hints -- FastMCP generates the schema from them automatically
3. Return a JSON string
4. Use `_breeze()` to get an authenticated BreezeConnect instance
5. Update the tools table in `README.md`
6. Add the change to `CHANGELOG.md`

Example:

```python
@mcp.tool()
def get_trades(order_id: str) -> str:
    """Get trades for a specific order."""
    breeze = _breeze()
    result = breeze.get_trade_list(
        from_date=_today_iso(),
        to_date=_today_iso(),
        exchange_code="NSE",
        product_type="cash",
        action="",
        stock_code="",
    )
    return json.dumps(result, indent=2, default=str)
```

## Reporting bugs

Use the [bug report template](https://github.com/aranjan/icici-mcp/issues/new?template=bug_report.md). Include your Python version, icici-mcp version, and any error output.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
