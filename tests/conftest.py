import shutil
import tempfile
from pathlib import Path

import pytest
from pwd_generator import SecurePasswordGenerator


@pytest.fixture
def temp_dir():
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture
def master_password():
    return "TestMasterPassword123!"


@pytest.fixture
def gen():
    return SecurePasswordGenerator()


@pytest.fixture
def gen_with_history(temp_dir, master_password):
    history_file = temp_dir / "test_history.enc"
    gen = SecurePasswordGenerator(
        master_password=master_password, history_file=str(history_file)
    )
    return gen
