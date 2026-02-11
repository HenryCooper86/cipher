import pytest
from unittest.mock import patch, MagicMock
from pwd_generator.dependency_checker import (
    check_and_install_package,
    ensure_qrcode,
    ensure_pyyaml,
)


@patch("builtins.__import__")
def test_check_already_installed(mock_import):
    mock_import.return_value = MagicMock()
    success, message = check_and_install_package("testpackage", "testpackage")
    assert success
    assert "already installed" in message


@patch("builtins.__import__")
@patch("pwd_generator.dependency_checker.subprocess.run")
def test_install_package_success(mock_subprocess, mock_import):
    mock_import.side_effect = [ImportError(), MagicMock()]

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_subprocess.return_value = mock_result

    success, message = check_and_install_package("testpackage", "testpackage")
    assert mock_subprocess.called


def test_ensure_qrcode_already_available():
    try:
        import qrcode

        assert ensure_qrcode()
    except ImportError:
        pass


def test_ensure_pyyaml_already_available():
    try:
        import yaml

        assert ensure_pyyaml()
    except ImportError:
        pass


@patch("builtins.__import__")
@patch("pwd_generator.dependency_checker.subprocess.run")
def test_install_package_managed_env(mock_subprocess, mock_import):
    mock_import.side_effect = ImportError()

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "error: externally-managed-environment"
    mock_subprocess.return_value = mock_result

    success, message = check_and_install_package("testpackage")
    assert not success
    assert "externally managed" in message


def test_install_package_timeout():
    import subprocess
    from pwd_generator.dependency_checker import check_and_install_package

    with patch(
        "pwd_generator.dependency_checker.__import__",
        side_effect=ImportError,
        create=True,
    ):
        with patch(
            "pwd_generator.dependency_checker.subprocess.run",
            side_effect=subprocess.TimeoutExpired("pip", 60),
        ):
            success, message = check_and_install_package("testpackage")
            assert not success
            assert "timed out" in message.lower()
