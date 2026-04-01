import io
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

QR_AVAILABLE = False
qrcode = None


def _ensure_qrcode():
    """Ensure qrcode library is available, install if needed."""
    global QR_AVAILABLE, qrcode

    if QR_AVAILABLE:
        return True

    try:
        import qrcode

        QR_AVAILABLE = True
        return True
    except ImportError:
        from pwd_generator.dependency_checker import ensure_qrcode

        if ensure_qrcode():
            try:
                import qrcode

                QR_AVAILABLE = True
                return True
            except ImportError:
                pass
        return False


def generate_qr_code(
    text: str,
    output_file: Optional[str] = None,
    size: int = 10,
    border: int = 4,
    output_dir: Optional[str] = None,
) -> Optional[str]:
    """
    Generate QR code for text.

    Args:
        text: Text to encode
        output_file: Output file path (optional, if None, auto-generates)
        size: QR code size (box_size parameter)
        border: Border size
        output_dir: Directory to save QR code (optional)

    Returns:
        Absolute path to generated QR code file, or None if failed
    """
    if not _ensure_qrcode():
        logger.error("QR code generation not available")
        return None

    try:
        import qrcode

        # Default to qr_codes/ folder if no directory specified
        if output_dir is None:
            output_dir = "qr_codes"

        # Determine output path
        if output_file:
            output_path = Path(output_file)
            if output_dir:
                output_path = Path(output_dir) / output_path.name
        else:
            import secrets
            filename = f"password_qr_{secrets.token_hex(4)}.png"
            output_path = Path(output_dir) / filename

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Save to absolute path
        abs_path = output_path.resolve()
        img.save(abs_path)

        logger.info(f"Generated QR code: {abs_path}")
        return str(abs_path)
    except OSError as e:
        logger.error(f"File system error during QR code generation: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during QR code generation: {e}")
        return None


def generate_qr_png_bytes(
    text: str,
    size: int = 10,
    border: int = 4,
) -> Optional[bytes]:
    """
    Encode text as a QR code and return PNG image bytes (no filesystem).

    Uses the same QR parameters as generate_qr_code (box_size, border, error correction).

    Args:
        text: Payload to encode (empty string returns None).
        size: box_size for QR modules.
        border: Quiet zone width in modules.

    Returns:
        PNG file contents, or None if qrcode is unavailable or generation fails.
    """
    if not text or not text.strip():
        return None
    if not _ensure_qrcode():
        logger.error("QR code generation not available")
        return None

    try:
        import qrcode

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except (OSError, TypeError, ValueError) as e:
        logger.error("Error building QR PNG bytes: %s", e)
        return None
    except Exception as e:
        logger.error("Unexpected error during QR PNG generation: %s", e)
        return None


def qr_code_to_ascii(text: str, size: int = 2) -> Optional[str]:
    """
    Generate QR code and convert to ASCII art for terminal display.

    Args:
        text: Text to encode in QR code
        size: Size multiplier (1 = small, 2 = medium, 3 = large)

    Returns:
        ASCII art string of QR code, or None if failed
    """
    if not _ensure_qrcode():
        return None

    try:
        import qrcode

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,  # Use 1 for ASCII conversion
            border=1,
        )
        qr.add_data(text)
        qr.make(fit=True)

        # Get QR code matrix
        matrix = qr.get_matrix()

        # Convert to ASCII
        # Use double-width characters for better visibility
        block_char = "██"
        space_char = "  "

        ascii_lines = []
        # Add top border
        ascii_lines.append(block_char * (len(matrix[0]) + 2))

        # Convert matrix to ASCII
        for row in matrix:
            line = block_char  # Left border
            for cell in row:
                line += block_char if cell else space_char
            line += block_char  # Right border
            ascii_lines.append(line)

        # Add bottom border
        ascii_lines.append(block_char * (len(matrix[0]) + 2))

        return "\n".join(ascii_lines)
    except (TypeError, ValueError) as e:
        logger.error(f"Formatting error during ASCII QR conversion: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during ASCII QR conversion: {e}")
        return None


def display_qr_code(qr_path: str) -> bool:
    """
    Display QR code image if possible.

    Args:
        qr_path: Path to QR code image

    Returns:
        True if displayed successfully, False otherwise
    """
    if not _ensure_qrcode():
        return False

    try:
        import os

        from PIL import Image

        if not os.path.exists(qr_path):
            logger.error(f"QR code file not found: {qr_path}")
            return False

        # Try to open and display (works on macOS/Linux with GUI)
        try:
            img = Image.open(qr_path)
            img.show()
            return True
        except Exception:
            # If display fails, at least confirm file exists
            logger.info("QR code saved but cannot display (no GUI available)")
            return False
    except ImportError:
        logger.warning("PIL not available for displaying QR code")
        return False
    except Exception as e:
        logger.error(f"Failed to display QR code: {e}")
        return False


def generate_wifi_qr(
    ssid: str,
    password: str,
    security: str = "WPA",
    hidden: bool = False,
    output_dir: Optional[str] = None,
) -> Optional[str]:
    """
    Generate QR code for WiFi password.

    Format: WIFI:T:WPA;S:SSID;P:password;H:false;;

    Args:
        ssid: WiFi network name
        password: WiFi password
        security: Security type (WPA, WEP, nopass)
        hidden: Whether network is hidden
        output_dir: Directory to save QR code (optional)

    Returns:
        Absolute path to generated QR code file, or None if failed
    """
    if not _ensure_qrcode():
        logger.error("QR code generation not available")
        return None

    filename = f"wifi_{ssid.replace(' ', '_').replace('/', '_')}.png"
    wifi_string = (
        f"WIFI:T:{security};S:{ssid};P:{password};H:{'true' if hidden else 'false'};;"
    )
    return generate_qr_code(wifi_string, filename, output_dir=output_dir)
