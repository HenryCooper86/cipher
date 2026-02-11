import json
import os
import secrets
import base64
import logging
from typing import List, Dict, Optional, Union
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pwd_generator.exceptions import EncryptionError, ValidationError
from pwd_generator.constants import (
    KDF_ITERATIONS,
    SALT_SIZE,
    MIN_MASTER_PASSWORD_LENGTH,
    MIN_MASTER_PASSWORD_ENTROPY,
    ARGON2_TIME_COST,
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
)

logger = logging.getLogger(__name__)

ARGON2_AVAILABLE = False
try:
    from argon2 import low_level

    ARGON2_AVAILABLE = True
except ImportError:
    low_level = None


def clear_memory(data: Union[bytearray, bytes, str]):
    if isinstance(data, bytearray):
        for i in range(len(data)):
            data[i] = 0
    elif isinstance(data, (bytes, str)):
        pass


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
                    ARGON2_TIME_COST,
                    ARGON2_MEMORY_COST,
                    ARGON2_PARALLELISM,
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
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise EncryptionError(f"Encryption initialization failed: {e}")

    def load_history(self, master_password: Union[str, bytearray, bytes]) -> List[Dict]:
        if not self.history_file.exists():
            logger.info("No history file found, starting fresh")
            return []

        try:
            with open(self.history_file, "rb") as f:
                raw_content = f.read()

            if len(raw_content) <= SALT_SIZE + 1:
                logger.warning("History file too small, starting fresh")
                return []

            method_flag = raw_content[0]
            if method_flag in [0, 1]:
                self.salt = raw_content[1 : SALT_SIZE + 1]
                ciphertext = raw_content[SALT_SIZE + 1 :]
                use_argon2 = method_flag == 1
            else:
                self.salt = raw_content[:SALT_SIZE]
                ciphertext = raw_content[SALT_SIZE:]
                use_argon2 = False

            self.init_encryption_system(
                master_password, self.salt, use_argon2=use_argon2
            )

            if not self.cipher:
                raise EncryptionError("Failed to initialize encryption cipher")

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
        except (OSError, IOError) as e:
            logger.error(f"File I/O error loading history: {e}")
            raise EncryptionError(f"Failed to load history: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading history: {e}")
            raise EncryptionError(f"Failed to load history: {e}")

    def save_history(self, history: List[Dict]) -> None:
        if not self.cipher or self.salt is None:
            logger.error("Cannot save history: encryption not initialized")
            return

        try:
            payload = json.dumps({"history": history}, indent=2).encode()
            method_flag = b"\x01" if ARGON2_AVAILABLE else b"\x00"
            encrypted = method_flag + self.salt + self.cipher.encrypt(payload)

            temp_file = self.history_file.with_suffix(".tmp")
            with open(temp_file, "wb") as f:
                f.write(encrypted)

            os.chmod(temp_file, 0o600)
            temp_file.replace(self.history_file)
            logger.debug(
                f"History saved and secured ({'Argon2id' if ARGON2_AVAILABLE else 'PBKDF2'})"
            )
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"File operation error saving history: {e}")
            raise EncryptionError(f"Failed to save history: {e}")
        except (TypeError, ValueError) as e:
            logger.error(f"Data formatting error saving history: {e}")
            raise EncryptionError(f"Failed to save history: {e}")
