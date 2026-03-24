<p align="center">
  <img src="https://raw.githubusercontent.com/aranjan/icici-mcp/main/logo.svg" alt="icici-mcp logo" width="128" height="128">
</p>

<h1 align="center">icici-mcp</h1>

<p align="center">
  <a href="https://pypi.org/project/icici-mcp/"><img src="https://badge.fury.io/py/icici-mcp.svg" alt="PyPI version"></a>
  <a href="https://github.com/aranjan/icici-mcp/actions/workflows/ci.yml"><img src="https://github.com/aranjan/icici-mcp/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://smithery.ai/servers/aranjan/icici-mcp"><img src="https://smithery.ai/badge/aranjan/icici-mcp" alt="Smithery"></a>
</p>

MCP server for [ICICI Direct](https://www.icicidirect.com/) -- trade Indian stocks through natural conversation with any [MCP-compatible](https://modelcontextprotocol.io/) AI assistant.

## Why an MCP server instead of a Python library?

Traditional Breeze Connect wrappers require you to write Python code to trade. With icici-mcp, you just talk:

```
You:       "Buy 50 Reliance at market price"
Assistant: checks quote, verifies funds, asks for confirmation, places order

You:       "How's my portfolio doing?"
Assistant: fetches holdings, calculates P&L, summarizes gainers and losers

You:       "Show me the NIFTY option chain for next expiry"
Assistant: fetches option chain data with strikes, premiums, and OI
```

No code. No scripts. No terminal. Just conversation.

icici-mcp connects any MCP-compatible AI assistant directly to your ICICI Direct account with 14 trading tools, automated TOTP login, and auto-retry on expired tokens.

## How it works

```
You (natural language) --> AI Assistant --> icici-mcp (MCP server) --> ICICI Direct Breeze API
```

Your AI assistant interprets your intent, maps stock names to symbols (e.g., "Infosys" to INFY), checks your funds, and executes trades -- all through the MCP protocol. The server handles authentication automatically, including daily token refresh via TOTP.

## Features

14 tools for complete trading control:

| Tool | Description |
|------|-------------|
| `icici_login` | Auto-authenticate with TOTP |
| `get_holdings` | Portfolio holdings with P&L |
| `get_demat_holdings` | All shares in your demat account |
| `get_positions` | Today's open positions |
| `get_orders` | Order history for a date range |
| `get_margins` | Available margins for trading |
| `get_funds` | Available funds in your account |
| `get_quote` | Live market quotes (equity and F&O) |
| `get_historical_data` | Historical OHLCV candle data |
| `get_option_chain` | Option chain quotes with strikes and premiums |
| `place_order` | Place buy/sell orders (market, limit, stop-loss) |
| `modify_order` | Modify pending orders |
| `cancel_order` | Cancel pending orders |
| `square_off` | Square off open positions |

**Key capabilities:**
- Fully automated login -- TOTP generated on the fly, no manual intervention
- Auto-retry on stale tokens -- re-authenticates transparently if a token expires mid-session
- Option chain data for F&O analysis
- Supports equity (cash), futures, options, margin, and BTST orders

## Compatible with

Works with any MCP-compatible client, including:

| Client | Platform |
|--------|----------|
| [Claude Desktop](https://claude.ai/download) | macOS, Windows |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Terminal (macOS, Linux, Windows) |
| [Cursor](https://cursor.sh/) | macOS, Windows, Linux |
| [Windsurf](https://codeium.com/windsurf) | macOS, Windows, Linux |
| [Continue](https://continue.dev/) | VS Code, JetBrains |
| Any MCP-compatible client | See [MCP clients list](https://modelcontextprotocol.io/clients) |

## Quick Start

### 1. Install

```bash
pip install icici-mcp
playwright install chromium
```

> **Note:** The `playwright install chromium` step is required once for automated TOTP login. It downloads a headless Chromium browser (~90MB) used to log in to ICICI Direct automatically.

### 2. Get your credentials

You need an [ICICI Direct API](https://api.icicidirect.com/) app. From your app dashboard, note your **API Key** and **API Secret**.

You also need:
- **User ID** -- your ICICI Direct client ID
- **Password** -- your ICICI Direct login password
- **TOTP Secret** (recommended) -- the base32 seed from setting up an external authenticator app for ICICI Direct 2FA. This enables fully automated login with no manual steps.

<details>
<summary>How to get your TOTP secret</summary>

1. Log in to **secure.icicidirect.com**
2. Go to **Profile** > **Security Settings** > **2FA / TOTP Settings**
3. Choose to set up an **external authenticator app** (Google Authenticator, Authy, etc.)
4. When the QR code appears, look for a **"Can't scan? Copy this key"** link or use a QR decoder to extract the secret
5. That key is your TOTP secret -- save it before completing setup
6. Enter the 6-digit code from your authenticator to finish

</details>

### 3. Configure your MCP client

Add this to your MCP client configuration. The config location depends on your client -- refer to your client's documentation for the exact path.

```json
{
  "mcpServers": {
    "icici": {
      "command": "icici-mcp",
      "env": {
        "ICICI_API_KEY": "your-api-key",
        "ICICI_API_SECRET": "your-api-secret",
        "ICICI_USER_ID": "your-user-id",
        "ICICI_PASSWORD": "your-password",
        "ICICI_TOTP_SECRET": "your-totp-secret",
        "ICICI_SESSION_TOKEN": ""
      }
    }
  }
}
```

Restart your MCP client. You're ready to trade.

### 4. Try it out

Open a new chat and try:

- "Show my portfolio holdings"
- "What's Reliance trading at?"
- "Buy 10 Infosys at market price"
- "How much cash do I have available?"
- "Cancel my last pending order"
- "Show me NIFTY option chain for the nearest expiry"

The AI assistant understands stock names in plain English -- no need to use trading symbols.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ICICI_API_KEY` | Yes | ICICI Direct API key |
| `ICICI_API_SECRET` | Yes | ICICI Direct API secret |
| `ICICI_USER_ID` | Yes | ICICI Direct client ID |
| `ICICI_PASSWORD` | Yes | ICICI Direct login password |
| `ICICI_TOTP_SECRET` | No | TOTP base32 seed for auto-login. Without this, you must run `icici-mcp-login` manually each day or set `ICICI_SESSION_TOKEN`. |
| `ICICI_SESSION_TOKEN` | No | Manual session token from the ICICI Direct API login page. Use this if you cannot set up TOTP auto-login. |

## Manual Login

If you don't have a TOTP secret, you can log in manually each day:

**Option 1: Use the CLI tool**

```bash
export ICICI_API_KEY=your-api-key
export ICICI_API_SECRET=your-api-secret
export ICICI_USER_ID=your-user-id
export ICICI_PASSWORD=your-password
icici-mcp-login
```

This caches the session token for the rest of the day. The MCP server will use the cached token until it expires.

**Option 2: Set ICICI_SESSION_TOKEN directly**

1. Visit `https://api.icicidirect.com/apiuser/login?api_key=YOUR_API_KEY`
2. Complete the login flow manually
3. Copy the `apisession` value from the redirect URL
4. Set it as `ICICI_SESSION_TOKEN` in your MCP client config

## Use Cases

- **Daily portfolio monitoring** -- "Give me a summary of my portfolio with top gainers and losers"
- **Quick trades** -- "Buy 50 Reliance" / "Sell all my Yes Bank"
- **F&O trading** -- "Show me BANKNIFTY option chain" / "Buy 1 lot NIFTY 25000 CE"
- **Research + action** -- "What's the 52-week high of HDFC Bank? Should I add more at current levels?"
- **Position management** -- "Square off all my margin positions"
- **Scheduled reports** -- Combine with MCP scheduled tasks to get a daily portfolio summary at 9am

## Roadmap

- [ ] Basket orders -- place multiple orders in one command
- [ ] Mutual fund tools -- buy, redeem, check SIPs
- [ ] IPO application tools
- [ ] Portfolio analytics -- sector allocation, diversification score
- [ ] Multi-account support

Have an idea? [Open a feature request](https://github.com/aranjan/icici-mcp/issues/new?template=feature_request.md).

## Development

```bash
git clone https://github.com/aranjan/icici-mcp.git
cd icici-mcp
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Security

- Credentials are passed via environment variables -- never stored in code
- Session tokens are cached locally at `~/.icici_direct_token.json` and expire daily
- The server runs locally on your machine -- no data is sent to third-party servers
- All communication with ICICI Direct uses HTTPS

## License

MIT
