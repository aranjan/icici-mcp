"""Tests for the CLI module."""

import os
from unittest import mock

import pytest

from icici_mcp.cli import login, status


class TestLogin:
    """Tests for the login CLI command."""

    def test_exits_without_totp_or_session(self):
        env = {
            "ICICI_API_KEY": "key",
            "ICICI_API_SECRET": "secret",
            "ICICI_USER_ID": "AB1234",
            "ICICI_PASSWORD": "pass",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with pytest.raises(SystemExit):
                login()


class TestStatus:
    """Tests for the status CLI command."""

    def test_exits_when_no_token(self, tmp_path):
        token_file = tmp_path / "nonexistent.json"
        with mock.patch("icici_mcp.auth.TOKEN_FILE", token_file):
            with pytest.raises(SystemExit):
                status()
