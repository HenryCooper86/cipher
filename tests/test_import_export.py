import csv
import json

import pytest
from pwd_generator.import_export import (
    export_to_1password_csv,
    export_to_bitwarden_csv,
    export_to_lastpass_csv,
    import_from_csv,
    import_from_json,
)


def test_import_from_json(temp_dir):
    test_data = [
        {
            "password": "test123",
            "metadata": {"service": "test_service", "notes": "test notes"},
        }
    ]
    json_file = temp_dir / "test.json"
    json_file.write_text(json.dumps(test_data))

    entries = import_from_json(str(json_file))
    assert len(entries) == 1
    assert entries[0]["password"] == "test123"
    assert entries[0]["metadata"]["service"] == "test_service"


def test_import_from_csv_generic(temp_dir):
    csv_file = temp_dir / "test.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["password", "service", "notes"])
        writer.writerow(["test123", "test_service", "test notes"])

    entries = import_from_csv(str(csv_file), "generic")
    assert len(entries) == 1
    assert entries[0]["password"] == "test123"


def test_import_from_csv_1password(temp_dir):
    csv_file = temp_dir / "test.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Password", "Notes"])
        writer.writerow(["test_service", "test123", "test notes"])

    entries = import_from_csv(str(csv_file), "1password")
    assert len(entries) == 1
    assert entries[0]["password"] == "test123"
    assert entries[0]["metadata"]["service"] == "test_service"


def test_export_to_1password_csv(temp_dir):
    history = [
        {
            "password": "test123",
            "metadata": {"service": "test_service", "notes": "test notes"},
        }
    ]
    csv_file = temp_dir / "export.csv"
    assert export_to_1password_csv(history, str(csv_file))
    assert csv_file.exists()

    with open(csv_file) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["Password"] == "test123"


def test_export_to_lastpass_csv(temp_dir):
    history = [{"password": "test", "metadata": {"service": "s"}}]
    csv_file = temp_dir / "export.csv"
    assert export_to_lastpass_csv(history, str(csv_file))
    assert csv_file.exists()


def test_export_to_bitwarden_csv(temp_dir):
    history = [{"password": "test", "metadata": {"service": "s"}}]
    csv_file = temp_dir / "export.csv"
    assert export_to_bitwarden_csv(history, str(csv_file))
    assert csv_file.exists()


def test_import_from_json_malformed(temp_dir):
    json_file = temp_dir / "malformed.json"
    json_file.write_text("{ not a json }")
    with pytest.raises(Exception):
        import_from_json(str(json_file))


def test_import_from_csv_empty(temp_dir):
    csv_file = temp_dir / "empty.csv"
    csv_file.write_text("")
    entries = import_from_csv(str(csv_file))
    assert len(entries) == 0
