"""Vault duplicate and near-duplicate password detection (single source for audit)."""

from __future__ import annotations

import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# O(n²) similar-pair scan; skip above this to keep audits responsive on huge vaults.
SIMILAR_PASSWORD_AUDIT_MAX_ENTRIES = 400


def find_duplicate_passwords(history: list[dict]) -> list[tuple[str, list[int]]]:
    """Find duplicate passwords in history."""
    password_indices = {}

    for i, entry in enumerate(history):
        pwd = entry.get('password', '')
        if pwd:
            if pwd not in password_indices:
                password_indices[pwd] = []
            password_indices[pwd].append(i)

    duplicates = [(pwd, indices) for pwd, indices in password_indices.items() if len(indices) > 1]
    return duplicates


def find_similar_passwords(
    history: list[dict],
    threshold: float = 0.8,
    *,
    max_entries: int = SIMILAR_PASSWORD_AUDIT_MAX_ENTRIES,
) -> list[tuple[int, int, float]]:
    """Return (index_i, index_j, similarity) for pairs with ratio >= threshold (SequenceMatcher).

    Returns an empty list when ``len(history) > max_entries`` to avoid quadratic cost on large vaults.
    """
    if len(history) > max_entries:
        logger.debug(
            "Skipping similar-password scan: history length %s > max %s",
            len(history),
            max_entries,
        )
        return []

    similar: list[tuple[int, int, float]] = []

    for i in range(len(history)):
        pwd1 = history[i].get("password", "")
        if not pwd1:
            continue

        for j in range(i + 1, len(history)):
            pwd2 = history[j].get("password", "")
            if not pwd2:
                continue

            ratio = SequenceMatcher(None, pwd1, pwd2).ratio()
            if ratio >= threshold:
                similar.append((i, j, ratio))

    return similar
