# CLAUDE.md - Project Context for icici-mcp

## Project Overview

icici-mcp is an MCP (Model Context Protocol) server for ICICI Direct Breeze Connect that enables trading Indian stocks through natural conversation with any MCP-compatible AI assistant.

- **Author:** Amit Ranjan (aranjan)
- **Repository:** https://github.com/aranjan/icici-mcp
- **PyPI:** https://pypi.org/project/icici-mcp/
- **Smithery:** https://smithery.ai/server/@aranjan/icici-mcp
- **License:** MIT

## Architecture

```
User (natural language) -> AI Assistant -> icici-mcp (MCP/stdio) -> ICICI Direct Breeze API
```

- Built with **FastMCP** (from the `mcp` Python package)
- Runs as a **stdio** server (local, not hosted)
- Auto-authenticates using TOTP via `pyotp`
- Token cached at `~/.icici_direct_token.json` (expires daily)
- Uses **breeze-connect** SDK for ICICI Direct API communication
- Login flow involves RSA-encrypted password submission + TOTP, then Breeze session generation

## Project Structure

```
~/icici-mcp/
  src/icici_mcp/
    __init__.py       # Version string
    auth.py           # Shared auth: load_credentials, automated_login, get_authenticated_breeze
    server.py         # FastMCP server with 14 @mcp.tool() decorated tools
    cli.py            # CLI entry points: login(), status()
  tests/
    __init__.py
    test_auth.py      # 8 tests for auth module
    test_server.py    # 3 tests for tool registration
    test_cli.py       # 2 tests for CLI
  pyproject.toml      # Hatchling build, entry points: icici-mcp, icici-mcp-login
  smithery.yaml       # Smithery directory config
  CHANGELOG.md
  CONTRIBUTING.md
  SECURITY.md
  LICENSE             # MIT
  README.md
  .github/
    workflows/ci.yml  # CI: ruff lint, syntax, imports, tests across Python 3.10-3.13
    ISSUE_TEMPLATE/   # Bug report + feature request templates
    pull_request_template.md
```

## Key Files

- **src/icici_mcp/auth.py** -- all authentication logic lives here. Functions are parameterized (no module-level globals). `get_authenticated_breeze()` tries cached token first, then manual session token, then auto-login if TOTP available. Login flow uses RSA encryption for password + TOTP code submission.
- **src/icici_mcp/server.py** -- all 14 tools. `_breeze()` helper validates token with `breeze.get_customer_details()` and auto-retries on auth failure. Tools use `Annotated` type hints for parameter descriptions and `ToolAnnotations` for read-only/write/destructive hints.
- **src/icici_mcp/cli.py** -- `login()` and `status()` for standalone CLI use.

## 14 MCP Tools

| Tool | Annotation | Description |
|------|-----------|-------------|
| icici_login | WRITE | Auto-authenticate with TOTP |
| get_holdings | READ_ONLY | Portfolio holdings with P&L |
| get_demat_holdings | READ_ONLY | All demat holdings |
| get_positions | READ_ONLY | Current open positions |
| get_orders | READ_ONLY | Order history |
| get_margins | READ_ONLY | Available margins |
| get_funds | READ_ONLY | Available funds |
| get_quote | READ_ONLY | Live quotes (equity and F&O) |
| get_historical_data | READ_ONLY | Historical OHLCV candles |
| get_option_chain | READ_ONLY | Option chain quotes |
| place_order | WRITE | Place buy/sell orders |
| modify_order | WRITE | Modify pending orders |
| cancel_order | DESTRUCTIVE | Cancel pending orders |
| square_off | WRITE | Square off positions |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| ICICI_API_KEY | Yes | ICICI Direct API key |
| ICICI_API_SECRET | Yes | ICICI Direct API secret |
| ICICI_USER_ID | Yes | ICICI Direct client ID |
| ICICI_PASSWORD | Yes | ICICI Direct login password |
| ICICI_TOTP_SECRET | No | Base32 TOTP seed for auto-login |
| ICICI_SESSION_TOKEN | No | Manual session token override |

## Local Setup

- **Project:** ~/icici-mcp/
- **Venv:** ~/icici-mcp/venv/ (Python 3.14)
- **Installed editable:** `pip install -e .`
- **Entry points:** ~/icici-mcp/venv/bin/icici-mcp, ~/icici-mcp/venv/bin/icici-mcp-login

## Build and Publish

```bash
# Build
cd ~/icici-mcp && rm -rf dist/ && ./venv/bin/python -m build

# Publish to PyPI
./venv/bin/twine upload dist/* -u __token__ -p <PYPI_API_TOKEN>

# Remember to:
# 1. Bump version in pyproject.toml and src/icici_mcp/__init__.py
# 2. Update CHANGELOG.md
# 3. git commit and push
# 4. Create GitHub release: gh release create vX.Y.Z
```

## Testing

```bash
cd ~/icici-mcp && ./venv/bin/pytest tests/ -v
```

13 tests covering auth, server tool registration, and CLI.

## Known Limitations

- **ICICI Direct API rate limits:** 100 requests per minute, 5000 requests per day. High-frequency strategies are not supported.
- **Exchange support:** Currently supports NSE and NFO only. BSE support is possible but not tested.
- **Breeze API string params quirk:** Many Breeze API parameters that logically should be integers (like quantity, price, strike_price) must be passed as strings. The tools handle this conversion internally.
- **Session tokens expire daily.** With ICICI_TOTP_SECRET set, the server auto-refreshes. Without it, run `icici-mcp-login` manually each morning or set ICICI_SESSION_TOKEN.
- **Automated login flow** depends on ICICI Direct's web login page structure. If ICICI changes their login page HTML, the automated login may break and require updates to `auth.py`.

## Roadmap

- Basket orders
- Mutual fund tools
- IPO application tools
- Portfolio analytics
- Multi-account support
