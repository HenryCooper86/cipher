import logging
from collections import Counter
from datetime import datetime
from typing import Any

from pwd_generator.duplicates import (
    SIMILAR_PASSWORD_AUDIT_MAX_ENTRIES,
    find_duplicate_passwords,
    find_similar_passwords,
)

logger = logging.getLogger(__name__)


class PasswordAuditor:
    def __init__(self, generator):
        self.gen = generator

    def find_duplicates(self) -> list[tuple[str, list[int]]]:
        """Find exact duplicate passwords in history (delegates to ``duplicates`` module)."""
        return find_duplicate_passwords(self.gen.history)

    def find_similar_password_pairs(self) -> list[tuple[int, int, float]]:
        """Find distinct index pairs with high string similarity (not exact duplicates)."""
        return find_similar_passwords(self.gen.history)

    def similar_password_audit_skipped(self) -> bool:
        return len(self.gen.history) > SIMILAR_PASSWORD_AUDIT_MAX_ENTRIES

    def find_weak_passwords(self, min_entropy: float = 60.0) -> list[tuple[int, dict]]:
        """Find weak passwords in history."""
        weak = []

        for i, entry in enumerate(self.gen.history):
            entropy = entry.get("metadata", {}).get("entropy", 0)
            if entropy < min_entropy:
                weak.append((i, entry))

        return weak

    def find_expired_passwords(self) -> list[tuple[int, dict]]:
        """Find expired passwords."""
        expired = []
        expiration_days = self.gen.policy.get("expiration_days", 90)

        for i, entry in enumerate(self.gen.history):
            try:
                created_at = datetime.fromisoformat(entry["metadata"]["created_at"])
                age = datetime.now() - created_at

                if age.days > expiration_days:
                    expired.append((i, entry))
            except (KeyError, ValueError):
                continue

        return expired

    def calculate_security_score(
        self,
        *,
        duplicate_count: int | None = None,
        similar_pair_count: int | None = None,
        weak_count: int | None = None,
        expired_count: int | None = None,
    ) -> dict[str, Any]:
        """Calculate overall security score. Pass counts to avoid recomputing scans."""
        if not self.gen.history:
            return {
                "score": 0,
                "max_score": 100,
                "percentage": 0,
                "details": {},
            }

        total = len(self.gen.history)
        wc = weak_count if weak_count is not None else len(self.find_weak_passwords())
        dc = duplicate_count if duplicate_count is not None else len(self.find_duplicates())
        sc = (
            similar_pair_count
            if similar_pair_count is not None
            else len(self.find_similar_password_pairs())
        )
        ec = expired_count if expired_count is not None else len(self.find_expired_passwords())

        strength_scores = {"Weak": 0, "Fair": 1, "Good": 2, "Strong": 3, "Very Strong": 4}
        avg_strength = sum(
            strength_scores.get(e.get("metadata", {}).get("strength", "Weak"), 0)
            for e in self.gen.history
        ) / total if total > 0 else 0

        score = 100.0
        score -= (wc / total * 30) if total > 0 else 0
        score -= (dc / total * 20) if total > 0 else 0
        score -= sc / max(total, 1) * 12
        score -= (ec / total * 15) if total > 0 else 0
        score += avg_strength / 4 * 10

        score = max(0, min(100, score))

        return {
            "score": round(score, 1),
            "max_score": 100,
            "percentage": round(score, 1),
            "details": {
                "total_passwords": total,
                "weak_passwords": wc,
                "duplicate_passwords": dc,
                "similar_pairs": sc,
                "similar_audit_skipped": self.similar_password_audit_skipped(),
                "expired_passwords": ec,
                "average_strength": avg_strength,
            },
        }

    def generate_audit_report(self) -> dict[str, Any]:
        """Generate comprehensive audit report."""
        duplicates = self.find_duplicates()
        similar_raw = self.find_similar_password_pairs()
        weak = self.find_weak_passwords()
        expired = self.find_expired_passwords()
        security_score = self.calculate_security_score(
            duplicate_count=len(duplicates),
            similar_pair_count=len(similar_raw),
            weak_count=len(weak),
            expired_count=len(expired),
        )

        strength_distribution = Counter(
            e.get("metadata", {}).get("strength", "Unknown") for e in self.gen.history
        )

        similar_entries = []
        for i, j, ratio in similar_raw:
            ea = self.gen.history[i]
            eb = self.gen.history[j]
            similar_entries.append(
                {
                    "index_a": i,
                    "index_b": j,
                    "similarity": round(ratio, 4),
                    "service_a": ea.get("metadata", {}).get("service", ""),
                    "service_b": eb.get("metadata", {}).get("service", ""),
                }
            )

        return {
            "generated_at": datetime.now().isoformat(),
            "security_score": security_score,
            "summary": {
                "total_passwords": len(self.gen.history),
                "duplicate_count": len(duplicates),
                "similar_pair_count": len(similar_raw),
                "similar_audit_skipped": self.similar_password_audit_skipped(),
                "weak_count": len(weak),
                "expired_count": len(expired),
            },
            "duplicates": [
                {
                    "password": "***",
                    "length": len(pwd),
                    "count": len(indices),
                    "indices": indices,
                }
                for pwd, indices in duplicates
            ],
            "similar_passwords": similar_entries,
            "weak_passwords": [
                {
                    "index": idx,
                    "service": entry.get("metadata", {}).get("service", ""),
                    "entropy": entry.get("metadata", {}).get("entropy", 0),
                }
                for idx, entry in weak
            ],
            "expired_passwords": [
                {
                    "index": idx,
                    "service": entry.get("metadata", {}).get("service", ""),
                    "created_at": entry.get("metadata", {}).get("created_at", ""),
                }
                for idx, entry in expired
            ],
            "strength_distribution": dict(strength_distribution),
        }


def format_audit_console_report(report: dict[str, Any], *, detail_limit: int = 10) -> str:
    """Human-readable audit body (shared by CLI and interactive menu)."""
    lines: list[str] = []
    lines.append(f"\n{'=' * 70}")
    lines.append("                    PASSWORD SECURITY AUDIT")
    lines.append(f"{'=' * 70}")
    lines.append(f"\nGenerated: {report['generated_at']}")

    score = report["security_score"]
    det = score["details"]
    lines.append(f"\nSecurity Score: {score['score']:.1f}/100")
    lines.append(f"  • Total Passwords: {det['total_passwords']}")
    lines.append(f"  • Weak Passwords: {det['weak_passwords']}")
    lines.append(f"  • Duplicate Passwords: {det['duplicate_passwords']}")
    lines.append(f"  • Similar Pairs: {det.get('similar_pairs', 0)}")
    if det.get("similar_audit_skipped"):
        lines.append(
            f"    (similar-pair scan skipped; vault larger than "
            f"{SIMILAR_PASSWORD_AUDIT_MAX_ENTRIES} entries)"
        )
    lines.append(f"  • Expired Passwords: {det['expired_passwords']}")

    if report["duplicates"]:
        lines.append(f"\n[WARNING]  Duplicate Passwords ({len(report['duplicates'])}):")
        for dup in report["duplicates"][:detail_limit]:
            length_info = f", length {dup['length']}" if "length" in dup else ""
            lines.append(
                f"   • {dup['password']} (used {dup['count']} times{length_info})"
            )

    sim = report.get("similar_passwords") or []
    if sim:
        lines.append(f"\n[WARNING]  Similar Passwords ({len(sim)} pairs, threshold 0.8):")
        for row in sim[:detail_limit]:
            lines.append(
                f"   • #{row['index_a']} {row['service_a']!r} ↔ "
                f"#{row['index_b']} {row['service_b']!r} "
                f"({row['similarity']:.0%})"
            )

    if report["weak_passwords"]:
        lines.append(f"\n[WARNING]  Weak Passwords ({len(report['weak_passwords'])}):")
        for weak in report["weak_passwords"][:detail_limit]:
            lines.append(f"   • {weak['service']}: {weak['entropy']:.1f} bits")

    if report["expired_passwords"]:
        lines.append(
            f"\n[WARNING]  Expired Passwords ({len(report['expired_passwords'])}):"
        )
        for exp in report["expired_passwords"][:detail_limit]:
            lines.append(f"   • {exp['service']}: {exp['created_at'][:10]}")

    lines.append(f"\n{'=' * 70}\n")
    return "\n".join(lines)
