import sys
from unittest.mock import MagicMock, patch

import pytest
from pwd_generator.cli import create_parser, handle_generate, main_cli


def test_parser_generate_defaults():
    parser = create_parser()
    args = parser.parse_args(["generate"])
    assert args.command == "generate"
    assert args.type == "random"
    assert args.length == 16


def test_parser_generate_custom():
    parser = create_parser()
    args = parser.parse_args(
        ["generate", "--type", "passphrase", "--words", "6", "--separator", "."]
    )
    assert args.type == "passphrase"
    assert args.words == 6
    assert args.separator == "."


def test_handle_generate_random(gen, capsys):
    args = MagicMock()
    args.type = "random"
    args.length = 16
    args.profile = None
    args.quiet = True
    args.json = False
    args.no_clipboard = True
    args.save = False

    handle_generate(args, gen)
    captured = capsys.readouterr()
    assert len(captured.out.strip()) == 16


def test_handle_generate_json(gen, capsys):
    args = MagicMock()
    args.type = "random"
    args.length = 16
    args.profile = None
    args.quiet = False
    args.json = True
    args.no_clipboard = True
    args.save = False

    handle_generate(args, gen)
    captured = capsys.readouterr()
    import json

    data = json.loads(captured.out)
    assert "password" in data
    assert len(data["password"]) == 16


def test_main_cli_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["prog"])
    with pytest.raises(SystemExit) as cm:
        main_cli()
    assert cm.value.code == 0
    captured = capsys.readouterr()
    assert "Horizon Secure Password Generator" in captured.out
    assert "interactive" in captured.err


def test_parser_interactive_subcommand():
    from pwd_generator.cli.parser import create_parser

    p = create_parser()
    assert p.parse_args(["interactive"]).command == "interactive"
    assert p.parse_args(["menu"]).command == "menu"


def test_main_cli_interactive_routes_to_main_interactive(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--history-file", "custom.enc", "menu"])
    with patch("pwd_generator.interactive.main_interactive") as mock_main:
        main_cli()
        mock_main.assert_called_once_with(history_file="custom.enc")


@patch("pwd_generator.cli.get_master_password")
@patch("pwd_generator.cli.SecurePasswordGenerator")
def test_main_cli_generate_routing(mock_gen_class, mock_get_pw, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--quiet", "generate"])
    mock_get_pw.return_value = bytearray(b"password12345")
    mock_gen_instance = MagicMock()
    mock_gen_class.return_value = mock_gen_instance

    with patch("pwd_generator.cli.handle_generate") as mock_handle:
        main_cli()
        assert mock_handle.called
        assert mock_handle.call_args[0][1] == mock_gen_instance


def test_main_cli_config_no_pw(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "config", "--show"])

    with patch("pwd_generator.cli.get_master_password") as mock_get_pw:
        with patch("pwd_generator.cli.handle_config") as mock_handle:
            main_cli()
            assert not mock_get_pw.called
            assert mock_handle.called
