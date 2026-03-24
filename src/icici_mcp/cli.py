"""CLI entry points for icici-mcp."""
import sys
from icici_mcp.auth import automated_login, get_cached_token, load_credentials

def login():
    """Perform automated ICICI Direct login and cache the session token."""
    creds = load_credentials()
    if not creds["totp_secret"] and not creds["session_token"]:
        print("Error: ICICI_TOTP_SECRET or ICICI_SESSION_TOKEN is required.", file=sys.stderr)
        sys.exit(1)
    if creds["session_token"]:
        from icici_mcp.auth import get_authenticated_breeze
        get_authenticated_breeze(creds)
        print("Login successful using manual session token. Token cached for today.")
        return
    automated_login(creds["api_key"], creds["api_secret"], creds["user_id"], creds["password"], creds["totp_secret"])
    print("Login successful. Session token cached for today.")

def status():
    """Check if a valid cached token exists."""
    cached = get_cached_token()
    if cached:
        print("Valid session token found for today.")
    else:
        print("No valid token. Run 'icici-mcp-login' or set ICICI_TOTP_SECRET/ICICI_SESSION_TOKEN.")
        sys.exit(1)
