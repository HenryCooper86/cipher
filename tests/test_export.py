import pytest
import json
import csv
from pwd_generator.export import (
    export_passwords_json,
    export_passwords_csv,
    export_history_json,
    export_history_csv,
)


def test_export_passwords_json(temp_dir):
    passwords = ["pass1", "pass2"]
    filename = temp_dir / "passwords.json"

    assert export_passwords_json(passwords, str(filename))

    with open(filename, "r") as f:
        data = json.load(f)
        assert data["count"] == 2
        assert len(data["passwords"]) == 2
        assert data["passwords"][0]["password"] == "pass1"


def test_export_passwords_csv(temp_dir):
    passwords = ["pass1", "pass2"]
    filename = temp_dir / "passwords.csv"

    assert export_passwords_csv(passwords, str(filename))

    with open(filename, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["Password"] == "pass1"


def test_export_history_json(temp_dir):
    history = [
        {"password": "p1", "metadata": {"service": "s1", "created_at": "now"}},
        {"password": "p2", "metadata": {"service": "s2"}},
    ]
    filename = temp_dir / "history.json"

    # Test with password inclusion
    assert export_history_json(history, str(filename), include_passwords=True)

    with open(filename, "r") as f:
        data = json.load(f)
        assert len(data["entries"]) == 2
        assert data["entries"][0]["password"] == "p1"

    # Test redacted
    assert export_history_json(history, str(filename), include_passwords=False)
    with open(filename, "r") as f:
        data = json.load(f)
        assert data["entries"][0]["password"] == "***REDACTED***"


def test_export_history_csv(temp_dir):
    history = [{"password": "p1", "metadata": {"service": "s1", "created_at": "now"}}]
    filename = temp_dir / "history.csv"

    assert export_history_csv(history, str(filename), include_passwords=True)

    with open(filename, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["Password"] == "p1"
        assert rows[0]["Service"] == "s1"


def test_export_errors(temp_dir):
    # Test invalid path
    assert not export_passwords_json([], "/invalid/path.json")
    assert not export_passwords_csv([], "/invalid/path.csv")
    assert not export_history_json([], "/invalid/path.json")
    assert not export_history_csv([], "/invalid/path.csv")
