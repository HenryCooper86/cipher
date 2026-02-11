import pytest
import os
from pathlib import Path
from pwd_generator.validators import validate_file_path
from pwd_generator.encryption import EncryptionManager, clear_memory


def test_path_traversal_prevention(temp_dir):
    with pytest.raises(ValueError, match="outside allowed directory"):
        validate_file_path("../../../etc/passwd", base_dir=temp_dir)

    with pytest.raises(ValueError, match="outside allowed directory"):
        validate_file_path("/etc/passwd", base_dir=temp_dir)

    valid_path = validate_file_path("test.txt", base_dir=temp_dir)
    assert valid_path == (temp_dir / "test.txt").resolve()


def test_memory_clearing():
    data = bytearray(b"sensitive")
    clear_memory(data)
    assert data == bytearray(len(data))


def test_argon2_encryption_cycle(temp_dir):
    history_file = temp_dir / "history.enc"
    manager = EncryptionManager(str(history_file))
    master_password = bytearray(b"super_secret_master_password_123!")

    history = [{"password": "test_pwd", "metadata": {"service": "test"}}]

    manager.init_encryption_system(master_password)
    manager.save_history(history)

    manager2 = EncryptionManager(str(history_file))
    loaded_history = manager2.load_history(master_password)

    assert history == loaded_history

    with open(history_file, "rb") as f:
        content = f.read()
        assert content[0] == 1
