import sys
import subprocess
import logging
import getpass
from typing import Optional

logger = logging.getLogger(__name__)


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


def copy_to_clipboard(text: str) -> bool:
    try:
        import pyperclip

        pyperclip.copy(text)
        logger.info("Copied to clipboard using pyperclip")
        return True
    except ImportError:
        pass

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
                return True
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
                    return True
                except FileNotFoundError:
                    logger.debug("xclip found but execution failed")
        elif sys.platform == "win32":
            cmd_path = shutil.which("clip")
            if cmd_path:
                try:
                    process = subprocess.Popen(
                        [cmd_path], stdin=subprocess.PIPE, close_fds=True
                    )  # nosec B603
                    process.communicate(text.encode("utf-8"), timeout=5)
                    logger.info("Copied to clipboard using clip")
                    return True
                except Exception as e:
                    logger.debug(f"clip execution failed: {e}")
    except Exception as e:
        logger.warning(f"Clipboard copy failed: {e}")
        return False

    return False


def print_password_stats(gen, password: str) -> None:
    stats = gen.get_password_stats(password)

    print(f"\n{'=' * 60}")
    print(f"Password Analysis")
    print(f"{'=' * 60}")
    print(f"Password:       {password}")
    print(f"Length:         {stats['length']} characters")
    print(f"Entropy:        {stats['entropy']:.2f} bits")
    print(f"Strength:       {stats['strength']}")
    print(f"Unique chars:   {stats['unique_chars']}")
    print(f"\nCharacter Types:")
    print(f"  Uppercase:    {'YES' if stats['has_uppercase'] else 'NO'}")
    print(f"  Lowercase:    {'YES' if stats['has_lowercase'] else 'NO'}")
    print(f"  Digits:       {'YES' if stats['has_digits'] else 'NO'}")
    print(f"  Special:      {'YES' if stats['has_special'] else 'NO'}")
    print(f"\nValidation:     {stats['validation_message']}")
    print(f"{'=' * 60}\n")
