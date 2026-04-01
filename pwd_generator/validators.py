import logging
from pathlib import Path


def validate_positive_int(value: str, field_name: str = "value", max_value: int = 10000) -> int:
    """Validate positive integer input with optional maximum."""
    try:
        num = int(value)
        if num <= 0:
            raise ValueError(f"{field_name} must be a positive number")
        if num > max_value:
            raise ValueError(f"{field_name} must be <= {max_value}")
        return num
    except ValueError as e:
        if "invalid literal" in str(e).lower():
            raise ValueError(f"{field_name} must be a valid number")
        raise


def validate_length(value: int, min_val: int, max_val: int, field_name: str = "length") -> int:
    if value < min_val:
        raise ValueError(f"{field_name} must be at least {min_val}")
    if value > max_val:
        raise ValueError(f"{field_name} must be at most {max_val}")
    return value


def validate_string(value: str, field_name: str = "value", allow_empty: bool = False, max_length: int = 1000) -> str:
    """Validate string input with length limits and character sanitization."""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    if len(value) > max_length:
        raise ValueError(f"{field_name} must be <= {max_length} characters")
    # Remove control characters (keep printable and whitespace)
    cleaned = ''.join(c for c in value if c.isprintable() or c.isspace())
    if cleaned != value:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Removed non-printable characters from {field_name}")
    return cleaned.strip()


def validate_file_path(user_path: str, base_dir=None, must_exist: bool = False) -> Path:
    """
    Validate and sanitize file paths to prevent path traversal attacks.

    Args:
        user_path: User-provided file path
        base_dir: Base directory to restrict paths to (default: current directory)
        must_exist: If True, file must exist

    Returns:
        Resolved Path object

    Raises:
        ValueError: If path is invalid or outside allowed directory
    """
    logging.getLogger(__name__)

    if not user_path:
        raise ValueError("Path cannot be empty")

    if base_dir is None:
        base_dir = Path.cwd()
    else:
        base_dir = Path(base_dir).resolve()

    # Remove null bytes and control characters
    if '\x00' in user_path:
        raise ValueError("Path cannot contain null bytes")

    # Resolve to absolute path
    try:
        # If user_path is absolute, we check if it starts with base_dir
        # If it's relative, we join with base_dir and resolve
        p = Path(user_path)
        if p.is_absolute():
            resolved = p.resolve()
        else:
            resolved = (base_dir / user_path).resolve()
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid path: {e}")

    # Ensure path is within base directory (prevent path traversal)
    try:
        resolved.relative_to(base_dir.resolve())
    except ValueError:
        raise ValueError(f"Path '{user_path}' is outside allowed directory")

    # Additional check for path traversal patterns
    if '..' in str(resolved) or resolved != resolved.resolve():
        raise ValueError("Path traversal not allowed")

    # Ensure resolved path (after following symlinks) is still within base_dir
    try:
        resolved.resolve(strict=False).relative_to(base_dir.resolve())
    except ValueError:
        raise ValueError("Path traversal not allowed")

    # Check if file exists (if required)
    if must_exist and not resolved.exists():
        raise ValueError(f"File does not exist: {user_path}")

    return resolved
