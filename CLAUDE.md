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
- Auto-authenticates using **Playwright headless Chromium** + TOTP via `pyotp`
- ICICI Direct blocks plain HTTP login automation — Playwright is required to render the JS login page
- Token cached at `~/.icici_direct_token.json` (expires daily)
- Uses **breeze-connect** SDK for ICICI Direct API communication
- Users must run `playwright install chromium` once after pip install

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
  run.sh              # Wrapper script for Claude Desktop (sets cwd)
  logo.svg
```

## Key Files

- **src/icici_mcp/auth.py** -- all authentication logic. `get_authenticated_breeze()` tries cached token -> manual session token -> auto-login via Playwright. `automated_login()` launches headless Chromium, fills credentials, submits TOTP, and intercepts the redirect to capture the apisession token.
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
- **Installed editable:** `pip install -e .` then `playwright install chromium`
- **Entry points:** ~/icici-mcp/venv/bin/icici-mcp, ~/icici-mcp/venv/bin/icici-mcp-login
- **Claude Desktop config:** Uses `run.sh` wrapper (not direct binary) because breeze_connect SDK creates a `logs/` directory in cwd, which fails in Claude Desktop's read-only launch directory
- **Claude Desktop command:** `/Users/arn/icici-mcp/run.sh`

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
- **Automated login via Playwright** depends on ICICI Direct's web login page structure. If ICICI changes their login page HTML/JS, the automated login may break and require updates to `auth.py`.
- **breeze_connect logs quirk:** The SDK creates a `logs/` directory in the current working directory on import. Claude Desktop launches processes in a read-only directory, so `run.sh` is needed to set cwd first.
- **Playwright dependency:** Adds ~90MB Chromium download on first setup (`playwright install chromium`). Required for automated login only — manual session token flow works without it.

## Distribution Status

| Platform | Status |
|----------|--------|
| PyPI | Live (v0.1.3) |
| GitHub | Public, github.com/aranjan/icici-mcp |
| awesome-mcp-servers | PR #3899 |
| Official MCP servers | PR #3706 |
| Glama | Ready to submit |
| Smithery | Ready to submit |

## Roadmap

- Basket orders
- Mutual fund tools
- IPO application tools
- Portfolio analytics
- Multi-account support
