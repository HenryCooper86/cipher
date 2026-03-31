import pytest
import os
import secrets
from pwd_generator.encryption import EncryptionManager, clear_memory
from pwd_generator.validation import PasswordValidator
from pwd_generator.exceptions import EncryptionError, ValidationError, HistoryError


@pytest.fixture
def encryption_manager(temp_dir):
    history_file = temp_dir / "test_history.enc"
    return EncryptionManager(str(history_file))


@pytest.fixture
def validator():
    return PasswordValidator()


def test_validate_master_password_too_short(encryption_manager, validator):
    with pytest.raises(ValidationError):
        encryption_manager.validate_master_password(
            "Short1!", validator.calculate_entropy
        )


def test_validate_master_password_low_entropy(encryption_manager, validator):
    with pytest.raises(ValidationError):
        encryption_manager.validate_master_password(
            "123456789012", validator.calculate_entropy
        )


def test_init_encryption_system(encryption_manager):
    master_password = "TestMasterPassword123!"
    encryption_manager.init_encryption_system(master_password)
    assert encryption_manager.cipher is not None
    assert encryption_manager.salt is not None


def test_init_encryption_system_with_salt(encryption_manager):
    master_password = "TestMasterPassword123!"
    salt = secrets.token_bytes(16)
    encryption_manager.init_encryption_system(master_password, salt)
    assert encryption_manager.salt == salt


def test_save_and_load_history(encryption_manager, master_password):
    test_history = [
        {
            "password": "TestPassword123!",
            "metadata": {
                "created_at": "2024-01-01T00:00:00",
                "service": "test",
                "notes": "test notes",
                "hash": "abc123",
                "strength": "Strong",
                "entropy": 80.0,
            },
        }
    ]

    encryption_manager.init_encryption_system(master_password)
    encryption_manager.save_history(test_history)

    loaded_history = encryption_manager.load_history(master_password)
    assert len(loaded_history) == 1
    assert loaded_history[0]["metadata"]["service"] == "test"


def test_load_history_file_not_exists(encryption_manager, master_password):
    encryption_manager.init_encryption_system(master_password)
    history = encryption_manager.load_history(master_password)
    assert history == []


def test_load_history_wrong_password(encryption_manager, master_password):
    test_history = [{"password": "test", "metadata": {}}]

    encryption_manager.init_encryption_system(master_password)
    encryption_manager.save_history(test_history)

    with pytest.raises(EncryptionError):
        encryption_manager.load_history("WrongPassword123!")


def test_save_history_no_cipher(encryption_manager):
    test_history = [{"password": "test", "metadata": {}}]
    with pytest.raises(HistoryError):
        encryption_manager.save_history(test_history)
    assert not os.path.exists(encryption_manager.history_file)


def test_load_history_legacy_pbkdf2(temp_dir, master_password):
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.fernet import Fernet
    import base64
    import json
    import secrets

    history_file = temp_dir / "legacy_history.enc"
    salt = secrets.token_bytes(16)
    while salt[0] in [0, 1]:
        salt = secrets.token_bytes(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
    cipher = Fernet(key)

    data = {"history": [{"password": "legacy_pwd", "metadata": {"service": "legacy"}}]}
    payload = json.dumps(data).encode()
    ciphertext = cipher.encrypt(payload)

    with open(history_file, "wb") as f:
        f.write(salt + ciphertext)

    manager = EncryptionManager(str(history_file))
    loaded_history = manager.load_history(master_password)

    assert len(loaded_history) == 1
    assert loaded_history[0]["password"] == "legacy_pwd"


def test_argon2_fallback_to_pbkdf2(temp_dir, master_password, monkeypatch):
    import pwd_generator.encryption

    monkeypatch.setattr(pwd_generator.encryption, "ARGON2_AVAILABLE", False)

    history_file = temp_dir / "fallback_history.enc"
    manager = EncryptionManager(str(history_file))

    manager.init_encryption_system(master_password)
    manager.save_history([{"password": "p", "metadata": {}}])

    with open(history_file, "rb") as f:
        content = f.read()
        assert content[0] == 0
