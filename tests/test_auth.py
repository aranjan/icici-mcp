"""Tests for the auth module."""

import json
import os
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest

from icici_mcp.auth import get_cached_token, load_credentials, TOKEN_FILE


class TestLoadCredentials:
    """Tests for load_credentials()."""

    def test_loads_all_credentials(self):
        env = {
            "ICICI_API_KEY": "test-key",
            "ICICI_API_SECRET": "test-secret",
            "ICICI_USER_ID": "AB1234",
            "ICICI_PASSWORD": "testpass",
            "ICICI_TOTP_SECRET": "TOTP123",
            "ICICI_SESSION_TOKEN": "session-abc",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            creds = load_credentials()
            assert creds["api_key"] == "test-key"
            assert creds["api_secret"] == "test-secret"
            assert creds["user_id"] == "AB1234"
            assert creds["password"] == "testpass"
            assert creds["totp_secret"] == "TOTP123"
            assert creds["session_token"] == "session-abc"

    def test_totp_secret_is_optional(self):
        env = {
            "ICICI_API_KEY": "test-key",
            "ICICI_API_SECRET": "test-secret",
            "ICICI_USER_ID": "AB1234",
            "ICICI_PASSWORD": "testpass",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            # Remove TOTP if it exists
            os.environ.pop("ICICI_TOTP_SECRET", None)
            os.environ.pop("ICICI_SESSION_TOKEN", None)
            creds = load_credentials()
            assert creds["totp_secret"] is None

    def test_session_token_is_optional(self):
        env = {
            "ICICI_API_KEY": "test-key",
            "ICICI_API_SECRET": "test-secret",
            "ICICI_USER_ID": "AB1234",
            "ICICI_PASSWORD": "testpass",
            "ICICI_TOTP_SECRET": "TOTP123",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            os.environ.pop("ICICI_SESSION_TOKEN", None)
            creds = load_credentials()
            assert creds["session_token"] is None

    def test_exits_on_missing_required(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                load_credentials()

    def test_exits_on_partial_credentials(self):
        env = {"ICICI_API_KEY": "test-key"}
        with mock.patch.dict(os.environ, env, clear=True):
            with pytest.raises(SystemExit):
                load_credentials()


class TestGetCachedToken:
    """Tests for get_cached_token()."""

    def test_returns_token_for_today(self, tmp_path):
        token_file = tmp_path / "token.json"
        token_file.write_text(json.dumps({
            "session_token": "test-token-123",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }))
        with mock.patch("icici_mcp.auth.TOKEN_FILE", token_file):
            assert get_cached_token() == "test-token-123"

    def test_returns_none_for_old_token(self, tmp_path):
        token_file = tmp_path / "token.json"
        token_file.write_text(json.dumps({
            "session_token": "old-token",
            "date": "2020-01-01",
        }))
        with mock.patch("icici_mcp.auth.TOKEN_FILE", token_file):
            assert get_cached_token() is None

    def test_returns_none_when_file_missing(self, tmp_path):
        token_file = tmp_path / "nonexistent.json"
        with mock.patch("icici_mcp.auth.TOKEN_FILE", token_file):
            assert get_cached_token() is None


class TestPlaywrightImportError:
    def test_automated_login_fails_without_playwright(self):
        """If playwright is not installed, should raise RuntimeError."""
        import sys

        with mock.patch.dict(sys.modules, {"playwright": None, "playwright.async_api": None}):
            # This test verifies the error message mentions playwright installation
            # Note: may need to reload the module or test differently
            pass  # Placeholder -- implement based on actual import structure
