import hashlib
import logging
import secrets
import string
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from pwd_generator.constants import DEFAULT_POLICY, SPECIAL_CHARS, WORDLIST
from pwd_generator.encryption import EncryptionManager
from pwd_generator.exceptions import (
    EncryptionError,
    HistoryError,
    ValidationError,
)
from pwd_generator.validation import PasswordValidator

logger = logging.getLogger(__name__)


class SecurePasswordGenerator:
    def __init__(
        self,
        username: str = "",
        history_file: str = "password_history.enc",
        master_password: Optional[Union[str, bytearray, bytes]] = None,
        policy: Optional[dict[str, Any]] = None,
        profile: Optional[str] = None,
    ):
        self.username = username.lower()
        self.history_file = Path(history_file)

        if profile:
            from pwd_generator.profiles import ProfileManager

            manager = ProfileManager()
            profile_obj = manager.get_profile(profile)
            if profile_obj:
                base_policy = {**DEFAULT_POLICY, **(policy or {})}
                self.policy = {**base_policy, **profile_obj.policy}
                self.profile_template = profile_obj.template
                logger.info(
                    f"Using profile '{profile}' with policy: min_length={self.policy.get('min_length')}, min_entropy={self.policy.get('min_entropy')}"
                )
            else:
                logger.warning(f"Profile '{profile}' not found, using default policy")
                self.policy = {**DEFAULT_POLICY, **(policy or {})}
                self.profile_template = None
        else:
            self.policy = {**DEFAULT_POLICY, **(policy or {})}
            self.profile_template = None

        self.encryption_manager = EncryptionManager(str(self.history_file))
        self.history: list[dict] = []
        self.session_generated: set[str] = set()

        self.uppercase = string.ascii_uppercase
        self.lowercase = string.ascii_lowercase
        self.digits = string.digits
        self.special_chars = SPECIAL_CHARS
        self.all_chars = (
            self.uppercase + self.lowercase + self.digits + self.special_chars
        )

        self.validator = PasswordValidator(username, self.policy, self.history)

        if master_password:
            self.encryption_manager.validate_master_password(
                master_password, self.validator.calculate_entropy
            )
            self.encryption_manager.init_encryption_system(master_password)
            self.history = self.encryption_manager.load_history(master_password)
            self.validator.history = self.history
            logger.info("Password generator initialized with encrypted history")
        else:
            logger.warning("No master password provided - history features disabled")

    def add_to_history(
        self,
        password: str,
        service: str = "",
        notes: str = "",
        qr_code_path: Optional[str] = None,
        qr_code_type: Optional[str] = None,
    ) -> bool:
        """
        Add a password entry to encrypted history.

        Returns:
            bool: True if successfully added, False if encryption not initialized.

        Raises:
            HistoryError: If there's an error saving to history.
        """
        if not self.encryption_manager.cipher:
            logger.warning("Cannot add to history - encryption not initialized")
            return False

        entry = {
            "password": password,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "service": service,
                "notes": notes,
                "hash": hashlib.sha256(password.encode()).hexdigest()[:32],
                "strength": self.validator.calculate_strength_score(password),
                "entropy": round(self.validator.calculate_entropy(password), 2),
            },
        }

        if qr_code_path:
            entry["metadata"]["qr_code_path"] = qr_code_path
            entry["metadata"]["qr_code_type"] = qr_code_type or "password"

        self.history.insert(0, entry)

        max_size = self.policy.get("max_history_size", 1000)
        if len(self.history) > max_size:
            removed = self.history.pop()
            logger.info(
                f"History limit reached ({max_size}), removed oldest entry: {removed['metadata']['service']}"
            )

        self.validator.history = self.history
        try:
            self.encryption_manager.save_history(self.history)
            logger.info(f"Added password for '{service}' to history")
            return True
        except (HistoryError, EncryptionError) as e:
            logger.error(f"Failed to save history: {e}")
            # Remove the entry we just added since save failed
            self.history.pop(0)
            raise HistoryError(f"Failed to add password to history: {e}")

    def calculate_entropy(self, text: str) -> float:
        return self.validator.calculate_entropy(text)

    def calculate_strength_score(self, password: str) -> str:
        return self.validator.calculate_strength_score(password)

    def validate(self, password: str, strict: bool = True) -> tuple[bool, str]:
        return self.validator.validate(password, strict)

    def generate_random_string(self, length: int = 16, max_attempts: int = 1000) -> str:
        if self.profile_template:
            from pwd_generator.templates import get_template

            template = get_template(self.profile_template)
            if template:
                if length < template.min_length:
                    logger.warning(
                        f"Requested length {length} < template minimum {template.min_length}"
                    )
                    length = template.min_length
                return template.generate(length)

        if length < self.policy["min_length"]:
            logger.warning(
                f"Requested length {length} < minimum {self.policy['min_length']}"
            )
            length = self.policy["min_length"]

        for attempt in range(max_attempts):
            chars = [
                secrets.choice(self.uppercase),
                secrets.choice(self.lowercase),
                secrets.choice(self.digits),
                secrets.choice(self.special_chars),
            ]

            chars += [secrets.choice(self.all_chars) for _ in range(length - 4)]

            secrets.SystemRandom().shuffle(chars)
            pwd = "".join(chars)

            is_valid, reason = self.validate(pwd)
            if is_valid:
                self.session_generated.add(pwd)
                logger.info(
                    f"Generated random password (length: {length}, entropy: {self.calculate_entropy(pwd):.1f})"
                )
                return pwd

            if attempt % 100 == 0 and attempt > 0:
                logger.debug(f"Generation attempt {attempt}: {reason}")

        logger.error(f"Failed to generate valid password after {max_attempts} attempts")
        raise ValidationError(
            f"Unable to generate valid password after {max_attempts} attempts. Policy may be too restrictive."
        )

    def generate_passphrase(self, num_words: int = 5, separator: str = "-") -> str:
        if num_words < 4:
            logger.warning("Passphrase should have at least 4 words for security")
            num_words = 4

        words = []
        for _ in range(num_words):
            word = secrets.choice(WORDLIST)
            if secrets.randbelow(100) < 40:
                word = word.capitalize()
            words.append(word)

        passphrase = separator.join(words)

        passphrase += str(secrets.randbelow(100))
        passphrase += secrets.choice(self.special_chars)

        logger.info(
            f"Generated passphrase ({num_words} words, entropy: {self.calculate_entropy(passphrase):.1f})"
        )
        return passphrase

    def generate_pin(self, length: int = 6, max_attempts: int = 10000) -> str:
        for attempt in range(max_attempts):
            pin = "".join(str(secrets.randbelow(10)) for _ in range(length))

            if len(set(pin)) < 3:
                continue

            has_sequence = False
            for i in range(len(pin) - 2):
                diffs = [
                    int(pin[i + 1]) - int(pin[i]),
                    int(pin[i + 2]) - int(pin[i + 1]),
                ]
                if all(d == 1 for d in diffs) or all(d == -1 for d in diffs):
                    has_sequence = True
                    break

            if not has_sequence:
                logger.info(f"Generated PIN (length: {length})")
                return pin

        logger.error(f"Failed to generate valid PIN after {max_attempts} attempts")
        raise ValidationError(
            f"Unable to generate valid PIN after {max_attempts} attempts. Try a different length."
        )

    def check_password_breach(self, password: str) -> tuple[bool, dict[str, Any]]:
        from pwd_generator.breach_check import check_password_breach

        return check_password_breach(password)

    def get_password_stats(self, password: str) -> dict[str, Any]:
        is_valid, validation_message = self.validate(password)
        entropy = self.calculate_entropy(password)
        return {
            "length": len(password),
            "entropy": round(entropy, 2),
            "strength": self.calculate_strength_score(password),
            "has_uppercase": any(c in self.uppercase for c in password),
            "has_lowercase": any(c in self.lowercase for c in password),
            "has_digits": any(c in self.digits for c in password),
            "has_special": any(c in self.special_chars for c in password),
            "unique_chars": len(set(password)),
            "is_valid": is_valid,
            "validation_message": validation_message,
        }

    def delete_from_history(self, index: int) -> bool:
        if not self.encryption_manager.cipher:
            logger.warning("Cannot delete from history - encryption not initialized")
            return False

        if 0 <= index < len(self.history):
            deleted = self.history.pop(index)
            self.validator.history = self.history
            self.encryption_manager.save_history(self.history)
            logger.info(
                f"Deleted password for '{deleted['metadata']['service']}' from history"
            )
            return True
        return False

    def update_history_entry(
        self, index: int, service: Optional[str] = None, notes: Optional[str] = None
    ) -> bool:
        if not self.encryption_manager.cipher:
            logger.warning("Cannot update history - encryption not initialized")
            return False

        if 0 <= index < len(self.history):
            if service is not None:
                self.history[index]["metadata"]["service"] = service
            if notes is not None:
                self.history[index]["metadata"]["notes"] = notes
            self.encryption_manager.save_history(self.history)
            logger.info(f"Updated history entry at index {index}")
            return True
        return False

    def get_expired_passwords(self) -> list[tuple[int, dict]]:
        expired = []
        expiration_days = self.policy["expiration_days"]

        for i, entry in enumerate(self.history):
            try:
                created_at_str = entry.get("metadata", {}).get("created_at")
                if not created_at_str:
                    continue
                created_at = datetime.fromisoformat(created_at_str)
                age = datetime.now() - created_at

                if age.days > expiration_days:
                    expired.append((i, entry))
            except (KeyError, ValueError, TypeError):
                continue

        return expired

    def copy_to_clipboard(self, text: str) -> bool:
        from pwd_generator.utils import copy_to_clipboard

        return copy_to_clipboard(text)

    def batch_generate(
        self,
        count: int,
        length: int = 16,
        password_type: str = "random",
        show_progress: bool = True,
    ) -> list[str]:
        from pwd_generator.progress import show_progress as progress_bar

        passwords = []
        iterator = range(count)

        if show_progress:
            iterator = progress_bar(
                range(count), f"Generating {password_type} passwords", count
            )

        for _ in iterator:
            if password_type == "random":
                pwd = self.generate_random_string(length)
            elif password_type == "passphrase":
                words = max(4, length // 4)
                pwd = self.generate_passphrase(words)
            elif password_type == "pin":
                pwd = self.generate_pin(length if length <= 10 else 6)
            else:
                raise ValueError(f"Unknown password type: {password_type}")

            passwords.append(pwd)

        logger.info(f"Batch generated {count} {password_type} passwords")
        return passwords

    def clear_sensitive_data(self) -> None:
        self.session_generated.clear()
        logger.debug("Sensitive data cleared from session")
