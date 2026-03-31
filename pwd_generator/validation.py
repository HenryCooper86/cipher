import string
import logging
import re
from typing import Tuple, Optional, List, Dict, Any
from pwd_generator.exceptions import ValidationError
from pwd_generator.constants import KEYBOARD_ROWS, SPECIAL_CHARS

logger = logging.getLogger(__name__)

KEYBOARD_PATTERNS = []
for row in KEYBOARD_ROWS:
    for i in range(len(row) - 2):
        seq = row[i : i + 3]
        escaped_seq = re.escape(seq)
        KEYBOARD_PATTERNS.append((re.compile(escaped_seq, re.IGNORECASE), seq))
        escaped_reverse = re.escape(seq[::-1])
        KEYBOARD_PATTERNS.append(
            (re.compile(escaped_reverse, re.IGNORECASE), seq[::-1])
        )


class PasswordValidator:
    def __init__(
        self,
        username: str = "",
        policy: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ):
        self.username = username.lower()
        self.policy = policy or {}
        self.history = history or []

        self.uppercase = string.ascii_uppercase
        self.lowercase = string.ascii_lowercase
        self.digits = string.digits
        self.special_chars = SPECIAL_CHARS
        self.uppercase_set = set(self.uppercase)
        self.lowercase_set = set(self.lowercase)
        self.digits_set = set(self.digits)
        self.special_chars_set = set(self.special_chars)
        self.keyboard_rows = KEYBOARD_ROWS

    def has_consecutive_pattern(self, password: str) -> bool:
        p_lower = password.lower()

        for i in range(len(password) - 2):
            chars = password[i : i + 3]
            if chars.isdigit() or chars.isalpha():
                diffs = [ord(chars[j + 1]) - ord(chars[j]) for j in range(2)]
                if all(d == 1 for d in diffs) or all(d == -1 for d in diffs):
                    logger.debug("Found consecutive pattern")
                    return True

        for pattern, seq in KEYBOARD_PATTERNS:
            if pattern.search(password):
                logger.debug("Found keyboard pattern")
                return True

        return False

    def has_username_leak(self, password: str) -> bool:
        if not self.username or len(self.username) < 3:
            return False

        p_lower = password.lower()
        for i in range(len(self.username) - 2):
            substring = self.username[i : i + 3]
            if substring in p_lower:
                logger.debug("Username leak detected")
                return True

        return False

    def has_repeated_characters(self, password: str, max_repeat: int = 3) -> bool:
        for i in range(len(password) - max_repeat + 1):
            if len(set(password[i : i + max_repeat])) == 1:
                logger.debug("Repeated character found")
                return True
        return False

    def calculate_entropy(self, text: str) -> float:
        import math

        text_set = set(text)
        char_set_size = 0
        if text_set & self.uppercase_set:
            char_set_size += 26
        if text_set & self.lowercase_set:
            char_set_size += 26
        if text_set & self.digits_set:
            char_set_size += 10
        if text_set & self.special_chars_set:
            char_set_size += len(self.special_chars)

        if char_set_size == 0:
            return 0.0

        return len(text) * math.log2(char_set_size)

    def calculate_strength_score(self, password: str) -> str:
        entropy = self.calculate_entropy(password)

        if entropy < 40:
            return "Weak"
        elif entropy < 60:
            return "Fair"
        elif entropy < 80:
            return "Good"
        elif entropy < 100:
            return "Strong"
        else:
            return "Very Strong"

    def validate(self, password: str, strict: bool = True) -> Tuple[bool, str]:
        import hashlib

        if len(password) < self.policy.get("min_length", 12):
            return False, f"Too short (min: {self.policy.get('min_length', 12)})"

        if len(password) > self.policy.get("max_length", 128):
            return False, f"Too long (max: {self.policy.get('max_length', 128)})"

        if strict:
            if self.policy.get("require_uppercase", True) and not any(
                c in self.uppercase for c in password
            ):
                return False, "Missing uppercase letter"

            if self.policy.get("require_lowercase", True) and not any(
                c in self.lowercase for c in password
            ):
                return False, "Missing lowercase letter"

            if self.policy.get("require_digits", True) and not any(
                c in self.digits for c in password
            ):
                return False, "Missing digit"

            if self.policy.get("require_special", True) and not any(
                c in self.special_chars for c in password
            ):
                return False, "Missing special character"

        if self.has_consecutive_pattern(password):
            return False, "Contains consecutive pattern (e.g., 123, abc, qwe)"

        if self.has_repeated_characters(password):
            return False, "Contains repeated characters (e.g., aaa, 111)"

        if self.has_username_leak(password):
            return False, "Contains username sequence"

        pwd_hash = hashlib.sha256(password.encode()).hexdigest()[:32]
        max_check = self.policy.get("max_history_check", 10)
        for entry in self.history[:max_check]:
            if entry.get("metadata", {}).get("hash") == pwd_hash:
                return False, "Recently used (password cycling prevented)"

        entropy = self.calculate_entropy(password)
        min_entropy = self.policy.get("min_entropy", 60)
        if entropy < min_entropy:
            return False, f"Entropy too low ({entropy:.1f} bits, min: {min_entropy})"

        return True, "Valid"
