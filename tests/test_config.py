import pytest
import json
import os
from pathlib import Path
from pwd_generator.config import load_config, save_config, create_default_config
from pwd_generator.constants import DEFAULT_POLICY


def test_load_config_default(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))
    config = load_config()
    assert config["policy"] == DEFAULT_POLICY


def test_save_and_load_json_config(temp_dir):
    config_file = temp_dir / "test_config.json"
    custom_config = {"policy": {"min_length": 32, "max_length": 256}}

    assert save_config(custom_config, str(config_file))
    assert config_file.exists()

    loaded = load_config(str(config_file))
    assert loaded["policy"]["min_length"] == 32
    assert loaded["policy"]["max_length"] == 256
    assert loaded["policy"]["min_entropy"] == DEFAULT_POLICY["min_entropy"]


def test_save_and_load_yaml_config(temp_dir):
    try:
        import yaml
    except ImportError:
        pytest.skip("PyYAML not installed")

    config_file = temp_dir / "test_config.yaml"
    custom_config = {"policy": {"min_length": 24}}

    assert save_config(custom_config, str(config_file))
    assert config_file.exists()

    loaded = load_config(str(config_file))
    assert loaded["policy"]["min_length"] == 24


def test_create_default_config(temp_dir):
    config_file = temp_dir / "default_config.json"
    assert create_default_config(str(config_file))
    assert config_file.exists()

    config = load_config(str(config_file))
    assert "policy" in config
    assert "history" in config
    assert "export" in config


def test_load_config_invalid_json(temp_dir):
    config_file = temp_dir / "invalid.json"
    config_file.write_text("{ invalid json }")

    config = load_config(str(config_file))
    assert config["policy"] == DEFAULT_POLICY


def test_load_config_non_dict(temp_dir):
    config_file = temp_dir / "list.json"
    config_file.write_text("[1, 2, 3]")

    config = load_config(str(config_file))
    assert config["policy"] == DEFAULT_POLICY
