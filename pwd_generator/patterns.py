import logging
import re
import secrets
import string

from pwd_generator.constants import SPECIAL_CHARS

logger = logging.getLogger(__name__)


class PatternGenerator:
    def __init__(self):
        self.nouns = ["apple", "book", "car", "door", "eagle", "fish", "gate", "house", "ice", "jacket"]
        self.verbs = ["run", "jump", "walk", "sing", "dance", "write", "read", "play", "work", "think"]
        self.adjectives = ["big", "small", "fast", "slow", "bright", "dark", "happy", "sad", "new", "old"]
        self.special_chars = SPECIAL_CHARS

    def generate_from_pattern(self, pattern: str) -> str:
        """
        Generate password from pattern.

        Patterns:
        - [noun], [verb], [adj] - word lists
        - [word] - random word
        - [4letters] - 4 random letters
        - [2digits] - 2 random digits
        - [1special] - 1 special character
        - [upper], [lower], [number], [special] - character types
        """
        result = []
        i = 0

        while i < len(pattern):
            if pattern[i] == '[':
                end = pattern.find(']', i)
                if end == -1:
                    result.append(pattern[i])
                    i += 1
                    continue

                token = pattern[i+1:end]
                replacement = self._replace_token(token)
                result.append(replacement)
                i = end + 1
            else:
                result.append(pattern[i])
                i += 1

        return ''.join(result)

    def _replace_token(self, token: str) -> str:
        """Replace pattern token with actual value."""
        token_lower = token.lower()

        if token_lower == 'noun':
            return secrets.choice(self.nouns).capitalize()
        elif token_lower == 'verb':
            return secrets.choice(self.verbs).capitalize()
        elif token_lower == 'adj':
            return secrets.choice(self.adjectives).capitalize()
        elif token_lower == 'word':
            word = secrets.choice(self.nouns + self.verbs + self.adjectives)
            return word.capitalize() if secrets.randbelow(2) else word
        elif 'letters' in token_lower:
            if token_lower == 'letters':
                return ''.join(secrets.choice(string.ascii_letters) for _ in range(4))
            count = self._extract_number(token_lower, 'letters', 4)
            return ''.join(secrets.choice(string.ascii_letters) for _ in range(count))
        elif 'digits' in token_lower or 'numbers' in token_lower:
            if token_lower in ['digits', 'numbers']:
                return ''.join(secrets.choice(string.digits) for _ in range(2))
            count = self._extract_number(token_lower, 'digits', 2)
            return ''.join(secrets.choice(string.digits) for _ in range(count))
        elif 'special' in token_lower:
            if token_lower == 'special':
                return secrets.choice(self.special_chars)
            count = self._extract_number(token_lower, 'special', 1)
            return ''.join(secrets.choice(self.special_chars) for _ in range(count))
        elif token_lower == 'upper':
            return secrets.choice(string.ascii_uppercase)
        elif token_lower == 'lower':
            return secrets.choice(string.ascii_lowercase)
        elif token_lower == 'number':
            return secrets.choice(string.digits)
        else:
            return f'[{token}]'

    def _extract_number(self, token: str, prefix: str, default: int) -> int:
        """Extract number from token like '4letters' -> 4 or 'letters' -> default."""
        match = re.search(r'^(\d+)', token)
        if match:
            value = int(match.group(1))
            # Security: Limit extracted numbers to reasonable bounds (max 100 chars)
            max_value = 100
            if value > max_value:
                logger.warning(
                    f"Pattern token '{token}' exceeds maximum allowed value ({max_value}). "
                    f"Using {max_value} instead."
                )
                return max_value
            if value < 1:
                return default
            return value
        return default


def validate_pattern(pattern: str) -> tuple[bool, str]:
    """Validate pattern syntax with security checks."""
    if not pattern:
        return False, "Pattern cannot be empty"

    # Security: Limit pattern length to prevent DoS
    if len(pattern) > 1000:
        return False, "Pattern too long (max 1000 characters)"

    brackets = 0
    bracket_count = 0
    for char in pattern:
        if char == '[':
            brackets += 1
            bracket_count += 1
            # Security: Limit number of tokens to prevent resource exhaustion
            if bracket_count > 50:
                return False, "Too many tokens in pattern (max 50)"
        elif char == ']':
            brackets -= 1
            if brackets < 0:
                return False, "Unmatched closing bracket"

    if brackets != 0:
        return False, "Unmatched opening bracket"

    return True, "Valid pattern"
