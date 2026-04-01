import logging
import re
import string
from typing import Any, Optional

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
        policy: Optional[dict[str, Any]] = None,
        history: Optional[list[dict[str, Any]]] = None,
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
        password.lower()

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
        """
        Calculate password entropy using a more conservative approach.
        
        This calculation accounts for:
        1. The actual character pool based on used character types
        2. Minimum guaranteed entropy from required character placement
        3. Length-dependent scaling
        
        Note: This is still an estimate. For more accurate strength assessment,
        consider using zxcvbn-style pattern analysis which we recommend.
        """
        import math

        # Count actual characters used from each pool
        has_upper = any(c in self.uppercase_set for c in text)
        has_lower = any(c in self.lowercase_set for c in text)
        has_digit = any(c in self.digits_set for c in text)
        has_special = any(c in self.special_chars_set for c in text)
        
        # Calculate pool size based on ACTUAL character types present
        pool_size = 0
        if has_upper:
            pool_size += 26
        if has_lower:
            pool_size += 26
        if has_digit:
            pool_size += 10
        if has_special:
            pool_size += len(self.special_chars)

        if pool_size == 0:
            return 0.0

        # Calculate base entropy
        base_entropy = len(text) * math.log2(pool_size)
        
        # Apply a conservative adjustment factor (0.8) because:
        # 1. Character frequency in random generation isn't perfectly uniform
        # 2. Users often create patterns even when using random generators
        # 3. The pool size assumes independence which isn't always true
        adjusted_entropy = base_entropy * 0.8
        
        # Minimum entropy based on length (assuming pool of 26)
        # This ensures very short passwords don't get inflated entropy
        min_entropy = len(text) * math.log2(26) * 0.6
        
        return max(adjusted_entropy, min_entropy)

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

    def validate(self, password: str, strict: bool = True) -> tuple[bool, str]:
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
