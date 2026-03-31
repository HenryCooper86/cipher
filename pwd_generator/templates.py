import secrets
import string
import logging
from typing import List, Optional, Set
from pwd_generator.constants import SPECIAL_CHARS

logger = logging.getLogger(__name__)


class PasswordTemplate:
    def __init__(self, 
                 name: str,
                 uppercase: bool = True,
                 lowercase: bool = True,
                 digits: bool = True,
                 special: bool = True,
                 exclude_chars: Optional[str] = None,
                 custom_special: Optional[str] = None,
                 min_length: int = 12):
        self.name = name
        self.uppercase = string.ascii_uppercase if uppercase else ""
        self.lowercase = string.ascii_lowercase if lowercase else ""
        self.digits = string.digits if digits else ""
        
        if custom_special:
            self.special = custom_special
        elif special:
            self.special = SPECIAL_CHARS
        else:
            self.special = ""
        
        if exclude_chars:
            for char in exclude_chars:
                self.uppercase = self.uppercase.replace(char, '')
                self.lowercase = self.lowercase.replace(char, '')
                self.digits = self.digits.replace(char, '')
                self.special = self.special.replace(char, '')
        
        self.all_chars = self.uppercase + self.lowercase + self.digits + self.special
        self.min_length = min_length
        
        if not self.all_chars:
            raise ValueError("Template must include at least one character type")
    
    def generate(self, length: int) -> str:
        if length < self.min_length:
            logger.warning(f"Requested length {length} < minimum {self.min_length}")
            length = self.min_length
        
        chars = []
        if self.uppercase:
            chars.append(secrets.choice(self.uppercase))
        if self.lowercase:
            chars.append(secrets.choice(self.lowercase))
        if self.digits:
            chars.append(secrets.choice(self.digits))
        if self.special:
            chars.append(secrets.choice(self.special))
        
        while len(chars) < length:
            chars.append(secrets.choice(self.all_chars))
        
        secrets.SystemRandom().shuffle(chars)
        return "".join(chars)


# Predefined templates
TEMPLATES = {
    'alphanumeric': PasswordTemplate(
        name='alphanumeric',
        special=False,
        min_length=12
    ),
    'numeric_only': PasswordTemplate(
        name='numeric_only',
        uppercase=False,
        lowercase=False,
        special=False,
        min_length=6
    ),
    'letters_only': PasswordTemplate(
        name='letters_only',
        digits=False,
        special=False,
        min_length=12
    ),
    'no_special': PasswordTemplate(
        name='no_special',
        special=False,
        min_length=12
    ),
    'url_safe': PasswordTemplate(
        name='url_safe',
        custom_special='-_',
        exclude_chars='@#$!?^&*~()[]=.',
        min_length=12
    ),
    'readable': PasswordTemplate(
        name='readable',
        exclude_chars='0O1lI',
        min_length=12
    )
}


def get_template(name: str) -> Optional[PasswordTemplate]:
    return TEMPLATES.get(name.lower())


def list_templates() -> List[str]:
    return list(TEMPLATES.keys())
