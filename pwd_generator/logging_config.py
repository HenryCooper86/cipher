import logging
import logging.handlers
import sys
import os
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

        file_handler = SecureRotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
        
        # Set secure file permissions (owner read/write only)
        try:
            os.chmod(log_file, 0o600)
        except OSError:
            pass  # File may not exist yet, will be set after first write

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


class SecureRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Rotating file handler that ensures secure file permissions."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._permissions_set = False
        
    def emit(self, record):
        super().emit(record)
        # Set secure permissions after first write
        if not self._permissions_set:
            try:
                os.chmod(self.baseFilename, 0o600)
                self._permissions_set = True
            except OSError:
                pass
    
    def doRollover(self):
        super().doRollover()
        # Ensure new log file also has secure permissions
        try:
            os.chmod(self.baseFilename, 0o600)
        except OSError:
            pass


class SecurityFilter(logging.Filter):
    """Filter to prevent sensitive data from being logged."""

    # Patterns that indicate a secret value is present (usually key=value pairs)
    SENSITIVE_KEYS = [
        "password",
        "master_password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "private_key",
        "privatekey",
        "passphrase",
        "pin",
        "pwd",
        "ssid",
        "master",
        "credential",
        "auth",
        "key",
    ]

    # Standalone patterns that should trigger redaction of the whole message
    SENSITIVE_PATTERNS = [
        "password:",
        "secret:",
        "token:",
        "api_key=",
        "passphrase=",
    ]

    def filter(self, record):
        message = record.getMessage()
        message_lower = message.lower()

        # Only redact if there's a strong indicator of sensitive data
        if self._contains_sensitive_data(message_lower):
            # Safely redact by creating a new message without mutating args
            redacted = self._redact_sensitive(message)
            record.msg = redacted
            record.args = ()

        return True

    def _contains_sensitive_data(self, message_lower):
        """Check if message likely contains actual secret values."""
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message_lower:
                return True
        # Check for key=value patterns with sensitive keys
        for key in self.SENSITIVE_KEYS:
            if f"{key}=" in message_lower or f"{key}:" in message_lower:
                return True
        return False

    def _redact_sensitive(self, msg):
        """Redact sensitive information from log messages."""
        if not isinstance(msg, str):
            return msg

        import re

        # Redact key=value or key:value patterns for sensitive keys
        for key in self.SENSITIVE_KEYS:
            msg = re.sub(
                rf"({re.escape(key)}\s*[=:]\s*)[^\s]+",
                r"\1***REDACTED***",
                msg,
                flags=re.IGNORECASE,
            )

        return msg
