import json
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def export_passwords_json(
    passwords: List[str], filename: str, metadata: Optional[List[Dict]] = None
) -> bool:
    try:
        data = {
            "exported_at": datetime.now().isoformat(),
            "count": len(passwords),
            "passwords": [],
        }

        for i, pwd in enumerate(passwords):
            entry = {"index": i + 1, "password": pwd}
            if metadata and i < len(metadata):
                entry.update(metadata[i])
            data["passwords"].append(entry)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(passwords)} passwords to JSON: {filename}")
        return True
    except (IOError, OSError) as e:
        logger.error(f"File I/O error during JSON export: {e}")
        return False
    except (TypeError, ValueError) as e:
        logger.error(f"Data formatting error during JSON export: {e}")
        return False


def export_passwords_csv(
    passwords: List[str], filename: str, metadata: Optional[List[Dict]] = None
) -> bool:
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Index",
                    "Password",
                    "Service",
                    "Notes",
                    "Created",
                    "Strength",
                    "Entropy",
                ]
            )

            for i, pwd in enumerate(passwords):
                row = [i + 1, pwd]
                if metadata and i < len(metadata):
                    meta = metadata[i].get("metadata", {})
                    row.extend(
                        [
                            meta.get("service", ""),
                            meta.get("notes", ""),
                            meta.get("created_at", ""),
                            meta.get("strength", ""),
                            meta.get("entropy", ""),
                        ]
                    )
                else:
                    row.extend(["", "", "", "", ""])
                writer.writerow(row)

        logger.info(f"Exported {len(passwords)} passwords to CSV: {filename}")
        return True
    except (IOError, OSError) as e:
        logger.error(f"File I/O error during CSV export: {e}")
        return False
    except (TypeError, ValueError, csv.Error) as e:
        logger.error(f"Data formatting error during CSV export: {e}")
        return False


def export_history_json(
    history: List[Dict], filename: str, include_passwords: bool = True
) -> bool:
    try:
        data = {
            "exported_at": datetime.now().isoformat(),
            "count": len(history),
            "entries": [],
        }

        for entry in history:
            export_entry = {"metadata": entry.get("metadata", {}).copy()}
            if include_passwords:
                export_entry["password"] = entry.get("password", "")
            else:
                export_entry["password"] = "***REDACTED***"
            data["entries"].append(export_entry)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(history)} history entries to JSON: {filename}")
        return True
    except (IOError, OSError) as e:
        logger.error(f"File I/O error during history JSON export: {e}")
        return False
    except (TypeError, ValueError) as e:
        logger.error(f"Data formatting error during history JSON export: {e}")
        return False


def export_history_csv(
    history: List[Dict], filename: str, include_passwords: bool = True
) -> bool:
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["Service", "Password", "Created", "Strength", "Entropy", "Notes"]
            )

            for entry in history:
                meta = entry.get("metadata", {})
                password = (
                    entry.get("password", "") if include_passwords else "***REDACTED***"
                )
                writer.writerow(
                    [
                        meta.get("service", ""),
                        password,
                        meta.get("created_at", ""),
                        meta.get("strength", ""),
                        meta.get("entropy", ""),
                        meta.get("notes", ""),
                    ]
                )

        logger.info(f"Exported {len(history)} history entries to CSV: {filename}")
        return True
    except (IOError, OSError) as e:
        logger.error(f"File I/O error during history CSV export: {e}")
        return False
    except (TypeError, ValueError, csv.Error) as e:
        logger.error(f"Data formatting error during history CSV export: {e}")
        return False
