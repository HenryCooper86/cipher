import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: Optional[str] = None,
    verbose: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    Setup logging with rotation and security considerations.

    Args:
        log_file: Path to log file (default: password_generator.log)
        verbose: Enable debug logging
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
    """
    level = logging.DEBUG if verbose else logging.INFO

    handlers = []

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    # Apply security filter to all handlers
    security_filter = SecurityFilter()
    for handler in handlers:
        handler.addFilter(security_filter)

    logging.basicConfig(
        level=level,
        handlers=handlers,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("Logging initialized")


class SecurityFilter(logging.Filter):
    """Filter to prevent sensitive data from being logged."""

    SENSITIVE_PATTERNS = [
        "password",
        "master_password",
        "secret",
        "token",
        "key",
        "ssid",
        "wifi",
        "service",
        "username",
        "user",
        "email",
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "private_key",
        "privatekey",
        "passphrase",
        "pin",
        "pwd",
    ]

    def filter(self, record):
        message = record.getMessage()
        message_lower = message.lower()

        # Check if message contains sensitive patterns
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message_lower:
                record.msg = self._redact_sensitive(record.msg)
                record.args = ()
                break  # Only redact once

        return True

    def _redact_sensitive(self, msg):
        """Redact sensitive information from log messages."""
        if isinstance(msg, str):
            # Use regex to find and replace sensitive patterns more accurately
            import re

            words = msg.split()
            redacted = []
            for word in words:
                word_lower = word.lower()
                # Check if word contains any sensitive pattern
                if any(pattern in word_lower for pattern in self.SENSITIVE_PATTERNS):
                    # Try to preserve structure (e.g., "password=xxx" -> "password=***REDACTED***")
                    if "=" in word:
                        key, _ = word.split("=", 1)
                        redacted.append(f"{key}=***REDACTED***")
                    elif ":" in word:
                        key, _ = word.split(":", 1)
                        redacted.append(f"{key}:***REDACTED***")
                    else:
                        redacted.append("***REDACTED***")
                else:
                    redacted.append(word)
            return " ".join(redacted)
        return msg
