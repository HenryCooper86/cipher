"""User-facing CLI error messages (terminal and embedded Quick commands)."""

from __future__ import annotations

from pwd_generator.exceptions import (
    EncryptionError,
    FileOperationError,
    HistoryError,
    PasswordGeneratorError,
    ValidationError,
)


def format_cli_error_text(exc: BaseException) -> str | None:
    """
    Return a full user-facing block ending with a newline, or None if the caller
    should treat the exception as unexpected (log + generic message).
    """
    if isinstance(exc, ValidationError):
        return f"[ERROR] Validation failed: {exc}\n"
    if isinstance(exc, FileOperationError):
        lines = [f"[ERROR] File operation failed: {exc}"]
        if exc.details:
            lines.append(f"   Details: {exc.details}")
        return "\n".join(lines) + "\n"
    if isinstance(exc, HistoryError):
        return f"[ERROR] History operation failed: {exc}\n"
    if isinstance(exc, EncryptionError):
        lines = [
            f"[ERROR] Encryption error: {exc}",
            "",
            "This usually means:",
            "  - You entered a different master password than before",
            "  - The history file is corrupted",
        ]
        if exc.details:
            lines.append(f"   Details: {exc.details}")
        return "\n".join(lines) + "\n"
    if isinstance(exc, ValueError):
        return f"[ERROR] Invalid input: {exc}\n"
    if isinstance(exc, PasswordGeneratorError):
        lines = [f"[ERROR] {exc}"]
        if exc.details:
            lines.append(f"   Details: {exc.details}")
        return "\n".join(lines) + "\n"
    return None
