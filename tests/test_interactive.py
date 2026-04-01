from unittest.mock import MagicMock, patch

import pytest
from pwd_generator.interactive import main_interactive, safe_getpass, safe_input


def test_safe_input_interrupt(monkeypatch):
    monkeypatch.setattr("builtins.input", MagicMock(side_effect=KeyboardInterrupt))
    with pytest.raises(SystemExit) as cm:
        safe_input("prompt")
    assert cm.value.code == 0


def test_safe_getpass_interrupt(monkeypatch):
    monkeypatch.setattr("getpass.getpass", MagicMock(side_effect=KeyboardInterrupt))
    with pytest.raises(SystemExit) as cm:
        safe_getpass("prompt")
    assert cm.value.code == 0


def test_get_input_escape_char(monkeypatch):
    from pwd_generator.interactive import get_input

    # Test physical Escape key (ASCII 27)
    monkeypatch.setattr(
        "pwd_generator.interactive.safe_input", MagicMock(return_value="\x1b")
    )
    assert get_input("prompt") == "back"

    # Test "esc" string
    monkeypatch.setattr(
        "pwd_generator.interactive.safe_input", MagicMock(return_value="ESC")
    )
    assert get_input("prompt") == "back"

    # Test normal input
    monkeypatch.setattr(
        "pwd_generator.interactive.safe_input", MagicMock(return_value="valid")
    )
    assert get_input("prompt") == "valid"


@patch("pwd_generator.interactive.load_config")
@patch("pwd_generator.interactive.safe_getpass")
@patch("pwd_generator.interactive.safe_input")
def test_main_interactive_exit(mock_input, mock_getpass, mock_load_config):
    mock_load_config.return_value = {}
    mock_getpass.return_value = bytearray(b"")
    mock_input.return_value = "21"

    with pytest.raises(SystemExit) as cm:
        main_interactive()
    assert cm.value.code == 0


@patch("pwd_generator.interactive.Path.exists")
@patch("pwd_generator.interactive.SecurePasswordGenerator")
@patch("pwd_generator.interactive.safe_getpass")
@patch("pwd_generator.interactive.safe_input")
def test_main_interactive_fresh_history_recovery(
    mock_input, mock_getpass, mock_gen, mock_path_exists, temp_dir, monkeypatch
):
    from pwd_generator.exceptions import EncryptionError

    mock_path_exists.return_value = True
    mock_getpass.side_effect = [bytearray(b"wrong"), bytearray(b"right")]
    mock_gen.side_effect = [EncryptionError("wrong"), MagicMock()]

    mock_input.side_effect = ["2", "21"]

    with patch("pwd_generator.interactive.shutil.copy") as mock_copy:
        with patch("pwd_generator.interactive.Path.unlink") as mock_unlink:
            try:
                main_interactive()
            except SystemExit:
                pass

            assert mock_copy.called
            assert mock_unlink.called
