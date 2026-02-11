import pytest
import os
import json
from pwd_generator.profiles import ProfileManager, PasswordProfile


@pytest.fixture
def profile_file(temp_dir):
    return temp_dir / "profiles.json"


def test_profile_creation():
    profile = PasswordProfile("test", {"min_length": 20}, "readable")
    assert profile.name == "test"
    assert profile.policy["min_length"] == 20
    assert profile.template == "readable"


def test_profile_to_dict():
    profile = PasswordProfile("test", {"min_length": 20}, "readable")
    data = profile.to_dict()
    assert data["name"] == "test"
    assert data["policy"]["min_length"] == 20
    assert data["template"] == "readable"


def test_profile_from_dict():
    data = {"name": "test", "policy": {"min_length": 20}, "template": "readable"}
    profile = PasswordProfile.from_dict(data)
    assert profile.name == "test"
    assert profile.policy["min_length"] == 20
    assert profile.template == "readable"


@pytest.fixture
def manager(profile_file):
    return ProfileManager(str(profile_file))


def test_create_default_profiles(manager):
    profiles = manager.list_profiles()
    assert len(profiles) > 0
    assert "banking" in profiles
    assert "social" in profiles


def test_add_profile(manager):
    profile = PasswordProfile("custom", {"min_length": 25}, None)
    assert manager.add_profile(profile)
    assert "custom" in manager.list_profiles()


def test_get_profile(manager):
    profile = manager.get_profile("banking")
    assert profile is not None
    assert profile.name == "banking"


def test_get_nonexistent_profile(manager):
    assert manager.get_profile("nonexistent") is None


def test_delete_profile(manager):
    profile = PasswordProfile("temp", {"min_length": 15}, None)
    manager.add_profile(profile)
    assert "temp" in manager.list_profiles()
    assert manager.delete_profile("temp")
    assert "temp" not in manager.list_profiles()


def test_save_and_load_profiles(profile_file, manager):
    profile = PasswordProfile("test_save", {"min_length": 18}, "url_safe")
    manager.add_profile(profile)

    new_manager = ProfileManager(str(profile_file))
    loaded_profile = new_manager.get_profile("test_save")
    assert loaded_profile is not None
    assert loaded_profile.name == "test_save"
    assert loaded_profile.policy["min_length"] == 18
