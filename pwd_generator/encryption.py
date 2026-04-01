import base64
import json
import logging
import os
import secrets
import time
import warnings
from pathlib import Path
from threading import Lock
from typing import Optional, Union

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from pwd_generator.constants import (
    KDF_ITERATIONS,
    MIN_MASTER_PASSWORD_ENTROPY,
    MIN_MASTER_PASSWORD_LENGTH,
    SALT_SIZE,
)
from pwd_generator.exceptions import (
    EncryptionError,
    HistoryError,
    ValidationError,
)

logger = logging.getLogger(__name__)

# Optional: install the `argon2-cffi` package (extra `argon2` in pyproject.toml) to
# enable Argon2-based KDF when creating new vault material. Default storage uses PBKDF2.
ARGON2_AVAILABLE = False
try:
    from argon2 import low_level

    ARGON2_AVAILABLE = True
except ImportError:
    low_level = None


# Brute-force protection constants
MAX_DECRYPTION_ATTEMPTS = 5  # Maximum failed attempts before lockout
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes lockout after max attempts
DECRYPTION_ATTEMPT_FILE = ".decryption_attempts"

# Global tracking for decryption attempts (in-memory, per-process)
_decryption_attempts: dict[str, list[float]] = {}
_attempt_lock = Lock()


def _get_vault_id() -> str:
    """Get a unique identifier for the current vault for attempt tracking."""
    # Use a combination of hostname and a fixed salt for vault identification
    import socket
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "unknown"
    return f"{hostname}_{os.getcwd()}"


def _is_locked_out() -> bool:
    """Check if the vault is currently locked out due to too many failed attempts."""
    with _attempt_lock:
        vault_id = _get_vault_id()
        now = time.time()
        
        # Clean up old attempts
        if vault_id in _decryption_attempts:
            _decryption_attempts[vault_id] = [
                t for t in _decryption_attempts[vault_id]
                if now - t < LOCKOUT_DURATION_SECONDS
            ]
        
        # Check if locked out
        if vault_id in _decryption_attempts:
            attempts = _decryption_attempts[vault_id]
            if len(attempts) >= MAX_DECRYPTION_ATTEMPTS:
                # Check if oldest attempt is within lockout period
                if attempts and (now - attempts[0]) < LOCKOUT_DURATION_SECONDS:
                    remaining = LOCKOUT_DURATION_SECONDS - (now - attempts[0])
                    logger.warning(
                        f"Vault locked out due to {len(attempts)} failed attempts. "
                        f"Try again in {int(remaining)} seconds."
                    )
                    return True
                else:
                    # Lockout period expired, clear attempts
                    _decryption_attempts[vault_id] = []
        
        return False


def _record_failed_attempt() -> None:
    """Record a failed decryption attempt."""
    with _attempt_lock:
        vault_id = _get_vault_id()
        now = time.time()
        
        if vault_id not in _decryption_attempts:
            _decryption_attempts[vault_id] = []
        
        _decryption_attempts[vault_id].append(now)
        
        # Log warning if approaching lockout
        if len(_decryption_attempts[vault_id]) >= MAX_DECRYPTION_ATTEMPTS - 2:
            remaining = MAX_DECRYPTION_ATTEMPTS - len(_decryption_attempts[vault_id])
            logger.warning(
                f"Failed decryption attempt recorded. "
                f"{remaining} attempts remaining before lockout."
            )


def _clear_failed_attempts() -> None:
    """Clear all failed attempts after successful decryption."""
    with _attempt_lock:
        vault_id = _get_vault_id()
        if vault_id in _decryption_attempts:
            _decryption_attempts[vault_id] = []
        logger.debug("Cleared failed decryption attempts after successful auth")


def check_brute_force_protection() -> tuple[bool, str]:
    """
    Check if decryption is allowed based on brute-force protection.
    
    Returns:
        Tuple of (is_allowed, message)
    """
    if _is_locked_out():
        vault_id = _get_vault_id()
        now = time.time()
        if vault_id in _decryption_attempts and _decryption_attempts[vault_id]:
            oldest = min(_decryption_attempts[vault_id])
            remaining = LOCKOUT_DURATION_SECONDS - (now - oldest)
            return False, f"Locked out. Try again in {int(remaining)} seconds."
        return False, "Temporarily locked out due to too many failed attempts."
    
    return True, "OK"


def clear_memory(data: Union[bytearray, bytes, str]) -> bool:
    """
    Attempt to securely clear sensitive data from memory.

    Args:
        data: The data to clear. Can be bytearray, bytes, or str.

    Returns:
        bool: True if data was successfully cleared, False otherwise.

    Note:
        - bytearray: Can be securely cleared in place (returns True)
        - bytes/str: Are immutable in Python and CANNOT be securely cleared.
                     For maximum security, always use bytearray for sensitive data.
                     This function will issue a warning and return False for
                     immutable types.
    """
    if data is None:
        return True

    if isinstance(data, bytearray):
        try:
            for i in range(len(data)):
                data[i] = 0
            return True
        except Exception as e:
            logger.warning(f"Failed to clear bytearray: {e}")
            return False
    elif isinstance(data, bytes):
        # bytes are immutable - cannot be cleared
        # Issue warning for security-conscious users
        warnings.warn(
            "Cannot securely clear immutable 'bytes' object from memory. "
            "Use 'bytearray' for sensitive data that needs to be cleared.",
            UserWarning,
            stacklevel=2
        )
        logger.warning("Attempted to clear immutable bytes object - data remains in memory")
        return False
    elif isinstance(data, str):
        # strings are immutable - cannot be cleared
        warnings.warn(
            "Cannot securely clear immutable 'str' object from memory. "
            "Use 'bytearray' for sensitive data that needs to be cleared.",
            UserWarning,
            stacklevel=2
        )
        logger.warning("Attempted to clear immutable str object - data remains in memory")
        return False
    else:
        logger.warning(f"Unknown data type for memory clearing: {type(data)}")
        return False


class EncryptionManager:
    def __init__(self, history_file: str = "password_history.enc"):
        self.history_file = Path(history_file)
        self.cipher: Optional[Fernet] = None
        self.salt: Optional[bytes] = None

    def validate_master_password(
        self, master_password: Union[str, bytearray, bytes], entropy_calculator
    ) -> None:
        if isinstance(master_password, str):
            pw_str = master_password
        else:
            pw_str = master_password.decode("utf-8")
        if len(pw_str) < MIN_MASTER_PASSWORD_LENGTH:
            raise ValidationError(
                f"Master password must be at least {MIN_MASTER_PASSWORD_LENGTH} characters"
            )

        entropy = entropy_calculator(pw_str)
        if entropy < MIN_MASTER_PASSWORD_ENTROPY:
            raise ValidationError(
                f"Master password entropy too low ({entropy:.1f} bits). "
                f"Minimum required: {MIN_MASTER_PASSWORD_ENTROPY} bits"
            )

        logger.info(f"Master password validated (entropy: {entropy:.1f} bits)")

    def init_encryption_system(
        self,
        master_password: Union[str, bytearray, bytes],
        provided_salt: Optional[bytes] = None,
        use_argon2: bool = True,
    ) -> None:
        try:
            if provided_salt:
                self.salt = provided_salt
            else:
                self.salt = secrets.token_bytes(SALT_SIZE)

            if isinstance(master_password, bytearray):
                pw_bytes = bytes(master_password)
            elif isinstance(master_password, str):
                pw_bytes = master_password.encode("utf-8")
            else:
                pw_bytes = master_password

            if use_argon2 and ARGON2_AVAILABLE and low_level is not None:
                from pwd_generator.constants import (
                    ARGON2_MEMORY_COST,
                    ARGON2_PARALLELISM,
                    ARGON2_TIME_COST,
                )

                key_raw = low_level.hash_secret_raw(
                    secret=pw_bytes,
                    salt=self.salt,
                    time_cost=ARGON2_TIME_COST,
                    memory_cost=ARGON2_MEMORY_COST,
                    parallelism=ARGON2_PARALLELISM,
                    hash_len=32,
                    type=low_level.Type.ID,
                )
                logger.debug("Using Argon2id (argon2-cffi) for key derivation")
                key = base64.urlsafe_b64encode(key_raw)
            else:
                if use_argon2 and (not ARGON2_AVAILABLE or low_level is None):
                    logger.warning(
                        "Argon2 requested but not available, falling back to PBKDF2"
                    )

                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=self.salt,
                    iterations=KDF_ITERATIONS,
                )
                logger.debug("Using PBKDF2 for key derivation")
                key = base64.urlsafe_b64encode(kdf.derive(pw_bytes))

            self.cipher = Fernet(key)
            logger.debug("Encryption system initialized")

        except (ValueError, TypeError) as e:
            logger.error(f"Invalid encryption parameters: {e}")
            raise EncryptionError(f"Encryption initialization failed: {e}")
        except SystemExit:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise EncryptionError(f"Encryption initialization failed: {e}")

    def load_history(self, master_password: Union[str, bytearray, bytes]) -> list[dict]:
        if not self.history_file.exists():
            logger.info("No history file found, starting fresh")
            return []

        try:
            with open(self.history_file, "rb") as f:
                raw_content = f.read()

            # Check minimum size (at least salt + some ciphertext)
            if len(raw_content) < SALT_SIZE + 1:
                logger.warning("History file too small, starting fresh")
                return []

            method_flag = raw_content[0]
            
            # Determine format: modern (method_flag 0 or 1) or legacy (any other value)
            if method_flag in [0, 1]:
                # Modern format: [method_flag][salt][ciphertext]
                self.salt = raw_content[1 : SALT_SIZE + 1]
                ciphertext = raw_content[SALT_SIZE + 1 :]
                use_argon2 = method_flag == 1
            else:
                # Legacy format: [salt][ciphertext] (no method flag)
                self.salt = raw_content[:SALT_SIZE]
                ciphertext = raw_content[SALT_SIZE:]
                use_argon2 = False

            # Initialize encryption system
            self.init_encryption_system(
                master_password, self.salt, use_argon2=use_argon2
            )

            if not self.cipher:
                raise EncryptionError("Failed to initialize encryption cipher")

            try:
                decrypted = self.cipher.decrypt(ciphertext).decode()
                history_data = json.loads(decrypted).get("history", [])
                logger.info(f"Loaded {len(history_data)} password entries from history")
                return history_data
            except InvalidToken:
                logger.error("Failed to decrypt history - incorrect master password")
                raise EncryptionError("Incorrect master password or corrupted history file")
            except json.JSONDecodeError as e:
                logger.error(f"History file corrupted: {e}")
                raise EncryptionError("History file is corrupted")

        except EncryptionError:
            raise
        except OSError as e:
            logger.error(f"File I/O error loading history: {e}")
            raise EncryptionError(f"Failed to load history: {e}")
        except SystemExit:
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading history: {e}")
            raise EncryptionError(f"Failed to load history: {e}")

    def save_history(self, history: list[dict]) -> None:
        if not self.cipher or self.salt is None:
            logger.error("Cannot save history: encryption not initialized")
            raise HistoryError(
                "Cannot save history: encryption system not initialized. "
                "Please provide a valid master password."
            )

        try:
            payload = json.dumps({"history": history}, indent=2).encode()
            method_flag = b"\x01" if ARGON2_AVAILABLE else b"\x00"
            encrypted = method_flag + self.salt + self.cipher.encrypt(payload)

            temp_file = self.history_file.with_suffix(".tmp")
            with open(temp_file, "wb") as f:
                f.write(encrypted)
                f.flush()
                os.fsync(f.fileno())

            os.chmod(temp_file, 0o600)
            temp_file.replace(self.history_file)
            logger.debug(
                f"History saved and secured ({'Argon2id' if ARGON2_AVAILABLE else 'PBKDF2'})"
            )
        except (OSError, PermissionError) as e:
            logger.error(f"File operation error saving history: {e}")
            raise EncryptionError(f"Failed to save history: {e}")
        except (TypeError, ValueError) as e:
            logger.error(f"Data formatting error saving history: {e}")
            raise EncryptionError(f"Failed to save history: {e}")
