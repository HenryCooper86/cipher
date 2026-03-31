import hmac
from typing import Optional

from pwd_generator import SecurePasswordGenerator
from pwd_generator.encryption import clear_memory
from pwd_generator.exceptions import ValidationError
from pwd_generator.utils import prompt_yes_no, safe_getpass


def constant_time_compare(a: bytearray, b: bytearray) -> bool:
    """
    Constant-time comparison to prevent timing attacks.
    Uses hmac.compare_digest for secure comparison.
    """
    return hmac.compare_digest(bytes(a), bytes(b))


def setup_logging(log_file: Optional[str] = None, verbose: bool = False):
    from pwd_generator.logging_config import setup_logging as setup_logging_enhanced

    setup_logging_enhanced(log_file, verbose)


def get_master_password(history_exists: bool = False) -> Optional[bytearray]:
    if not history_exists:
        print(
            "Welcome! This appears to be your first time using the password generator."
        )
        print("Let's create a master password to encrypt your password history.")
        print()

        while True:
            master_password = safe_getpass("Create a master password (12+ chars): ")
            if not master_password:
                return None

            confirm = safe_getpass("Confirm master password: ")
            if not constant_time_compare(master_password, confirm):
                print("Passwords don't match. Please try again.")
                print()
                clear_memory(master_password)
                clear_memory(confirm)
                continue

            clear_memory(confirm)
            try:
                SecurePasswordGenerator(master_password=master_password)
                print("Master password created successfully!")
                return master_password
            except ValidationError as e:
                print(f"{e}")
                clear_memory(master_password)
                if not prompt_yes_no("Try again?", default=True):
                    return None
    else:
        master_password = safe_getpass(
            "Enter master password for history (12+ chars): "
        )
        return master_password if master_password else None
