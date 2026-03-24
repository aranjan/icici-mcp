"""CLI entry points for icici-mcp."""

import sys

from icici_mcp.auth import (
    get_authenticated_breeze,
    get_cached_token,
    load_credentials,
    open_login_page,
    save_session_token,
)


def login():
    """Log in to ICICI Direct and cache the session token."""
    creds = load_credentials()

    # If session token is provided via env, use it directly
    if creds["session_token"]:
        get_authenticated_breeze(creds)
        print("Login successful using session token. Cached for today.")
        return

    # Otherwise, open browser and ask for the session token
    url = open_login_page(creds["api_key"])
    print(f"Opening login page: {url}\n")
    print("After logging in, copy the 'apisession' value from the redirect URL.")
    session_token = input("Paste your apisession here: ").strip()

    if not session_token:
        print("Error: No session token provided.", file=sys.stderr)
        sys.exit(1)

    # Validate by connecting
    get_authenticated_breeze({**creds, "session_token": session_token})
    save_session_token(session_token)
    print("Login successful. Session token cached for today.")


def status():
    """Check if a valid cached token exists."""
    cached = get_cached_token()
    if cached:
        print("Valid session token found for today.")
    else:
        print(
            "No valid token. Run 'icici-mcp-login' to log in, "
            "or set ICICI_SESSION_TOKEN."
        )
        sys.exit(1)
