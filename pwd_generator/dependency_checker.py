import subprocess
import sys
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def check_and_install_package(package_name: str, import_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    Check if a package is installed, and if not, attempt to install it.
    
    Args:
        package_name: Name of the package to install (e.g., 'qrcode[pil]')
        import_name: Name to import (e.g., 'qrcode'). If None, uses package_name
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if import_name is None:
        import_name = package_name.split('[')[0]  # Remove extras like [pil]
    
    # First, check if already installed
    try:
        __import__(import_name)
        return True, f"{import_name} is already installed"
    except ImportError:
        pass
    
    # Try to install
    try:
        logger.info(f"Attempting to install {package_name}...")
        print(f"\n[WARNING]  {import_name} not found. Attempting to install {package_name}...")
        
        # Try with --user first (for externally managed environments)
        install_commands = [
            [sys.executable, "-m", "pip", "install", "--user", package_name],
            [sys.executable, "-m", "pip", "install", package_name],
        ]
        
        # Try --break-system-packages if available (Python 3.12+)
        if sys.version_info >= (3, 12):
            install_commands.insert(1, [sys.executable, "-m", "pip", "install", "--break-system-packages", package_name])
        
        last_error = None
        last_stderr = None
        last_stdout = None
        
        for cmd in install_commands:
            try:
                logger.debug(f"Trying installation command: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=60
                )  # nosec B603
                
                last_stderr = result.stderr
                last_stdout = result.stdout
                
                if result.returncode == 0:
                    # Verify installation
                    try:
                        __import__(import_name)
                        logger.info(f"Successfully installed {package_name}")
                        print(f"[OK] Successfully installed {package_name}")
                        return True, f"Installed {package_name}"
                    except ImportError as e:
                        logger.warning(f"Installation succeeded but import failed: {e}")
                        continue  # Try next method
                else:
                    # Capture error details
                    error_output = result.stderr or result.stdout or "Unknown error"
                    last_error = error_output
                    logger.warning(f"Installation command failed with return code {result.returncode}: {error_output[:500]}")
                    
            except subprocess.TimeoutExpired:
                last_error = "Installation timed out after 60 seconds"
                logger.error("Installation timed out")
            except Exception as e:
                last_error = f"Exception during installation: {str(e)}"
                logger.exception(f"Exception during installation: {e}")
        
        # If all methods failed, provide helpful error message
        error_details = last_error or last_stderr or last_stdout or "Unknown error"
        
        if "externally-managed-environment" in error_details:
            return False, f"Environment is externally managed. Please install manually:\n   pip install --user {package_name}\n   or: pip install --break-system-packages {package_name}"
        elif error_details:
            # Show more detailed error
            error_preview = error_details[:300] if len(error_details) > 300 else error_details
            return False, f"Installation failed:\n{error_preview}\n\nYou can install manually with: pip install --user {package_name}"
        else:
            return False, f"Installation failed (unknown error). You can install manually with: pip install --user {package_name}"
        
    except Exception as e:
        error_msg = f"Unexpected error installing {package_name}: {e}"
        logger.error(error_msg)
        return False, error_msg


def ensure_qrcode() -> bool:
    """Ensure qrcode library is installed."""
    success, message = check_and_install_package("qrcode[pil]", "qrcode")
    if success:
        logger.info("QR code library available")
    else:
        logger.warning(f"QR code library not available: {message}")
        # Only print error if it's not already installed
        if "already installed" not in message:
            print(f"\n[ERROR] {message}")
            if "externally-managed" not in message.lower():
                print("   You can install it manually with: pip install --user qrcode[pil]")
    return success


def ensure_pyyaml() -> bool:
    """Ensure PyYAML is installed (optional for YAML config support)."""
    success, message = check_and_install_package("PyYAML", "yaml")
    if success:
        logger.info("PyYAML available")
    else:
        logger.warning(f"PyYAML not available: {message}")
    return success


def check_all_optional_dependencies() -> dict:
    """Check and optionally install all optional dependencies."""
    results = {
        'qrcode': ensure_qrcode(),
        'pyyaml': ensure_pyyaml(),
    }
    return results
