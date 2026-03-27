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

## Broader System Context

icici-mcp is part of a multi-broker trading system:

```
Claude Desktop
  ├── kite-mcp          → Zerodha portfolio + orders (auto TOTP)
  ├── zerodha-official   → Free quotes for any NSE stock (browser OAuth)
  ├── icici-mcp         → ICICI Direct portfolio + orders (Playwright TOTP)
  ├── finance MCP       → Technical analysis (RSI, MACD, Bollinger, MA)
  └── Slack MCP         → Post to #kite-portfolio
```

**Related projects:**
- `~/kite-mcp/` — Zerodha Kite MCP server (separate repo)
- `~/finance-mcp-wrapper.py` — Async wrapper for finance-mcp-server
- `~/trading-agent-prompt.md` — Scheduled task prompts for daily/EOD/weekly reports
- `~/test_claude_config.py` — Validates Claude Desktop config
- `~/improvements-26-march.md` — Planned improvements backlog

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
  logo.svg
  run.sh              # Wrapper script for Claude Desktop (sets cwd for breeze_connect logs)
  .github/
    workflows/ci.yml  # CI: ruff lint, syntax, imports, tests across Python 3.10-3.13
    ISSUE_TEMPLATE/   # Bug report + feature request templates
    pull_request_template.md
```

## Key Files

- **src/icici_mcp/auth.py** -- all authentication logic. `get_authenticated_breeze()` tries cached token -> manual session token -> auto-login via Playwright. `automated_login()` launches headless Chromium, fills credentials, submits TOTP, intercepts the redirect to capture the apisession token. Uses `concurrent.futures.ThreadPoolExecutor` to handle asyncio.run() when called from an existing event loop (co-work compatibility fix).
- **src/icici_mcp/server.py** -- all 14 tools. `_breeze()` helper returns authenticated instance. Tools use `Annotated` type hints for parameter descriptions and `ToolAnnotations` for read-only/write/destructive hints.
- **src/icici_mcp/cli.py** -- `login()` opens browser, prompts for apisession token, caches it. `status()` checks cached token.
- **run.sh** -- wrapper script that `cd`s to project directory before launching the server. Required because breeze_connect SDK creates `logs/` directory in cwd on import, which fails in Claude Desktop's read-only launch directory.

## 14 MCP Tools

| Tool | Annotation | Description |
|------|-----------|-------------|
| icici_login | WRITE | Auto-authenticate with TOTP via Playwright |
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

## ICICI Stock Code Mapping

ICICI Direct uses different stock codes than NSE. Key mappings:

| ICICI Code | NSE Code | Company |
|------------|----------|---------|
| TATMOT | TATAMOTORS | Tata Motors |
| HDFBAN | HDFCBANK | HDFC Bank |
| STABAN | SBIN | State Bank of India |
| TATCOV | TATACONSUM | Tata Consumer |
| POWFIN | PFC | Power Finance Corp |
| ONE97 | PAYTM | Paytm |
| TATCAP | TATACAPITAL | Tata Capital |

For finance MCP technical analysis, append `.NS` to NSE codes (e.g., `RELIANCE.NS`).

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| ICICI_API_KEY | Yes | Breeze API key (contains special chars @, ~) |
| ICICI_API_SECRET | Yes | Breeze API secret |
| ICICI_USER_ID | Yes | ICICI Direct client ID (e.g., AMITRV8P) |
| ICICI_PASSWORD | Yes | ICICI Direct login password |
| ICICI_TOTP_SECRET | No | Base32 TOTP seed for auto-login via Playwright |
| ICICI_SESSION_TOKEN | No | Manual session token override (bypass Playwright) |

## Local Setup

- **Project:** ~/icici-mcp/
- **Venv:** ~/icici-mcp/venv/ (Python 3.14)
- **Installed editable:** `pip install -e .` then `playwright install chromium`
- **Entry points:** ~/icici-mcp/venv/bin/icici-mcp, ~/icici-mcp/venv/bin/icici-mcp-login
- **Claude Desktop config:** Uses `run.sh` wrapper (not direct binary)
- **Claude Desktop command:** `/Users/arn/icici-mcp/run.sh`
- **Log file:** ~/.icici-mcp.log
- **Audit log:** ~/.trading-audit.log

## Credentials Storage

- ICICI credentials: environment variables in ~/.bashrc and Claude Desktop config
- Session token: ~/.icici_direct_token.json (auto-refreshed daily via Playwright)
- PyPI recovery codes: ~/.config/pypi/recovery_codes.txt (chmod 600)

## Pre-push Checklist

Always run before pushing:
```bash
cd ~/icici-mcp
./venv/bin/ruff check src/          # Lint
./venv/bin/pytest tests/ -v         # Tests
python3 ~/test_claude_config.py     # Config validation (if config changed)
```

## Build and Publish

```bash
# Build
cd ~/icici-mcp && rm -rf dist/ && ./venv/bin/python -m build

# Publish to PyPI
./venv/bin/twine upload dist/* -u __token__ -p <PYPI_API_TOKEN>

# Remember to:
# 1. Bump version in pyproject.toml and src/icici_mcp/__init__.py
# 2. Update CHANGELOG.md
# 3. Run ruff + pytest before committing
# 4. git commit and push
# 5. Create GitHub release: gh release create vX.Y.Z
```

## Testing

```bash
cd ~/icici-mcp && ./venv/bin/pytest tests/ -v
```

23 tests covering auth, server tool registration, order validation, and CLI.

## Known Limitations

- **ICICI Direct API rate limits:** 100 requests per minute, 5000 requests per day. High-frequency strategies are not supported.
- **Exchange support:** Currently supports NSE and NFO only. BSE/MCX parameters accepted but no data available.
- **Breeze API string params quirk:** Many parameters (quantity, price, strike_price) must be passed as strings. Tools handle this conversion internally.
- **Session tokens expire daily.** With ICICI_TOTP_SECRET set, the server auto-refreshes via Playwright. Without it, run `icici-mcp-login` or set ICICI_SESSION_TOKEN.
- **Automated login via Playwright** depends on ICICI Direct's web login page structure. If ICICI changes their login page HTML/JS, the automated login may break.
- **breeze_connect logs quirk:** The SDK creates a `logs/` directory in cwd on import. Claude Desktop launches in read-only directory — `run.sh` wrapper fixes this.
- **Playwright dependency:** Adds ~90MB Chromium download on first setup. Required for automated login only.
- **asyncio.run() in event loop:** Co-work runs in an async context. The auth module uses ThreadPoolExecutor as a workaround. May still fail intermittently.
- **Static IP requirement from April 1, 2026:** SEBI mandates static IP for API trading. Current dynamic IP may stop working.
- **Logging to ~/.icici-mcp.log** (rotating, 5MB, 3 backups)
- **Trade audit log at ~/.trading-audit.log** (JSON lines, chmod 600)
- **Rate limit retry with exponential backoff on _breeze()**

## Known Issues with Scheduled Tasks

- **asyncio.run() conflict** -- co-work environment has a running event loop. Fixed with ThreadPoolExecutor workaround but may still fail intermittently.
- **Slack channel search intermittent** -- hardcode channel name "kite-portfolio" in prompts.
- **ICICI login may timeout** -- Playwright browser launch takes 5-10 seconds. If co-work has a short timeout, login may fail.

## Distribution Status

| Platform | Status |
|----------|--------|
| PyPI | Live (v0.1.3) |
| GitHub | Public, github.com/aranjan/icici-mcp |
| awesome-mcp-servers | PR #3899 |
| Official MCP servers | PR #3706 |
| Glama | Ready to submit |
| Smithery | Ready to submit |

## Scheduled Tasks (Co-work)

Three scheduled tasks use this MCP along with kite-mcp and finance MCP:
1. **Daily trading agent** -- Weekdays 9:20 AM IST -- full portfolio report
2. **EOD trading review** -- Weekdays 3:35 PM IST -- market close review
3. **Weekly portfolio digest** -- Fridays 4:00 PM IST -- week in review

Prompts saved at: `~/trading-agent-prompt.md`

## Roadmap

- Basket orders
- Mutual fund tools
- IPO application tools
- Portfolio analytics / diversification tool
- Multi-account support
- Replace ThreadPoolExecutor with nest_asyncio for cleaner async handling
