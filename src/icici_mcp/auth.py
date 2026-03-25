"""Shared authentication module for ICICI Direct MCP server."""

import asyncio
import json
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse

import pyotp
from breeze_connect import BreezeConnect

TOKEN_FILE = Path.home() / ".icici_direct_token.json"


def load_credentials() -> dict:
    """Load credentials from environment variables.

    Returns a dict with keys: api_key, api_secret, user_id, password, totp_secret, session_token.
    Raises SystemExit if required variables are missing.
    """
    required = {
        "ICICI_API_KEY": "api_key",
        "ICICI_API_SECRET": "api_secret",
        "ICICI_USER_ID": "user_id",
        "ICICI_PASSWORD": "password",
    }
    creds = {}
    missing = []

    for env_var, key in required.items():
        val = os.environ.get(env_var)
        if not val:
            missing.append(env_var)
        creds[key] = val or ""

    if missing:
        print(
            f"Error: Missing required environment variables: {', '.join(missing)}\n"
            "Set them in your shell or in your MCP client's env config.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    creds["totp_secret"] = os.environ.get("ICICI_TOTP_SECRET")
    creds["session_token"] = os.environ.get("ICICI_SESSION_TOKEN")
    return creds


def get_cached_token() -> str | None:
    """Return today's cached session token, or None if expired/missing."""
    if TOKEN_FILE.exists():
        data = json.loads(TOKEN_FILE.read_text())
        if data.get("date") == datetime.now().strftime("%Y-%m-%d"):
            return data["session_token"]
    return None


def get_login_url(api_key: str) -> str:
    """Return the ICICI Direct login URL for the given API key."""
    encoded_key = quote_plus(api_key)
    return f"https://api.icicidirect.com/apiuser/login?api_key={encoded_key}"


def open_login_page(api_key: str) -> str:
    """Open the ICICI Direct login page in the default browser and return the URL."""
    url = get_login_url(api_key)
    webbrowser.open(url)
    return url


def save_session_token(session_token: str) -> None:
    """Cache a session token for the rest of the day."""
    TOKEN_FILE.write_text(
        json.dumps(
            {
                "session_token": session_token,
                "date": datetime.now().strftime("%Y-%m-%d"),
            }
        )
    )


def automated_login(
    api_key: str,
    api_secret: str,
    user_id: str,
    password: str,
    totp_secret: str,
) -> str:
    """Full automated login using headless Chromium via Playwright.

    Navigates the ICICI Direct login page, fills credentials, submits TOTP,
    and intercepts the redirect to extract the apisession token.

    Returns the session_token and saves it to TOKEN_FILE.
    """

    async def _login() -> str:
        from playwright.async_api import async_playwright

        login_url = get_login_url(api_key)
        apisession = None

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Intercept requests to capture apisession from redirect URL
            def on_request(request):
                nonlocal apisession
                url = request.url
                if "apisession" in url:
                    parsed = urlparse(url)
                    params = parse_qs(parsed.query)
                    token = params.get("apisession", [None])[0]
                    if token:
                        apisession = token

            page.on("request", on_request)

            # Step 1: Navigate to login page
            await page.goto(login_url, wait_until="networkidle")

            # Step 2: Fill credentials
            await page.fill("#txtuid", user_id)
            await page.fill("#txtPass", password)
            await page.check("#chkssTnc")

            # Step 3: Click login
            await page.click("#btnSubmit")
            await page.wait_for_timeout(3000)

            # Step 4: Enter TOTP
            totp_code = pyotp.TOTP(totp_secret).now()
            otp_inputs = await page.query_selector_all("input[tg-nm=otp]")

            if len(otp_inputs) == 6:
                for i, digit in enumerate(totp_code):
                    await otp_inputs[i].fill(digit)
            elif otp_inputs:
                await otp_inputs[0].fill(totp_code)

            # Step 5: Submit OTP
            try:
                await page.evaluate("submitotp()")
            except Exception:
                pass
            await page.wait_for_timeout(5000)

            await browser.close()

        if not apisession:
            raise RuntimeError(
                "Could not extract apisession after automated login. "
                "Try running 'icici-mcp-login' to log in manually."
            )

        return apisession

    # Run the async login — handle both fresh and existing event loops
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already in an async context (e.g., MCP server) — use nest_asyncio or new thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            session_token = pool.submit(asyncio.run, _login()).result()
    else:
        session_token = asyncio.run(_login())

    # Cache the token
    save_session_token(session_token)

    return session_token


def get_authenticated_breeze(creds: dict) -> BreezeConnect:
    """Return an authenticated BreezeConnect instance.

    Auth priority:
    1. Today's cached session token
    2. ICICI_SESSION_TOKEN env var (manual override)
    3. Auto-login with TOTP via headless browser (if ICICI_TOTP_SECRET set)
    4. Error with instructions
    """
    breeze = BreezeConnect(api_key=creds["api_key"])

    # Try cached token first
    cached = get_cached_token()
    if cached:
        breeze.generate_session(
            api_secret=creds["api_secret"], session_token=cached
        )
        return breeze

    # Try manual session token override
    if creds["session_token"]:
        breeze.generate_session(
            api_secret=creds["api_secret"],
            session_token=creds["session_token"],
        )
        save_session_token(creds["session_token"])
        return breeze

    # Try auto-login with TOTP via headless browser
    if creds["totp_secret"]:
        session_token = automated_login(
            creds["api_key"],
            creds["api_secret"],
            creds["user_id"],
            creds["password"],
            creds["totp_secret"],
        )
        breeze.generate_session(
            api_secret=creds["api_secret"], session_token=session_token
        )
        return breeze

    # No valid token available
    login_url = get_login_url(creds["api_key"])
    raise RuntimeError(
        "No valid session token. To fix this, either:\n"
        "1. Set ICICI_TOTP_SECRET for fully automated login\n"
        f"2. Log in manually at: {login_url}\n"
        "   Then set ICICI_SESSION_TOKEN=<apisession from redirect URL>\n"
        "3. Run: icici-mcp-login\n"
    )
