# Changelog

## [0.1.0] - 2026-03-25

### Added
- Initial release
- 14 MCP tools: icici_login, get_holdings, get_demat_holdings, get_positions, get_orders, get_margins, get_funds, get_quote, get_historical_data, get_option_chain, place_order, modify_order, cancel_order, square_off
- Automated TOTP login with daily session token caching
- Manual session token override via ICICI_SESSION_TOKEN
- Auto-retry on expired tokens
- CLI entry points: icici-mcp (server) and icici-mcp-login (standalone auth)
- Support for equity (cash), futures, options, margin, and BTST orders
- Option chain data support
