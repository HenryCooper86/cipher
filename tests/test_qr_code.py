import pytest
import os
from unittest.mock import MagicMock
from pwd_generator.qr_code import (
    generate_qr_code,
    generate_qr_png_bytes,
    generate_wifi_qr,
    qr_code_to_ascii,
    display_qr_code,
)


def test_generate_qr_png_bytes():
    data = generate_qr_png_bytes("test123")
    assert data is not None
    assert data.startswith(b"\x89PNG\r\n\x1a\n")


def test_generate_qr_png_bytes_empty():
    assert generate_qr_png_bytes("") is None
    assert generate_qr_png_bytes("   ") is None


def test_generate_qr_code(temp_dir):
    qr_file = generate_qr_code("test123", output_dir=str(temp_dir))
    assert qr_file is not None
    assert os.path.exists(qr_file)
    assert qr_file.endswith(".png")


def test_generate_qr_code_custom_filename(temp_dir):
    qr_file = generate_qr_code(
        "test123", output_file="custom.png", output_dir=str(temp_dir)
    )
    assert qr_file is not None
    assert os.path.exists(qr_file)
    assert "custom.png" in qr_file


def test_generate_wifi_qr(temp_dir):
    qr_file = generate_wifi_qr(
        "TestNetwork", "password123", "WPA", output_dir=str(temp_dir)
    )
    assert qr_file is not None
    assert os.path.exists(qr_file)
    assert "wifi_" in qr_file.lower()


def test_generate_wifi_qr_hidden(temp_dir):
    qr_file = generate_wifi_qr(
        "HiddenNet", "pass", "WPA", hidden=True, output_dir=str(temp_dir)
    )
    assert qr_file is not None
    assert os.path.exists(qr_file)


def test_qr_code_to_ascii():
    ascii_qr = qr_code_to_ascii("test123")
    assert ascii_qr is not None
    assert isinstance(ascii_qr, str)
    assert "█" in ascii_qr
    assert len(ascii_qr.split("\n")) > 5


def test_qr_code_to_ascii_empty_string():
    assert qr_code_to_ascii("") is not None


def test_generate_qr_code_creates_directory(temp_dir):
    new_dir = temp_dir / "new" / "sub" / "dir"
    qr_file = generate_qr_code("test", output_dir=str(new_dir))
    assert qr_file is not None
    assert new_dir.exists()


def test_display_qr_code_nonexistent_file():
    assert not display_qr_code("/nonexistent/file.png")


def test_generate_qr_code_absolute_path(temp_dir):
    qr_file = generate_qr_code("test", output_dir=str(temp_dir))
    assert qr_file is not None
    assert os.path.isabs(qr_file)


def test_wifi_qr_string_format(temp_dir, monkeypatch):
    import qrcode

    mock_qr = MagicMock()
    monkeypatch.setattr("qrcode.QRCode", lambda **kwargs: mock_qr)

    generate_wifi_qr(
        "My SSID", "password", "WPA", hidden=True, output_dir=str(temp_dir)
    )

    expected = "WIFI:T:WPA;S:My SSID;P:password;H:true;;"
    mock_qr.add_data.assert_called_with(expected)


@pytest.mark.parametrize(
    "ssid, password, security, hidden, expected",
    [
        ("Home;Net", "pass", "WPA", False, "WIFI:T:WPA;S:Home;Net;P:pass;H:false;;"),
        ("Guest", "no:pass", "WEP", True, "WIFI:T:WEP;S:Guest;P:no:pass;H:true;;"),
        ("Open", "", "nopass", False, "WIFI:T:nopass;S:Open;P:;H:false;;"),
    ],
)
def test_wifi_qr_edge_cases(
    temp_dir, monkeypatch, ssid, password, security, hidden, expected
):
    import qrcode

    mock_qr = MagicMock()
    monkeypatch.setattr("qrcode.QRCode", lambda **kwargs: mock_qr)

    generate_wifi_qr(ssid, password, security, hidden, output_dir=str(temp_dir))
    mock_qr.add_data.assert_called_with(expected)
