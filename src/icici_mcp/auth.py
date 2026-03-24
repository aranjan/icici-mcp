"""Shared authentication module for ICICI Direct MCP server."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import pyotp
import requests
from bs4 import BeautifulSoup
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


def _rsa_encrypt(plaintext: str, exponent_hex: str, modulus_hex: str) -> str:
    """RSA-encrypt a string using the public key from the login page.

    Replicates the JavaScript cmdEncrypt() function used by ICICI Direct.
    """
    e = int(exponent_hex, 16)
    n = int(modulus_hex, 16)
    # Convert plaintext to integer (big-endian byte encoding)
    plaintext_bytes = plaintext.encode("utf-8")
    plaintext_int = int.from_bytes(plaintext_bytes, byteorder="big")
    # RSA encrypt: ciphertext = plaintext^e mod n
    cipher_int = pow(plaintext_int, e, n)
    return format(cipher_int, "x")


def automated_login(
    api_key: str,
    api_secret: str,
    user_id: str,
    password: str,
    totp_secret: str,
) -> str:
    """Full automated login: credentials -> TOTP -> session token.

    Returns the session_token and saves it to TOKEN_FILE.
    """
    session = requests.Session()
    encoded_key = quote_plus(api_key)

    # Step 1: GET the login page (auto-submit form)
    resp = session.get(
        f"https://api.icicidirect.com/apiuser/login?api_key={encoded_key}"
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    form = soup.find("form")
    form_data = {
        inp.get("name"): inp.get("value", "")
        for inp in form.find_all("input")
    }

    # Step 2: POST to tradelogin to get the actual login page
    resp2 = session.post(
        "https://api.icicidirect.com/apiuser/tradelogin",
        data=form_data,
    )
    resp2.raise_for_status()
    soup2 = BeautifulSoup(resp2.text, "html.parser")

    # Extract RSA public key for password encryption
    hidenc_el = soup2.find("input", {"id": "hidenc"})
    if not hidenc_el:
        raise RuntimeError("Could not find RSA encryption key on login page")
    hidenc = hidenc_el.get("value", "")
    rsa_e, rsa_m = hidenc.split("~", 1)

    # Encrypt password with RSA
    encrypted_password = _rsa_encrypt(password, rsa_e, rsa_m)

    # Build form data for credential submission
    login_data = {}
    form2 = soup2.find("form")
    for inp in form2.find_all("input"):
        name = inp.get("name")
        if name:
            login_data[name] = inp.get("value", "")

    # Set the fields the JavaScript would set
    login_data["hidp"] = encrypted_password
    login_data["txtuid"] = user_id
    login_data["txtPass"] = "************"  # Masked, actual value in hidp

    # Step 3: POST credentials to get OTP page
    resp3 = session.post(
        "https://api.icicidirect.com/apiuser/tradelogin/getotp",
        data=login_data,
    )
    resp3.raise_for_status()

    # Check for errors in response
    if "invalid" in resp3.text.lower() or "error" in resp3.text.lower()[:200]:
        soup3 = BeautifulSoup(resp3.text, "html.parser")
        err = soup3.find(class_="error") or soup3.find(id="errmsg")
        err_text = err.get_text().strip() if err else "Unknown login error"
        if "invalid" not in err_text.lower():
            # Not necessarily an error - might contain 'error' in other context
            pass
        else:
            raise RuntimeError(f"Login failed: {err_text}")

    # Step 4: Generate and submit TOTP
    totp_code = pyotp.TOTP(totp_secret).now()

    # Update form data with OTP
    login_data["hiotp"] = totp_code

    resp4 = session.post(
        "https://api.icicidirect.com/apiuser/tradelogin/validateuser",
        data=login_data,
    )
    resp4.raise_for_status()

    # Step 5: Extract apisession from the response/redirect
    # The validateuser endpoint should redirect with apisession in the URL
    apisession = None

    # Check if response URL contains apisession
    if "apisession" in resp4.url:
        from urllib.parse import parse_qs, urlparse
        parsed = urlparse(resp4.url)
        params = parse_qs(parsed.query)
        apisession = params.get("apisession", [None])[0]

    # Also check response text for apisession
    if not apisession:
        soup4 = BeautifulSoup(resp4.text, "html.parser")
        # Look for redirect URL or apisession in page content
        for script in soup4.find_all("script"):
            text = script.string or ""
            if "apisession" in text:
                import re
                match = re.search(r"apisession[=:]\s*['\"]?([A-Za-z0-9]+)", text)
                if match:
                    apisession = match.group(1)
                    break

        # Check meta refresh or form redirects
        for meta in soup4.find_all("meta", {"http-equiv": "refresh"}):
            content = meta.get("content", "")
            if "apisession" in content:
                import re
                match = re.search(r"apisession=([A-Za-z0-9]+)", content)
                if match:
                    apisession = match.group(1)
                    break

        # Check hidden inputs
        for inp in soup4.find_all("input"):
            if "apisession" in (inp.get("name", "") + inp.get("id", "")).lower():
                apisession = inp.get("value", "")
                break

    if not apisession:
        raise RuntimeError(
            "Could not extract apisession after login. "
            "Try setting ICICI_SESSION_TOKEN manually by logging in at "
            f"https://api.icicidirect.com/apiuser/login?api_key={encoded_key}"
        )

    # Step 6: Generate session with Breeze SDK
    breeze = BreezeConnect(api_key=api_key)
    breeze.generate_session(api_secret=api_secret, session_token=apisession)

    # Cache the session token
    TOKEN_FILE.write_text(
        json.dumps(
            {
                "session_token": apisession,
                "date": datetime.now().strftime("%Y-%m-%d"),
            }
        )
    )

    return apisession


def get_authenticated_breeze(creds: dict) -> BreezeConnect:
    """Return an authenticated BreezeConnect instance.

    Tries cached token first, then manual session_token env var, then auto-login.
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
        # Cache it for the rest of the day
        TOKEN_FILE.write_text(
            json.dumps(
                {
                    "session_token": creds["session_token"],
                    "date": datetime.now().strftime("%Y-%m-%d"),
                }
            )
        )
        return breeze

    # Try auto-login with TOTP
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

    raise RuntimeError(
        "No valid cached token, ICICI_SESSION_TOKEN not set, and ICICI_TOTP_SECRET not set. "
        "Either set ICICI_TOTP_SECRET for auto-login, set ICICI_SESSION_TOKEN manually, "
        "or run 'icici-mcp-login' first."
    )
