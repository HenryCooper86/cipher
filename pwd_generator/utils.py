import getpass
import logging
import subprocess
import sys
import threading
import time
from typing import Optional

from pwd_generator.exceptions import ClipboardError

logger = logging.getLogger(__name__)

# Clipboard auto-clear configuration
CLIPBOARD_AUTO_CLEAR_SECONDS = 30  # Clear clipboard after 30 seconds


def safe_input(prompt: str) -> str:
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
        sys.exit(0)


def safe_getpass(prompt: str) -> bytearray:
    try:
        password = getpass.getpass(prompt)
        return bytearray(password.encode("utf-8"))
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
        # Clear any partial password data from memory before exiting
        try:
            from pwd_generator.encryption import clear_memory
            # We can't clear what we never received, but we log the interrupt
            logger.warning("Keyboard interrupt during password entry - no sensitive data stored")
        except Exception:
            pass
        sys.exit(0)


def prompt_yes_no(prompt: str, default: Optional[bool] = None) -> bool:
    suffix = " (Y/n)" if default is True else " (y/N)" if default is False else " (y/n)"
    while True:
        response = safe_input(f"{prompt}{suffix}: ").strip().lower()
        if not response and default is not None:
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Invalid response. Please enter 'y' or 'n'.")


def copy_to_clipboard(text: str, raise_on_error: bool = False, auto_clear: bool = True) -> bool:
    """
    Copy text to system clipboard with optional auto-clear.

    Args:
        text: The text to copy to clipboard
        raise_on_error: If True, raises ClipboardError on failure instead of returning False
        auto_clear: If True, schedules clipboard to be cleared after CLIPBOARD_AUTO_CLEAR_SECONDS

    Returns:
        bool: True if successful, False otherwise

    Raises:
        ClipboardError: If raise_on_error is True and clipboard operation fails
    """
    last_error = None

    try:
        import pyperclip

        pyperclip.copy(text)
        logger.info("Copied to clipboard using pyperclip")
        
        # Schedule auto-clear if enabled
        if auto_clear:
            _schedule_clipboard_clear()
        
        return True
    except ImportError:
        logger.debug("pyperclip not available, trying system clipboard tools")
    except Exception as e:
        logger.debug(f"pyperclip failed: {e}")
        last_error = e

    import shutil

    try:
        if sys.platform == "darwin":
            cmd_path = shutil.which("pbcopy")
            if cmd_path:
                process = subprocess.Popen(
                    [cmd_path], stdin=subprocess.PIPE, close_fds=True
                )  # nosec B603
                process.communicate(text.encode("utf-8"), timeout=5)
                logger.info("Copied to clipboard using pbcopy")
                
                if auto_clear:
                    _schedule_clipboard_clear()
                
                return True
            else:
                last_error = "pbcopy command not found"
        elif sys.platform == "linux":
            cmd_path = shutil.which("xclip")
            if cmd_path:
                try:
                    process = subprocess.Popen(
                        [cmd_path, "-selection", "clipboard"],
                        stdin=subprocess.PIPE,
                        close_fds=True,
                    )  # nosec B603
                    process.communicate(text.encode("utf-8"), timeout=5)
                    logger.info("Copied to clipboard using xclip")
                    
                    if auto_clear:
                        _schedule_clipboard_clear()
                    
                    return True
                except FileNotFoundError as e:
                    logger.debug("xclip found but execution failed")
                    last_error = e
            else:
                last_error = "xclip command not found"
        elif sys.platform == "win32":
            cmd_path = shutil.which("clip")
            if cmd_path:
                try:
                    process = subprocess.Popen(
                        [cmd_path], stdin=subprocess.PIPE, close_fds=True
                    )  # nosec B603
                    process.communicate(text.encode("utf-8"), timeout=5)
                    logger.info("Copied to clipboard using clip")
                    
                    if auto_clear:
                        _schedule_clipboard_clear()
                    
                    return True
                except Exception as e:
                    logger.debug(f"clip execution failed: {e}")
                    last_error = e
            else:
                last_error = "clip command not found"
    except subprocess.TimeoutExpired:
        logger.warning("Clipboard operation timed out")
        last_error = "Clipboard operation timed out"
    except Exception as e:
        logger.warning(f"Clipboard copy failed: {e}")
        last_error = e

    if raise_on_error:
        raise ClipboardError(
            f"Failed to copy to clipboard: {last_error or 'No clipboard tool available'}",
            details={"platform": sys.platform, "error": str(last_error) if last_error else None}
        )

    return False


def _clear_clipboard() -> bool:
    """Clear the system clipboard by overwriting with empty string."""
    try:
        import pyperclip
        pyperclip.copy("")
        logger.info("Clipboard cleared using pyperclip")
        return True
    except Exception as e:
        logger.debug(f"pyperclip clear failed: {e}")
    
    import shutil
    try:
        if sys.platform == "darwin":
            cmd_path = shutil.which("pbcopy")
            if cmd_path:
                process = subprocess.Popen(
                    [cmd_path], stdin=subprocess.PIPE, close_fds=True
                )  # nosec B603
                process.communicate(b"", timeout=5)
                logger.info("Clipboard cleared using pbcopy")
                return True
        elif sys.platform == "linux":
            cmd_path = shutil.which("xclip")
            if cmd_path:
                process = subprocess.Popen(
                    [cmd_path, "-selection", "clipboard"],
                    stdin=subprocess.PIPE,
                    close_fds=True,
                )  # nosec B603
                process.communicate(b"", timeout=5)
                logger.info("Clipboard cleared using xclip")
                return True
        elif sys.platform == "win32":
            cmd_path = shutil.which("cmd")
            if cmd_path:
                process = subprocess.Popen(
                    [cmd_path, "/c", "echo off | clip"],
                    stdin=subprocess.PIPE,
                    close_fds=True,
                )  # nosec B603
                process.communicate(timeout=5)
                logger.info("Clipboard cleared using cmd/clip")
                return True
    except Exception as e:
        logger.debug(f"Clipboard clear failed: {e}")
    
    return False


def _schedule_clipboard_clear() -> None:
    """Schedule clipboard to be cleared after CLIPBOARD_AUTO_CLEAR_SECONDS."""
    def _delayed_clear():
        time.sleep(CLIPBOARD_AUTO_CLEAR_SECONDS)
        _clear_clipboard()
    
    # Run in a daemon thread so it doesn't prevent program exit
    clear_thread = threading.Thread(target=_delayed_clear, daemon=True)
    clear_thread.start()
    logger.debug(f"Scheduled clipboard auto-clear in {CLIPBOARD_AUTO_CLEAR_SECONDS} seconds")


def print_password_stats(gen, password: str) -> None:
    stats = gen.get_password_stats(password)

    print(f"\n{'=' * 60}")
    print("Password Analysis")
    print(f"{'=' * 60}")
    print(f"Password:       {password}")
    print(f"Length:         {stats['length']} characters")
    print(f"Entropy:        {stats['entropy']:.2f} bits")
    print(f"Strength:       {stats['strength']}")
    print(f"Unique chars:   {stats['unique_chars']}")
    print("\nCharacter Types:")
    print(f"  Uppercase:    {'YES' if stats['has_uppercase'] else 'NO'}")
    print(f"  Lowercase:    {'YES' if stats['has_lowercase'] else 'NO'}")
    print(f"  Digits:       {'YES' if stats['has_digits'] else 'NO'}")
    print(f"  Special:      {'YES' if stats['has_special'] else 'NO'}")
    print(f"\nValidation:     {stats['validation_message']}")
    print(f"{'=' * 60}\n")
