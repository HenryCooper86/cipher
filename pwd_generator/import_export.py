import csv
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from pwd_generator.exceptions import FileOperationError, ValidationError

logger = logging.getLogger(__name__)


def import_from_csv(
    filename: str, format_type: str = "generic"
) -> List[Dict[str, Any]]:
    """
    Import passwords from CSV file.

    Supported formats:
    - generic: Generic CSV (password, service, notes)
    - 1password: 1Password CSV format
    - lastpass: LastPass CSV format
    - bitwarden: Bitwarden CSV format
    """
    entries = []

    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                entry = {
                    "password": "",
                    "metadata": {
                        "service": "",
                        "notes": "",
                        "created_at": datetime.now().isoformat(),
                        "imported": True,
                    },
                }

                if format_type == "1password":
                    entry["password"] = row.get("Password", "")
                    entry["metadata"]["service"] = row.get("Title", "")
                    entry["metadata"]["notes"] = row.get("Notes", "")
                elif format_type == "lastpass":
                    entry["password"] = row.get("Password", "")
                    entry["metadata"]["service"] = row.get("Name", "")
                    entry["metadata"]["notes"] = row.get("Extra", "")
                elif format_type == "bitwarden":
                    entry["password"] = row.get("password", "")
                    entry["metadata"]["service"] = row.get("name", "")
                    entry["metadata"]["notes"] = row.get("notes", "")
                else:
                    entry["password"] = row.get("password", row.get("Password", ""))
                    entry["metadata"]["service"] = row.get(
                        "service", row.get("Service", row.get("name", ""))
                    )
                    entry["metadata"]["notes"] = row.get("notes", row.get("Notes", ""))

                if entry["password"]:
                    entries.append(entry)

        logger.info(f"Imported {len(entries)} entries from {filename}")
        return entries
    except FileNotFoundError as e:
        logger.error(f"CSV file not found: {filename}")
        raise FileOperationError(f"Import file not found: {filename}", details={"path": filename})
    except PermissionError as e:
        logger.error(f"Permission denied reading CSV file: {filename}")
        raise FileOperationError(f"Permission denied reading file: {filename}", details={"path": filename})
    except (IOError, OSError) as e:
        logger.error(f"File I/O error during CSV import: {e}")
        raise FileOperationError(f"Failed to read CSV file: {e}", details={"path": filename, "error": str(e)})
    except csv.Error as e:
        logger.error(f"CSV parsing error: {e}")
        raise ValidationError(f"Invalid CSV format: {e}", details={"path": filename, "error": str(e)})


def import_from_json(filename: str) -> List[Dict[str, Any]]:
    """Import passwords from JSON file."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        entries = []
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            if "passwords" in data:
                entries = data["passwords"]
            elif "entries" in data:
                entries = data["entries"]
            elif "history" in data:
                entries = data["history"]

        for entry in entries:
            if "metadata" not in entry:
                entry["metadata"] = {
                    "created_at": datetime.now().isoformat(),
                    "imported": True,
                }
            elif "created_at" not in entry["metadata"]:
                entry["metadata"]["created_at"] = datetime.now().isoformat()
            entry["metadata"]["imported"] = True

        logger.info(f"Imported {len(entries)} entries from {filename}")
        return entries
    except FileNotFoundError as e:
        logger.error(f"JSON file not found: {filename}")
        raise FileOperationError(f"Import file not found: {filename}", details={"path": filename})
    except PermissionError as e:
        logger.error(f"Permission denied reading JSON file: {filename}")
        raise FileOperationError(f"Permission denied reading file: {filename}", details={"path": filename})
    except (IOError, OSError) as e:
        logger.error(f"File I/O error during JSON import: {e}")
        raise FileOperationError(f"Failed to read JSON file: {e}", details={"path": filename, "error": str(e)})
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        raise ValidationError(f"Invalid JSON format: {e}", details={"path": filename, "error": str(e)})


def export_to_1password_csv(history: List[Dict], filename: str) -> bool:
    """Export to 1Password CSV format."""
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Password", "Notes"])

            for entry in history:
                meta = entry.get("metadata", {})
                writer.writerow(
                    [
                        meta.get("service", ""),
                        entry.get("password", ""),
                        meta.get("notes", ""),
                    ]
                )

        logger.info(f"Exported to 1Password format: {filename}")
        return True
    except (IOError, OSError) as e:
        logger.error(f"File I/O error during 1Password export: {e}")
        return False
    except csv.Error as e:
        logger.error(f"CSV error during 1Password export: {e}")
        return False


def export_to_lastpass_csv(history: List[Dict], filename: str) -> bool:
    """Export to LastPass CSV format."""
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["url", "username", "password", "extra", "name", "grouping", "fav"]
            )

            for entry in history:
                meta = entry.get("metadata", {})
                writer.writerow(
                    [
                        "",  # url
                        "",  # username
                        entry.get("password", ""),
                        meta.get("notes", ""),  # extra
                        meta.get("service", ""),  # name
                        "",  # grouping
                        "0",  # fav
                    ]
                )

        logger.info(f"Exported to LastPass format: {filename}")
        return True
    except (IOError, OSError) as e:
        logger.error(f"File I/O error during LastPass export: {e}")
        return False
    except csv.Error as e:
        logger.error(f"CSV error during LastPass export: {e}")
        return False


def export_to_bitwarden_csv(history: List[Dict], filename: str) -> bool:
    """Export to Bitwarden CSV format."""
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "name",
                    "notes",
                    "login_uri",
                    "login_username",
                    "login_password",
                    "login_totp",
                ]
            )

            for entry in history:
                meta = entry.get("metadata", {})
                writer.writerow(
                    [
                        meta.get("service", ""),
                        meta.get("notes", ""),
                        "",  # login_uri
                        "",  # login_username
                        entry.get("password", ""),
                        "",  # login_totp
                    ]
                )

        logger.info(f"Exported to Bitwarden format: {filename}")
        return True
    except (IOError, OSError) as e:
        logger.error(f"File I/O error during Bitwarden export: {e}")
        return False
    except csv.Error as e:
        logger.error(f"CSV error during Bitwarden export: {e}")
        return False
