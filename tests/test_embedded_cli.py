"""Embedded CLI runner (GUI terminal)."""

from unittest.mock import MagicMock

from pwd_generator.cli.embedded_cli import _EMBEDDED_NO_INTERACTIVE_MSG, run_cli_line_embedded


def test_embedded_interactive_rejected():
    gen = MagicMock()
    code, out = run_cli_line_embedded("interactive", gen)
    assert code == 1
    assert "real terminal" in out.lower()
    assert _EMBEDDED_NO_INTERACTIVE_MSG in out


def test_embedded_menu_alias_rejected():
    gen = MagicMock()
    code, out = run_cli_line_embedded("menu", gen)
    assert code == 1
    assert "horizon-cipher" in out
