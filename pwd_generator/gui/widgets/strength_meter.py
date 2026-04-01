"""
Password Strength Meter Widget

Visual indicator for password strength with color-coded progress bar.
"""

from __future__ import annotations

from pwd_generator.gui import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    Qt,
    QVBoxLayout,
    QWidget,
)
from pwd_generator.gui.widgets.theme import theme_manager


class StrengthMeter(QWidget):
    """
    Visual password strength indicator.

    Shows:
    - Strength label (Weak/Fair/Good/Strong/Very Strong)
    - Progress bar with color-coded fill
    - Entropy value in bits
    """

    STRENGTH_LEVELS = {
        "Weak": {"threshold": 40, "color_key": "strength_weak"},
        "Fair": {"threshold": 60, "color_key": "strength_fair"},
        "Good": {"threshold": 80, "color_key": "strength_good"},
        "Strong": {"threshold": 100, "color_key": "strength_strong"},
        "Very Strong": {"threshold": 150, "color_key": "strength_very_strong"},
    }

    STRENGTH_ORDER = ["Weak", "Fair", "Good", "Strong", "Very Strong"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_strength = "Weak"
        self._current_entropy = 0.0
        self._last_stats: dict | None = None
        self._meter_cleared = True
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header with label and entropy
        header_layout = QHBoxLayout()

        self.strength_label = QLabel("Password Strength: -")
        self.strength_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.strength_label)

        header_layout.addStretch()

        self.entropy_label = QLabel("Entropy: 0.0 bits")
        self.entropy_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')};")
        header_layout.addWidget(self.entropy_label)

        layout.addLayout(header_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)

        # Character stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.stats_labels = {}
        for stat_name in ["Length", "Upper", "Lower", "Digits", "Special"]:
            stat_label = QLabel(f"{stat_name}: -")
            stat_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')}; font-size: 11px;")
            stats_layout.addWidget(stat_label)
            self.stats_labels[stat_name.lower()] = stat_label

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

    def set_strength(self, strength: str, entropy: float, stats: dict = None):
        """
        Update the strength display.

        Args:
            strength: Strength level string (Weak/Fair/Good/Strong/Very Strong)
            entropy: Entropy value in bits
            stats: Optional dict with character stats
        """
        self._meter_cleared = False
        self._last_stats = stats
        self._current_strength = strength
        self._current_entropy = entropy

        # Update labels
        self.strength_label.setText(f"Password Strength: {strength}")
        self.entropy_label.setText(f"Entropy: {entropy:.1f} bits")

        # Calculate progress value (0-100)
        progress = min(100, int(entropy * 0.8))  # Scale entropy to progress
        self.progress_bar.setValue(progress)

        # Get color for current strength
        color = self._get_strength_color(strength)

        # Update progress bar style
        self.progress_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)

        # Update strength label color
        self.strength_label.setStyleSheet(f"font-weight: bold; color: {color};")

        # Update stats if provided
        if stats:
            self._update_stats(stats)

    def _get_strength_color(self, strength: str) -> str:
        """Get the color for a given strength level."""
        if strength in self.STRENGTH_LEVELS:
            color_key = self.STRENGTH_LEVELS[strength]["color_key"]
            return theme_manager.get_color(color_key)
        return theme_manager.get_color("strength_weak")

    def _update_stats(self, stats: dict):
        """Update the character statistics display."""
        if "length" in stats:
            self.stats_labels["length"].setText(f"Length: {stats['length']}")

        # Map stat keys to label keys
        stat_mapping = {
            "uppercase": "upper",
            "lowercase": "lower",
            "digits": "digits",
            "special": "special"
        }

        for stat_name, label_key in stat_mapping.items():
            key = f"has_{stat_name}"
            if key in stats:
                has_stat = stats[key]
                label = self.stats_labels[label_key]
                check = "Yes" if has_stat else "No"
                color = theme_manager.get_color("accent_success") if has_stat else theme_manager.get_color("text_secondary")
                label.setText(f"{label_key.capitalize()}: {check}")
                label.setStyleSheet(f"color: {color}; font-size: 11px;")

    def refresh_from_theme(self) -> None:
        """Reapply colors after global theme change."""
        if self._meter_cleared:
            self.entropy_label.setStyleSheet(
                f"color: {theme_manager.get_color('text_secondary')};"
            )
            for label in self.stats_labels.values():
                label.setStyleSheet(
                    f"color: {theme_manager.get_color('text_secondary')}; font-size: 11px;"
                )
            self.progress_bar.setStyleSheet("")
            self.strength_label.setStyleSheet("font-weight: bold;")
            return
        self.set_strength(
            self._current_strength, self._current_entropy, self._last_stats
        )

    def clear(self):
        """Reset the strength meter."""
        self._meter_cleared = True
        self._last_stats = None
        self.strength_label.setText("Password Strength: -")
        self.strength_label.setStyleSheet("font-weight: bold;")
        self.entropy_label.setText("Entropy: 0.0 bits")
        self.entropy_label.setStyleSheet(
            f"color: {theme_manager.get_color('text_secondary')};"
        )
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("")

        for stat_name, label in self.stats_labels.items():
            label.setText(f"{stat_name.capitalize()}: -")
            label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')}; font-size: 11px;")


class StrengthIndicator(QWidget):
    """
    Compact strength indicator for use in tables and lists.

    Shows a small colored badge with the strength level.
    """

    def __init__(self, strength: str = "", parent=None):
        super().__init__(parent)
        self._setup_ui(strength)

    def _setup_ui(self, strength: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        self.label = QLabel(strength or "-")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        if strength:
            self._apply_strength_style(strength)

    def set_strength(self, strength: str):
        """Set the strength level."""
        self.label.setText(strength)
        self._apply_strength_style(strength)

    def _apply_strength_style(self, strength: str):
        """Apply styling based on strength level."""
        color = self._get_strength_color(strength)
        self.setStyleSheet(f"""
            background-color: {color};
            border-radius: 4px;
        """)
        badge = theme_manager.get_color("strength_badge_text")
        self.label.setStyleSheet(
            f"color: {badge}; font-size: 11px; font-weight: bold;"
        )

    def _get_strength_color(self, strength: str) -> str:
        """Get the color for a given strength level."""
        colors = {
            "Weak": theme_manager.get_color("strength_weak"),
            "Fair": theme_manager.get_color("strength_fair"),
            "Good": theme_manager.get_color("strength_good"),
            "Strong": theme_manager.get_color("strength_strong"),
            "Very Strong": theme_manager.get_color("strength_very_strong"),
        }
        return colors.get(strength, theme_manager.get_color("text_secondary"))
